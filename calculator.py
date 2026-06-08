"""
calculator.py
Glues the tax engine + relief catalogue into a full assessment, plus a
year-end action plan. Mirrors the LHDN computation order:

  gross -> (statutory deductions) -> (reliefs) -> chargeable
        -> tax -> (rebates) -> tax payable -> refund vs PCB
"""

from tax_engine import compute_tax, marginal_rate
from reliefs import build_reliefs

# Demo sample data per persona (stand-in for a parsed EA / P&L form).
SAMPLE = {
    "individual": {
        "grossIncome": 96000, "bonus": 8000, "epf": 4000, "socso": 350,
        "pcb": 4800, "employer": "Redleaf Ventures Sdn Bhd", "icLast4": "****-2847",
    },
    "sme": {
        "grossIncome": 1250000, "allowableExp": 820000, "capAllowance": 48000,
        "directorFees": 180000, "epf": 0, "socso": 0, "pcb": 0,
        "employer": "Kedai Kopi Hijau Sdn Bhd", "icLast4": "202301-M",
    },
    "freelancer": {
        "grossIncome": 142000, "bonus": 0, "epf": 4000, "socso": 0,
        "pcb": 0, "employer": "Self-employed (design)", "icLast4": "****-1193",
    },
}


def compute_rebate(answers: dict, chargeable: float) -> float:
    """s.6A rebates: RM400 individual rebate if chargeable <= 35,000; zakat is a full rebate."""
    rebate = 0
    if chargeable <= 35000:
        rebate += 400
    if answers.get("zakat") == "yes":
        rebate += float(answers.get("zakatAmount") or 0)
    return rebate


def run_calculation(extracted: dict, answers: dict) -> dict:
    gross = (extracted.get("grossIncome", 0) or 0) + (extracted.get("bonus", 0) or 0)
    statutory = (extracted.get("epf", 0) or 0) + (extracted.get("socso", 0) or 0)

    reliefs = build_reliefs(extracted, answers)
    relief_total = sum(r["amount"] for r in reliefs)
    chargeable = max(0, gross - relief_total)

    tax = compute_tax(chargeable)
    rebate = compute_rebate(answers, chargeable)
    payable = max(0, tax - rebate)

    pcb = extracted.get("pcb", 0) or 0
    refund = max(0, pcb - payable)

    # Baseline = filing with auto reliefs only (no wizard reliefs claimed).
    baseline_reliefs = sum(r["amount"] for r in reliefs if r["id"] in ("personal", "epf", "socso"))
    baseline_chargeable = max(0, gross - baseline_reliefs)
    baseline_tax = max(0, compute_tax(baseline_chargeable)
                       - (400 if baseline_chargeable <= 35000 else 0))
    savings = max(0, baseline_tax - payable)

    return {
        "gross": gross, "statutory": statutory, "reliefs": reliefs,
        "reliefTotal": relief_total, "chargeable": chargeable, "tax": tax,
        "rebate": rebate, "payable": payable, "pcb": pcb, "refund": refund,
        "savings": savings, "baselineTax": baseline_tax,
        "effectiveRate": round((payable / gross) * 100, 2) if gross else 0,
    }


def build_actions(extracted: dict, answers: dict, calc: dict):
    """Conditional year-end moves, ranked by ringgit saved. Returns top 3."""
    rate = marginal_rate(calc["chargeable"])
    pct = round(rate * 100)
    items = []

    if answers.get("prs") != "yes":
        items.append({
            "id": "prs", "spend": 3000, "save": round(3000 * rate),
            "title": {"en": "Top up your PRS to RM 3,000", "bm": "Tambah PRS kepada RM 3,000"},
            "deadline": {"en": "31 Dec 2025", "bm": "31 Dis 2025"},
            "tag": {"en": "Highest efficiency", "bm": "Kecekapan tertinggi"},
            "why": {"en": f"PRS contributions are deductible up to RM 3,000 under s.49(1D). At your bracket each ringgit cuts about {pct}% off tax.",
                    "bm": f"Sumbangan PRS boleh ditolak sehingga RM 3,000 di bawah s.49(1D). Pada band anda setiap ringgit mengurangkan kira-kira {pct}% cukai."},
            "cite": "ITA 1967 s.49(1D)",
        })
    if answers.get("sspn") != "yes" and answers.get("kids") == "yes":
        items.append({
            "id": "sspn", "spend": 8000, "save": round(8000 * rate),
            "title": {"en": "Open an SSPN-i and deposit RM 8,000", "bm": "Buka SSPN-i & deposit RM 8,000"},
            "deadline": {"en": "31 Dec 2025", "bm": "31 Dis 2025"},
            "tag": {"en": "Biggest absolute saving", "bm": "Jimat mutlak tertinggi"},
            "why": {"en": "Net SSPN-i deposits for a child are relief up to RM 8,000 under s.46(1)(k). The funds stay yours, earmarked for education.",
                    "bm": "Deposit bersih SSPN-i untuk anak adalah pelepasan sehingga RM 8,000 di bawah s.46(1)(k). Dana kekal milik anda untuk pendidikan."},
            "cite": "ITA 1967 s.46(1)(k)",
        })
    if answers.get("lifestyle") != "yes":
        items.append({
            "id": "lifestyle", "spend": 2500, "save": round(2500 * rate),
            "title": {"en": "Finish your lifestyle claim before year-end", "bm": "Lengkapkan tuntutan gaya hidup"},
            "deadline": {"en": "31 Dec 2025", "bm": "31 Dis 2025"},
            "tag": {"en": "Easiest win", "bm": "Paling mudah"},
            "why": {"en": "Books, laptop, tablet, phone, internet or printers count up to RM 2,500 under s.46(1)(p). Keep e-receipts.",
                    "bm": "Buku, laptop, tablet, telefon, internet atau pencetak dikira sehingga RM 2,500 di bawah s.46(1)(p). Simpan e-resit."},
            "cite": "ITA 1967 s.46(1)(p)",
        })
    if answers.get("insurance") != "yes":
        items.append({
            "id": "med_ins", "spend": 4000, "save": round(4000 * rate),
            "title": {"en": "Buy education & medical insurance", "bm": "Beli insurans pendidikan & perubatan"},
            "deadline": {"en": "31 Dec 2025", "bm": "31 Dis 2025"},
            "tag": {"en": "Protective", "bm": "Perlindungan"},
            "why": {"en": "Education & medical premiums give up to RM 4,000 relief under s.49(1B) (raised from RM 3,000 in YA 2025) and cover a real risk.",
                    "bm": "Premium pendidikan & perubatan beri pelepasan sehingga RM 4,000 di bawah s.49(1B) (naik dari RM 3,000 pada TT 2025)."},
            "cite": "ITA 1967 s.49(1B)",
        })

    items.sort(key=lambda a: a["save"], reverse=True)
    return items[:3]
