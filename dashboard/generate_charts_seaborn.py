"""
Generator Grafik Laporan (PNG 300 DPI) - Dashboard Monitoring Pengendalian Risiko ITJEN KESDM

Angka dihitung dengan aturan yang SAMA seperti index.html, sehingga PNG laporan dan dashboard konsisten:
- Titik mitigasi   = pasangan risiko x PIC; status: lengkap (semua rencana tindak terealisasi), on progress (sebagian), belum sama sekali.
- Efektivitas      = dihitung per titik mitigasi (bukan per baris register).
- Rencana tindak   = baris register yang punya rencana (F) atau realisasi (H); baris kosong tidak dihitung.

Palet sama dengan dashboard: navy + amber, dengan aksen kuning logo ESDM di bagian atas.
Keluaran: images/chart_unit.png, images/chart_efek.png, images/chart_rencana.png
"""

import json
import logging
import os
import textwrap

import matplotlib.pyplot as plt
import numpy as np
import seaborn as sns

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

C = {
    "ink": "#0B0B0C", "text": "#334155", "muted": "#64748B", "faint": "#94A3B8",
    "line": "#E2E8F0", "track": "#E2E8F0", "card": "#FFFFFF",
    "brand": "#FFF500", "brand_deep": "#FFC800",
    "ok": "#1E3A8A", "ok_dark": "#1E3A8A", "blue": "#0284C7",
    "warn": "#F59E0B", "warn_dark": "#D97706",
    "bad": "#E11D48", "bad_dark": "#E11D48",
    "none": "#CBD5E1",
}
FOOTER = "Sumber: Dashboard Monitoring Pengendalian Risiko  •  Inspektorat Jenderal KESDM"
SIJ_FULL = "Sekretariat Inspektorat Jenderal"


# ------------------------------------------------------------------ data
def load_data():
    base = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(base, "data_clean.json"), "r", encoding="utf-8") as f:
        return json.load(f)


def efek_class(v):
    v = v or ""
    if "Cukup" in v:
        return "cukup"
    if "Efektif" in v:
        return "efektif"
    if "Kelemahan" in v:
        return "kelemahan"
    return "belum"


def pct(a, b):
    from decimal import Decimal, ROUND_HALF_UP
    return float((Decimal(str(a)) / Decimal(str(b)) * 100).quantize(Decimal('0.1'), rounding=ROUND_HALF_UP)) if b else 0.0


def fmt(p):
    return (f"{p:.1f}".rstrip("0").rstrip(".")).replace(".", ",")


def compute(data):
    titik = [m for r in data.get("risks", []) for m in r.get("pic_mitigasi", {}).values()]
    efek = {"efektif": 0, "cukup": 0, "kelemahan": 0, "belum": 0}
    for m in titik:
        efek[efek_class(m.get("efektivitas"))] += 1

    flat = data.get("flat_records", [])
    items = [r for r in flat if r.get("rencana_tindak_pengendalian") or r.get("pengendalian_yang_sudah_dilakukan")]
    pics = data.get("metadata", {}).get("daftar_semua_pic") or list(data.get("summary_per_pic", {}).keys())
    per_pic = {p: [0, 0] for p in pics}
    for r in items:
        p = r.get("pic_mitigasi")
        if not p:
            continue
        per_pic.setdefault(p, [0, 0])
        per_pic[p][0] += 1
        if r.get("status_pengendalian") == "Sudah Dilakukan":
            per_pic[p][1] += 1
    return {"total_titik": len(titik), "efek": efek, "pics": list(per_pic.keys()), "per_pic": per_pic}


# ------------------------------------------------------------------ gaya
def setup_style():
    sns.set_theme(style="white")
    plt.rcParams.update({
        "font.family": "sans-serif",
        "font.sans-serif": ["Plus Jakarta Sans", "Inter", "Segoe UI", "Helvetica Neue", "Arial", "DejaVu Sans"],
        "axes.edgecolor": C["line"], "axes.labelcolor": C["muted"],
        "xtick.color": C["muted"], "ytick.color": C["muted"],
        "xtick.major.size": 0, "ytick.major.size": 0,
        "legend.frameon": False,
    })


def new_figure(size, title, subtitle):
    fig = plt.figure(figsize=size, dpi=300)
    fig.patch.set_facecolor(C["card"])
    fig.add_artist(plt.Rectangle((0, 0.982), 1, 0.018, transform=fig.transFigure,
                                 facecolor=C["brand"], edgecolor="none"))
    fig.text(0.04, 0.94, title, fontsize=17, fontweight="bold", color=C["ink"], va="top")
    fig.text(0.04, 0.885, subtitle, fontsize=10.5, color=C["muted"], va="top")
    fig.text(0.04, 0.025, FOOTER, fontsize=7.5, color=C["faint"], va="bottom")
    # logo (opsional) di kanan atas
    base = os.path.dirname(os.path.abspath(__file__))
    for cand in (os.path.join(base, "images", "logo-esdm.png"), os.path.join(base, "..", "images", "logo-esdm.png")):
        if os.path.exists(cand):
            try:
                img = plt.imread(cand)
                lax = fig.add_axes([0.915, 0.86, 0.065, 0.10])
                lax.imshow(img)
                lax.axis("off")
            except Exception:
                pass
            break
    return fig


