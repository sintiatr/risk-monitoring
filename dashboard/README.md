# Dashboard Monitoring Pengendalian Risiko per Inspektorat (ITJEN)

Dashboard eksekutif interaktif untuk memonitor pelaksanaan pengendalian risiko di lingkungan **Inspektorat Jenderal Kementerian Energi dan Sumber Daya Mineral** mencakup **6 Unit Eselon II** (Inspektorat I s.d. V dan Sekretariat Itjen) serta **4 Sub-Bagian SIJ** (Total 24 Risiko / 80 Titik Mitigasi).

Dashboard ini dirancang **khusus agar ramah pengguna umum (awam)**: cukup klik dua kali (*double click*) file `index.html` langsung di browser tanpa perlu menginstal Python, Node.js, atau memahami file JSON.

---

## Fitur Utama untuk Pengguna Awam

1. **Buka Langsung Tanpa Instalasi Software Tambahan**
   - Penerima folder cukup membuka file `index.html` dengan Google Chrome, Microsoft Edge, atau browser modern lainnya.
   - Tidak memerlukan instalasi Python, Jupyter Notebook, server web, atau terminal apapun.

2. **Sinkronisasi Real-Time Otomatis dari Google Sheets**
   - Saat file `index.html` dibuka, dashboard langsung terhubung ke Google Sheets secara real-time.
   - Dilengkapi **Auto-Sync Otomatis** (tiap 60 detik) dan tombol **"Sinkronkan Sekarang"** untuk menarik perubahan data terbaru tanpa memuat ulang halaman.
   - Status sinkronisasi ditampilkan langsung pada bilah status di bawah header (`Live Sinkronisasi Aktif` dan jam update terakhir).

3. **Menu Samping (Tombol Garis Tiga ☰)**
   - Di sudut kiri atas terdapat tombol menu hamburger (`☰`).
   - Berisi menu navigasi cepat:
     * **Tab Dashboard & Grafik**: 4 KPI, sorotan otomatis, tiga grafik interaktif (capaian per unit, efektivitas, realisasi rencana tindak per PIC) dan catatan validasi data. Grafik mengikuti data sinkronisasi langsung; tombol unduh pada tiap grafik menyimpan PNG terbaru.
     * **Tab Matriks 24 Risiko**: Matriks 24 Risiko × 6 Kolom Unit Eselon II (interaktif, klik sel untuk melihat detail).
     * **Tab Tabel Register (155 Baris Rinci)**: Tabel lengkap seluruh rincian per baris rencana tindak pengendalian (F) dan realisasi pengendalian (H), dilengkapi filter sticky yang tetap mengambang saat di-scroll, pencarian real-time, serta uraian risiko lengkap di setiap baris.
     * **Ubah Link Data**: Mengganti tautan Google Sheets sewaktu-waktu (misal untuk TW berikutnya). Link baru disimpan otomatis di `localStorage`.
     * **Buka Sheet**: Membuka Google Spreadsheet sumber data langsung di tab baru.

4. **Mode Bekerja Offline (Tanpa Internet Tetap Aman)**
   - Jika pengguna membuka dashboard saat tidak ada koneksi internet, dashboard tetap langsung terbuka secara instan menggunakan dataset lokal cadangan (`data_clean.js`). Tidak akan terjadi error atau layar putih.

---

## 📋 Ketentuan Format Kolom Spreadsheet Baru

Jika Anda ingin mengganti link data dengan Google Spreadsheet baru, pastikan file tersebut memenuhi kriteria berikut:

1. **Hak Akses Google Sheets**:
   - Klik tombol **Bagikan (Share)** di Google Sheets.
   - Ubah Akses Umum menjadi **"Siapa saja yang memiliki link" -> "Pelihat" (Anyone with the link can view)**.
2. **Ketentuan Nama Kolom (Wajib Ada di Sheet)**:
   - **Jumlah risiko dan rencana tindak pengendalian bersifat dinamis** (bisa bertambah atau berkurang).
   - **Yang wajib ada dan sama adalah nama-nama kolom berikut**:
     1. `No` (Nomor urut risiko)
     2. `Kode Risiko` (Kode identifikasi register risiko)
     3. `Uraian Risiko` (Deskripsi/peristiwa risiko)
     4. `PIC Mitigasi` (Unit pelaksana mitigasi)
     5. `Rencana Tindak Pengendalian` (Rencana aksi/langkah mitigasi)
     6. `Pengendalian yang Sudah Dilakukan` (Realisasi tindak lanjut)
     7. `Status` (Status capaian atau jika belum ada, otomatis diisi dari realisasi pengendalian)

---

## Struktur File dalam Folder

```text
dashboard/
├── index.html         <-- FILE UTAMA (Cukup double-click file ini untuk membuka dashboard)
├── data_clean.js      <-- Dataset cadangan lokal untuk mode offline
├── data_clean.json    <-- Format data terstruktur JSON
├── data_cleaner.py    <-- Script pipeline data Python (Opsional untuk administrator/developer)
├── generate_charts_seaborn.py <-- PNG laporan 300 DPI (opsional; aturan hitung sama dengan dashboard)
├── data_cleaner.ipynb <-- Jupyter notebook (Opsional)
├── monitoring_pengendalian_inspektorat.csv <-- File rekap CSV awal
└── README.md          <-- Panduan penggunaan ini
```

---

## Panduan Ringkas untuk Pengguna

1. Buka folder `dashboard`.
2. Klik ganda (**double click**) file `index.html`.
3. Dashboard akan langsung menampilkan:
   - KPI: Kode Risiko, Titik Mitigasi, Pengendalian Terlaksana (titik dan rencana tindak), Efektivitas Sudah Dinilai.
   - Capaian per Unit Eselon II, proporsi efektivitas, dan realisasi seluruh rencana tindak per PIC.
   - Catatan Validasi Data yang dihitung otomatis (baris kosong, realisasi tanpa rencana, titik yang baru sebagian terealisasi).
   - **Tab Matriks**: Seluruh 24 Kode Risiko × 6 Kolom Unit Eselon II (klik sel mana saja untuk membaca narasi lengkap pelaksanaan Kolom H).
   - **Tab Register**: Tabel daftar lengkap 155 baris rincian rencana tindak pengendalian (F) dan realisasi pengendalian (H) dengan filter sticky, pencarian real-time, dan uraian risiko terisi penuh.
4. Untuk memperbarui link data ke Google Spreadsheet lain, klik tombol **"Ubah Link Data"** pada menu atas dan masukkan link yang baru.

---

## Definisi Angka

- **Titik mitigasi** = pasangan risiko × PIC. Statusnya tiga tingkat:
  - **Lengkap**: semua rencana tindak pada titik itu terealisasi.
  - **On progress**: sebagian rencana tindak terealisasi.
  - **Belum sama sekali**: belum ada rencana tindak yang terealisasi.
- **Rencana tindak** = baris register yang memiliki rencana (kolom F) atau realisasi (kolom H). Baris kosong tidak dihitung. Sebuah rencana berstatus *Sudah* bila kolom H pada barisnya terisi.
- **Efektivitas** dihitung per titik mitigasi.
