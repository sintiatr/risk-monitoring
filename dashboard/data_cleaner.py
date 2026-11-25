"""
Pipeline Data Cleaner & ETL: Monitoring Pengendalian Risiko per Inspektorat & SIJ
Sumber Data Tunggal: Google Spreadsheet URL
Lengkap untuk seluruh 24 Kode Risiko (R1 - R24) dan seluruh Kategori PIC:
- Inspektorat I s.d. Inspektorat V
- Sekretariat Inspektorat Jenderal (SIJ) beserta 4 Bagian:
  * SIJ (RK)      : Bagian Rencana dan Keuangan
  * SIJ (PTLHPKI) : Bagian Pemantauan Tindak Lanjut Hasil Pengawasan dan Kepatuhan Internal
  * SIJ (HKO)     : Bagian Hukum dan Komunikasi Publik
  * SIJ (SIJU)    : Bagian Sistem Informasi dan Umum
"""

import os
import io
import sys
import json
import re
import urllib.request
import urllib.error
import openpyxl
import pandas as pd

# =====================================================================
# KONFIGURASI SUMBER DATA TUNGGAL (GOOGLE SPREADSHEET)
# =====================================================================
GOOGLE_SHEET_URL = "https://docs.google.com/spreadsheets/d/1IALIKNQBasKoP_-x88Zhc-McVKSTdyt3/edit?gid=40730807#gid=40730807"
SHEET_NAME = "Monitoring Pengendalian Risiko"

# Kategori Unit Kerja Eselon II Utama
UNIT_ESELON_2 = [
    'Inspektorat I',
    'Inspektorat II',
    'Inspektorat III',
    'Inspektorat IV',
    'Inspektorat V',
    'Sekretariat Inspektorat Jenderal'
]

# Kategori PIC Rinci
SUB_BAGIAN_SIJ = [
    'SIJ (RK)',
    'SIJ (PTLHPKI)',
    'SIJ (HKO)',
    'SIJ (SIJU)'
]

def clean_text(val):
    """Membersihkan spasi ganda, newline fisik, dan karakter error."""
    if val is None:
        return ""
    s = str(val).strip()
    if s == "#REF!" or s.lower() in ("nan", "none"):
        return ""
    s = re.sub(r'[\r\n]+', ' ', s)
    s = re.sub(r'\s+', ' ', s)
    return s.strip()

def normalize_pic_name(raw_name):
    """Menstandarisasi nama PIC dari database."""
    if not raw_name:
        return ""
    clean = re.sub(r'\s+', ' ', str(raw_name)).strip()
    # Handle multi-line SIJ\n(RK) -> SIJ (RK)
    clean = re.sub(r'SIJ\s*\(', 'SIJ (', clean)
    return clean

def extract_spreadsheet_id(url):
    """Mengekstrak ID Spreadsheet dari link Google Sheets."""
    m = re.search(r'/spreadsheets/d/([a-zA-Z0-9_-]{20,})', url or "")
    if not m:
        raise ValueError(f"Link Google Sheets tidak valid: {url}")
    return m.group(1)