def style_axes(ax):
    ax.set_facecolor(C["card"])
    ax.grid(axis="x", color=C["line"], linewidth=0.7, zorder=0)
    ax.set_axisbelow(True)
    sns.despine(ax=ax, top=True, right=True, left=True, bottom=True)


def save(fig, out_dir, name):
    path = os.path.join(out_dir, name)
    fig.savefig(path, dpi=300, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.25)
    plt.close(fig)
    print(f"[OK] Generated {path}")


def rag(p):
    return (C["ok"], C["ok_dark"]) if p >= 80 else (C["warn"], C["warn_dark"]) if p >= 50 else (C["bad"], C["bad_dark"])


def legend_above(ax, handles_labels, ncol):
    handles, labels = zip(*handles_labels)
    ax.legend(handles, labels, loc="lower left", bbox_to_anchor=(0.0, 1.02), ncol=ncol,
              fontsize=9.5, labelcolor=C["text"], handlelength=1, handleheight=1, columnspacing=1.6)


# ------------------------------------------------------------------ status titik
def titik_status(data):
    """Status tiga tingkat per titik mitigasi (risiko x PIC), sama dengan dashboard:
    lengkap = semua rencana tindak terealisasi; progress = sebagian; belum = belum ada."""
    groups = {}
    for r in data.get("flat_records", []):
        if r.get("rencana_tindak_pengendalian") or r.get("pengendalian_yang_sudah_dilakukan"):
            groups.setdefault((r.get("no_risiko"), r.get("pic_mitigasi")), []).append(
                r.get("status_pengendalian") == "Sudah Dilakukan")
    order = [u for u in data.get("summary_eselon2", {}).keys()]
    units = {}
    for risk in data.get("risks", []):
        for pic in risk.get("pic_mitigasi", {}):
            v = groups.get((risk.get("no"), pic), [])
            st = "lengkap" if v and all(v) else "progress" if any(v) else "belum"
            u = SIJ_FULL if "SIJ" in pic else pic
            units.setdefault(u, {"lengkap": 0, "progress": 0, "belum": 0})[st] += 1
    keys = [u for u in order if u in units] + [u for u in units if u not in order]
    return keys, units


# ------------------------------------------------------------------ grafik 1
def generate_chart_unit(data, out_dir):
    keys, units = titik_status(data)
    labels = [("Sekretariat Itjen (SIJ)" if u == SIJ_FULL else u) for u in keys]
    lk = np.array([units[u]["lengkap"] for u in keys])
    pg = np.array([units[u]["progress"] for u in keys])
    bl = np.array([units[u]["belum"] for u in keys])
    tot = lk + pg + bl
    T = int(tot.sum())

    fig = new_figure((10.5, 5.8), "Status Pengendalian per Unit Eselon II",
                     f"{int(lk.sum())} dari {T} titik mitigasi lengkap ({fmt(pct(lk.sum(), T))}%); "
                     f"{int(pg.sum())} on progress, {int(bl.sum())} belum sama sekali")
    ax = fig.add_axes([0.22, 0.13, 0.70, 0.60])
    style_axes(ax)
    y = np.arange(len(keys))[::-1]
    h = 0.52
    b1 = ax.barh(y, lk, h, color=C["ok"], edgecolor="white", linewidth=1.5, zorder=3, label=f"Lengkap  {int(lk.sum())}")
    b2 = ax.barh(y, pg, h, left=lk, color=C["warn"], edgecolor="white", linewidth=1.5, zorder=3, label=f"On progress  {int(pg.sum())}")
    b3 = ax.barh(y, bl, h, left=lk + pg, color=C["none"], edgecolor="white", linewidth=1.5, zorder=3, label=f"Belum sama sekali  {int(bl.sum())}")
    for i in range(len(keys)):
        for val, left, col in ((lk[i], 0, "white"), (pg[i], lk[i], "white"), (bl[i], lk[i] + pg[i], C["text"])):
            if val >= 1:
                ax.text(left + val / 2, y[i], int(val), ha="center", va="center", color=col, fontsize=10, fontweight="bold")
        p = pct(lk[i], tot[i])
        ax.text(tot[i] + 0.35, y[i], f"{fmt(p)}%", va="center", fontsize=10, fontweight="bold", color=rag(p)[1])
    ax.set_yticks(y)
    ax.set_yticklabels(labels, fontsize=10, fontweight="600", color=C["text"])
    ax.set_xlim(0, max(tot.max(), 5) * 1.18)
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.set_xlabel("Jumlah titik mitigasi (angka di ujung bar = persentase titik lengkap)", fontsize=9.5)
    legend_above(ax, [(b1, b1.get_label()), (b2, b2.get_label()), (b3, b3.get_label())], 3)
    save(fig, out_dir, "chart_unit.png")


# ------------------------------------------------------------------ grafik 2
def generate_chart_efek(data, out_dir):
    s = compute(data)
    total = s["total_titik"]
    e = s["efek"]
    dinilai = e["efektif"] + e["cukup"] + e["kelemahan"]
    names = ["Efektif", "Cukup Efektif", "Kelemahan Material", "Belum dinilai"]
    vals = [e["efektif"], e["cukup"], e["kelemahan"], e["belum"]]
    cols = [C["ok"], C["blue"], C["bad"], C["none"]]

    fig = new_figure((10, 5.8), "Efektivitas Pengendalian",
                     f"Penilaian efektivitas per titik mitigasi ({total} titik)")
    ax = fig.add_axes([0.03, 0.10, 0.50, 0.72])
    ax.pie(vals if total else [1], colors=cols if total else [C["none"]], startangle=90, counterclock=False,
           wedgeprops=dict(width=0.28, edgecolor="white", linewidth=3))
    ax.text(0, 0.07, f"{dinilai}/{total}", ha="center", va="center", fontsize=28, fontweight="bold", color=C["ink"])
    ax.text(0, -0.14, "titik sudah dinilai", ha="center", va="center", fontsize=10, color=C["muted"])
    ax.set_aspect("equal")

    lx = fig.add_axes([0.57, 0.18, 0.40, 0.58])
    lx.axis("off")
    lx.set_xlim(0, 1)
    lx.set_ylim(0, 1)
    step = 1 / len(names)
    for i, (n, v, col) in enumerate(zip(names, vals, cols)):
        yy = 1 - step * (i + 0.5)
        lx.add_patch(plt.Rectangle((0, yy - 0.045), 0.045, 0.09, color=col))
        lx.text(0.09, yy + 0.035, n, fontsize=11, fontweight="bold", color=C["text"], va="center")
        lx.text(0.09, yy - 0.045, f"{v} titik  •  {fmt(pct(v, total))}%", fontsize=9.5, color=C["muted"], va="center")
        if i < len(names) - 1:
            lx.plot([0, 1], [yy - step / 2] * 2, color=C["line"], lw=0.8)
    save(fig, out_dir, "chart_efek.png")


# ------------------------------------------------------------------ grafik 3
def generate_chart_rencana(data, out_dir):
    s = compute(data)
    pics = s["pics"]
    tot = np.array([s["per_pic"][p][0] for p in pics])
    sud = np.array([s["per_pic"][p][1] for p in pics])
    sisa = tot - sud
    ps = [pct(a, b) for a, b in zip(sud, tot)]

    fig = new_figure((10.5, 6.8), "Realisasi Rencana Tindak per PIC",
                     f"{int(sud.sum())} dari {int(tot.sum())} rencana tindak terealisasi ({fmt(pct(sud.sum(), tot.sum()))}%)")
    ax = fig.add_axes([0.22, 0.12, 0.70, 0.62])
    style_axes(ax)
    y = np.arange(len(pics))[::-1]
    h = 0.52
    ax.barh(y, sud, h, color=[rag(p)[0] for p in ps], edgecolor="white", linewidth=1.5, zorder=3)
    ax.barh(y, sisa, h, left=sud, color=C["track"], edgecolor="white", linewidth=1.5, zorder=3)
    for i in range(len(pics)):
        if sud[i] >= 2:
            ax.text(sud[i] / 2, y[i], int(sud[i]), ha="center", va="center", color="white", fontsize=9.5, fontweight="bold")
        ax.text(tot[i] + 0.4, y[i], f"{sud[i]}/{tot[i]} · {fmt(ps[i])}%", va="center", fontsize=9.5,
                fontweight="bold", color=rag(ps[i])[1])
    ax.set_yticks(y)
    ax.set_yticklabels([textwrap.fill(p, 24) for p in pics], fontsize=10, fontweight="600", color=C["text"])
    ax.set_xlim(0, max(tot.max(), 5) * 1.25)
    ax.xaxis.set_major_locator(plt.MaxNLocator(integer=True))
    ax.set_xlabel("Jumlah rencana tindak", fontsize=9.5)
    hs = [plt.Rectangle((0, 0), 1, 1, color=c) for c in (C["ok"], C["warn"], C["bad"], C["track"])]
    legend_above(ax, list(zip(hs, ["Capaian 80% atau lebih", "50 sampai 79%", "Di bawah 50%", "Belum terealisasi"])), 4)
    save(fig, out_dir, "chart_rencana.png")


def generate_all(data, out_dir):
    setup_style()
    os.makedirs(out_dir, exist_ok=True)
    generate_chart_unit(data, out_dir)
    generate_chart_efek(data, out_dir)
    generate_chart_rencana(data, out_dir)


def main():
    data = load_data()
    out_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
    print("Generating report charts...")
    generate_all(data, out_dir)
    print("All charts generated successfully!")


if __name__ == "__main__":
    main()