def fetch_google_sheet(url):
    """Mengunduh workbook langsung dari Google Sheets via endpoint export xlsx."""
    sheet_id = extract_spreadsheet_id(url)
    export_url = f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=xlsx"
    print(f"[1/4] Mengunduh data dari Google Sheets (ID: {sheet_id}) ...")
    
    req = urllib.request.Request(export_url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            content = resp.read()
    except Exception as e:
        print(f"[ERROR] Gagal mengunduh spreadsheet dari Google: {e}")
        sys.exit(1)

    if not content.startswith(b"PK"):
        raise PermissionError(
            "Spreadsheet tidak dapat diakses. Pastikan hak akses Google Sheets "
            "telah diatur ke 'Anyone with the link' (Viewer)."
        )
    print(f"[SUKSES] Spreadsheet berhasil diunduh ({len(content) / 1024:.1f} KB)")
    return openpyxl.load_workbook(io.BytesIO(content), data_only=True)

def select_target_sheet(wb, target_name):
    """Mencari sheet target secara fleksibel."""
    norm = lambda s: re.sub(r'\s+', ' ', s).strip().lower()
    t = norm(target_name)

    for name in wb.sheetnames:
        if norm(name) == t:
            return wb[name]

    for name in wb.sheetnames:
        if "monitoring pengendalian risiko" in norm(name):
            print(f"[INFO] Menggunakan sheet: '{name}'")
            return wb[name]

    print(f"[ERROR] Sheet '{target_name}' tidak ditemukan! Sheet yang ada: {wb.sheetnames}")
    sys.exit(1)

def process_monitoring_data(wb):
    """
    Ekstraksi lengkap untuk seluruh 24 Risiko (R1 s.d. R24) dan seluruh PIC:
    - Kolom B: Kode Risiko
    - Kolom G: PIC Mitigasi (Inspektorat I-V dan Bagian SIJ)
    - Kolom H: Pengendalian yang Sudah Dilakukan
    - Kolom Q: Efektivitas Pengendalian (dari database)
    """
    ws = select_target_sheet(wb, SHEET_NAME)
    print(f"[2/4] Memproses data dari sheet: '{ws.title}' ...")

    current_no = ""
    current_kode = ""
    current_indikator = ""
    current_uraian = ""
    current_pic = ""

    # Menyimpan data per risiko dan daftar seluruh baris register terperinci
    risks_map = {}
    flat_records = []

    for r in range(5, 165):
        val_no = ws.cell(r, 1).value    # Kolom A: No (R1, R2, ...)
        val_b = ws.cell(r, 2).value     # Kolom B: Kode Risiko
        val_c = ws.cell(r, 3).value     # Kolom C: Indikator Sasaran
        val_d = ws.cell(r, 4).value     # Kolom D: Uraian Risiko
        val_f = ws.cell(r, 6).value     # Kolom F: Rencana Tindak Pengendalian
        val_g = ws.cell(r, 7).value     # Kolom G: PIC Mitigasi
        val_h = ws.cell(r, 8).value     # Kolom H: Pengendalian Yang Sudah Dilakukan
        val_i = ws.cell(r, 9).value     # Kolom I: Link Data Dukung
        val_n = ws.cell(r, 14).value    # Kolom N: Kendala
        val_q = ws.cell(r, 17).value    # Kolom Q: Efektivitas Pengendalian

        # Forward fill data master risiko
        if val_no and str(val_no).strip():
            current_no = str(val_no).strip().upper()
        if val_b and str(val_b).strip():
            current_kode = str(val_b).strip()
        if val_c and str(val_c).strip():
            current_indikator = str(val_c).strip()
        if val_d and str(val_d).strip():
            current_uraian = str(val_d).strip()

        if not current_no:
            continue

        if current_no not in risks_map:
            risks_map[current_no] = {
                "no": current_no,
                "kode_risiko": current_kode,
                "indikator": current_indikator,
                "uraian_risiko": current_uraian,
                "pic_mitigasi": {}  # dictionary of pic_name -> mitigasi detail
            }
        elif current_uraian and not risks_map[current_no]["uraian_risiko"]:
            risks_map[current_no]["uraian_risiko"] = current_uraian

        # Update PIC baris ini jika ada
        if val_g and str(val_g).strip():
            current_pic = normalize_pic_name(val_g)

        if current_pic:
            eselon2 = "Sekretariat Inspektorat Jenderal" if "SIJ" in current_pic else current_pic
            if current_pic not in risks_map[current_no]["pic_mitigasi"]:
                risks_map[current_no]["pic_mitigasi"][current_pic] = {
                    "pic": current_pic,
                    "kategori_eselon2": eselon2,
                    "status": "Belum Dilakukan",
                    "sudah_dilakukan": False,
                    "rencana_tindak_pengendalian": "",
                    "rencana_list": [],
                    "pengendalian_dilakukan": "",
                    "pengendalian_list": [],
                    "link_dukung": "",
                    "kendala": "",
                    "efektivitas": "-"
                }

            target = risks_map[current_no]["pic_mitigasi"][current_pic]
            f_text = clean_text(val_f)
            h_text = clean_text(val_h)
            q_text = clean_text(val_q)
            link_text = clean_text(val_i)
            kendala_text = clean_text(val_n)

            if f_text and f_text not in target["rencana_list"]:
                target["rencana_list"].append(f_text)
                target["rencana_tindak_pengendalian"] = "\n".join([f"• {x}" for x in target["rencana_list"]])

            if h_text:
                target["pengendalian_list"].append(h_text)
                target["sudah_dilakukan"] = True
                target["status"] = "Sudah Dilakukan"
                target["pengendalian_dilakukan"] = "\n".join([f"• {x}" for x in target["pengendalian_list"]])
            if link_text and not target["link_dukung"]:
                target["link_dukung"] = link_text
            if kendala_text and not target["kendala"]:
                target["kendala"] = kendala_text
            if q_text and q_text != "#REF!":
                target["efektivitas"] = q_text

            # Simpan baris register per-row individual (dijabarkan per row rencana/pengendalian)
            if f_text or h_text or val_g:
                row_status = "Sudah Dilakukan" if h_text else "Belum Dilakukan"
                row_efek = q_text if (q_text and q_text not in ["#REF!", "-"]) else "-"
                flat_records.append({
                    "no_risiko": current_no,
                    "kode_risiko": current_kode,
                    "uraian_risiko": current_uraian,
                    "pic_mitigasi": current_pic,
                    "kategori_eselon2": eselon2,
                    "status_pengendalian": row_status,
                    "rencana_tindak_pengendalian": f_text,
                    "pengendalian_yang_sudah_dilakukan": h_text,
                    "efektivitas_pengendalian": row_efek,
                    "link_dukung": link_text,
                    "kendala": kendala_text
                })

    # Urutkan risiko R1 s.d. R24
    sorted_keys = sorted(
        risks_map.keys(),
        key=lambda x: int(re.sub(r'\D', '', x)) if re.sub(r'\D', '', x) else 0
    )

    # -----------------------------------------------------------------
    # PERHITUNGAN STATISTIK CAPAIAN PER PIC & ESELON II
    # -----------------------------------------------------------------
    # Statistik per PIC spesifik (Inspektorat I-V, SIJ RK, PTLHPKI, HKO, SIJU)
    all_pics_found = set()
    for r in risks_map.values():
        all_pics_found.update(r["pic_mitigasi"].keys())

    # Urutkan daftar PIC
    ordered_pics = [
        'Inspektorat I',
        'Inspektorat II',
        'Inspektorat III',
        'Inspektorat IV',
        'Inspektorat V',
        'SIJ (RK)',
        'SIJ (PTLHPKI)',
        'SIJ (HKO)',
        'SIJ (SIJU)'
    ]
    for p in sorted(all_pics_found):
        if p not in ordered_pics:
            ordered_pics.append(p)

    summary_per_pic = {}
    for p in ordered_pics:
        summary_per_pic[p] = {
            "pic": p,
            "eselon2": "Sekretariat Inspektorat Jenderal" if "SIJ" in p else p,
            "total_titik": 0,
            "sudah_dilakukan": 0,
            "belum_dilakukan": 0,
            "persentase_selesai": 0.0,
            "daftar_risiko": [],
            "efektivitas_database": {"Efektif": 0, "Cukup Efektif": 0, "Kelemahan Material": 0, "Belum Diisi": 0}
        }

    # Statistik agregat per Unit Eselon II (Inspektorat I s.d. V dan SIJ)
    summary_eselon2 = {
        'Inspektorat I': {'unit': 'Inspektorat I', 'total_titik': 0, 'sudah': 0, 'belum': 0, 'persentase': 0.0},
        'Inspektorat II': {'unit': 'Inspektorat II', 'total_titik': 0, 'sudah': 0, 'belum': 0, 'persentase': 0.0},
        'Inspektorat III': {'unit': 'Inspektorat III', 'total_titik': 0, 'sudah': 0, 'belum': 0, 'persentase': 0.0},
        'Inspektorat IV': {'unit': 'Inspektorat IV', 'total_titik': 0, 'sudah': 0, 'belum': 0, 'persentase': 0.0},
        'Inspektorat V': {'unit': 'Inspektorat V', 'total_titik': 0, 'sudah': 0, 'belum': 0, 'persentase': 0.0},
        'Sekretariat Inspektorat Jenderal': {'unit': 'Sekretariat Inspektorat Jenderal', 'alias': 'SIJ', 'total_titik': 0, 'sudah': 0, 'belum': 0, 'persentase': 0.0}
    }

    for k in sorted_keys:
        r_item = risks_map[k]
        for pic_name, mit in r_item["pic_mitigasi"].items():
            st = mit["status"]
            ef = mit["efektivitas"]
            es2 = mit["kategori_eselon2"]

            # Update per PIC
            if pic_name in summary_per_pic:
                s_pic = summary_per_pic[pic_name]
                s_pic["total_titik"] += 1
                s_pic["daftar_risiko"].append(k)
                if st == "Sudah Dilakukan":
                    s_pic["sudah_dilakukan"] += 1
                else:
                    s_pic["belum_dilakukan"] += 1

                if "Cukup" in ef: s_pic["efektivitas_database"]["Cukup Efektif"] += 1
                elif "Efektif" in ef: s_pic["efektivitas_database"]["Efektif"] += 1
                elif "Kelemahan" in ef: s_pic["efektivitas_database"]["Kelemahan Material"] += 1
                else: s_pic["efektivitas_database"]["Belum Diisi"] += 1

            # Update Eselon II
            if es2 in summary_eselon2:
                s_es = summary_eselon2[es2]
                s_es["total_titik"] += 1
                if st == "Sudah Dilakukan":
                    s_es["sudah"] += 1
                else:
                    s_es["belum"] += 1

    # Hitung persentase
    for p, s in summary_per_pic.items():
        if s["total_titik"] > 0:
            s["persentase_selesai"] = round((s["sudah_dilakukan"] / s["total_titik"]) * 100, 1)

    for e, s in summary_eselon2.items():
        if s["total_titik"] > 0:
            s["persentase"] = round((s["sudah"] / s["total_titik"]) * 100, 1)

    total_titik_itjen = sum(s["total_titik"] for s in summary_eselon2.values())
    total_sudah_itjen = sum(s["sudah"] for s in summary_eselon2.values())
    total_belum_itjen = total_titik_itjen - total_sudah_itjen
    persentase_itjen = round((total_sudah_itjen / total_titik_itjen) * 100, 1) if total_titik_itjen > 0 else 0

    return {
        "metadata": {
            "title": "Dashboard Monitoring Pelaksanaan Pengendalian Risiko per Unit PIC ITJEN",
            "institusi": "Inspektorat Jenderal Kementerian Energi dan Sumber Daya Mineral",
            "periode": "Triwulan III Tahun 2026",
            "sumber_data": GOOGLE_SHEET_URL,
            "total_kode_risiko": len(sorted_keys),  # 24 Risiko Lengkap
            "total_titik_kendali": total_titik_itjen,  # 80 Titik Kendali
            "total_baris_register": len(flat_records),  # 155 Baris Register Rinci
            "total_pengendalian_dilakukan": total_sudah_itjen,
            "total_pengendalian_belum": total_belum_itjen,
            "persentase_kepatuhan_total": persentase_itjen,
            "daftar_eselon2": list(summary_eselon2.keys()),
            "daftar_semua_pic": ordered_pics
        },
        "summary_eselon2": summary_eselon2,
        "summary_per_pic": summary_per_pic,
        "risks": [risks_map[k] for k in sorted_keys],
        "flat_records": flat_records
    }

def export_all(data, output_dir):
    """Menyimpan data bersih ke JSON, JS, dan CSV."""
    os.makedirs(output_dir, exist_ok=True)
    print("[3/4] Mengekspor dataset bersih ...")

    # 1. Simpan ke data_clean.json
    json_path = os.path.join(output_dir, "data_clean.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"      ✓ data_clean.json ({os.path.getsize(json_path) / 1024:.1f} KB)")

    # 2. Simpan ke data_clean.js
    js_path = os.path.join(output_dir, "data_clean.js")
    with open(js_path, "w", encoding="utf-8") as f:
        f.write("/* Dataset Hasil Pembersihan Otomatis dari Google Sheets */\n")
        f.write("window.RISK_DATA = ")
        json.dump(data, f, indent=2, ensure_ascii=False)
        f.write(";\n")
    print(f"      ✓ data_clean.js ({os.path.getsize(js_path) / 1024:.1f} KB)")

    # 3. Simpan ke CSV
    csv_path = os.path.join(output_dir, "monitoring_pengendalian_inspektorat.csv")
    df = pd.DataFrame(data["flat_records"])
    try:
        df.to_csv(csv_path, index=False, encoding="utf-8-sig")
        print(f"      ✓ monitoring_pengendalian_inspektorat.csv ({os.path.getsize(csv_path) / 1024:.1f} KB)")
    except PermissionError:
        alt_csv = os.path.join(output_dir, "monitoring_pengendalian_inspektorat_rekap.csv")
        df.to_csv(alt_csv, index=False, encoding="utf-8-sig")
        print(f"      ✓ {os.path.basename(alt_csv)} (karena file utama sedang dibuka)")

def main():
    print("=" * 70)
    print(" PIPELINE MONITORING PENGENDALIAN RISIKO ITJEN (LENGKAP SEMUA PIC) ")
    print("=" * 70)

    # 1. Unduh langsung dari Google Sheets
    wb = fetch_google_sheet(GOOGLE_SHEET_URL)

    # 2. Ekstraksi dan pembersihan data lengkap
    cleaned_data = process_monitoring_data(wb)

    # 3. Ekspor ke file output
    output_dir = os.path.dirname(os.path.abspath(__file__))
    export_all(cleaned_data, output_dir)

    # 4. Generate grafik eksekutif Seaborn
    try:
        from generate_charts_seaborn import generate_all
        print("\n[4/5] Menghasilkan PNG laporan (300 DPI)...")
        generate_all(cleaned_data, os.path.join(output_dir, "images"))
        print("      ✓ Seluruh grafik laporan berhasil diperbarui!")
    except Exception as e:
        print(f"      [INFO] Skip Seaborn generator: {e}")

    print("\n[5/5] [SELESAI] Pipeline selesai dan seluruh dataset PIC berhasil disinkronkan!")

if __name__ == "__main__":
    main()
