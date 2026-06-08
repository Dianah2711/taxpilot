"""
reliefs.py
YA 2025 relief catalogue for resident individuals, with statutory citations.
Caps verified against LHDN tax-relief list + Budget 2025 amendments.

Notes on YA 2025 changes baked in here:
  - Education & medical insurance: RM3,000 -> RM4,000  (Budget 2025)
  - Sports relief stays RM1,000 (now also covers parents)
  - SSPN (RM8,000) extended to YA 2027; PRS (RM3,000) extended to YA 2030
  - Housing-loan interest relief for first-time buyers is NEW (SPA 2025-2027)
"""

# Eight yes/no wizard questions -> reliefs they unlock.
QUESTIONS = [
    {"id": "married",   "icon": "users",   "key": "wiz_q_married",   "hint": "wiz_hint_married"},
    {"id": "kids",      "icon": "users",   "key": "wiz_q_kids",      "hint": "wiz_hint_kids"},
    {"id": "parents",   "icon": "heart",   "key": "wiz_q_parents",   "hint": "wiz_hint_parents"},
    {"id": "sspn",      "icon": "book",    "key": "wiz_q_sspn",      "hint": "wiz_hint_sspn"},
    {"id": "lifestyle", "icon": "sparkle", "key": "wiz_q_lifestyle", "hint": "wiz_hint_lifestyle"},
    {"id": "insurance", "icon": "shield",  "key": "wiz_q_insurance", "hint": "wiz_hint_insurance"},
    {"id": "prs",       "icon": "coin",    "key": "wiz_q_prs",       "hint": "wiz_hint_prs"},
    {"id": "zakat",     "icon": "diamond", "key": "wiz_q_zakat",     "hint": "wiz_hint_zakat"},
]

# auto      -> always applies, amount comes from the extracted form
# trigger_q -> applies only if the wizard answer for that question == "yes"
# claimed   -> demo: amount the filer is assumed to have ALREADY claimed
RELIEF_CATALOG = [
    {"id": "personal",   "name": {"en": "Individual & dependents",        "bm": "Individu & tanggungan"},
     "cap": 9000, "auto": True,  "cite": "ITA 1967 s.46(1)(a)"},
    {"id": "epf",        "name": {"en": "EPF / KWSP contribution",         "bm": "Caruman KWSP"},
     "cap": 4000, "auto": True,  "cite": "ITA 1967 s.49(1)(a)"},
    {"id": "socso",      "name": {"en": "SOCSO / EIS (PERKESO)",           "bm": "PERKESO / SIP"},
     "cap": 350,  "auto": True,  "cite": "ITA 1967 s.46(1)(i)"},
    {"id": "spouse",     "name": {"en": "Spouse (no income) / alimony",    "bm": "Pasangan (tiada pendapatan)"},
     "cap": 4000, "trigger_q": "married", "cite": "ITA 1967 s.47(1)"},
    {"id": "children",   "name": {"en": "Child relief (under 18)",         "bm": "Pelepasan anak (bawah 18)"},
     "cap": 2000, "trigger_q": "kids",    "cite": "ITA 1967 s.48(2)"},
    {"id": "parents",    "name": {"en": "Parental medical & care",         "bm": "Perubatan & jagaan ibu bapa"},
     "cap": 8000, "claimed": 5200, "trigger_q": "parents", "cite": "ITA 1967 s.46(1)(c)"},
    {"id": "sspn",       "name": {"en": "SSPN-i net deposit",              "bm": "Deposit bersih SSPN-i"},
     "cap": 8000, "claimed": 6000, "trigger_q": "sspn",    "cite": "ITA 1967 s.46(1)(k)"},
    {"id": "lifestyle",  "name": {"en": "Lifestyle (books, devices, internet)", "bm": "Gaya hidup"},
     "cap": 2500, "trigger_q": "lifestyle", "cite": "ITA 1967 s.46(1)(p)"},
    {"id": "sports",     "name": {"en": "Sports equipment, gym & fees",    "bm": "Peralatan, gim & yuran sukan"},
     "cap": 1000, "trigger_q": "lifestyle", "cite": "ITA 1967 s.46(1)(u)"},
    {"id": "life_ins",   "name": {"en": "Life insurance / Takaful (non-EPF)", "bm": "Insurans hayat (bukan KWSP)"},
     "cap": 3000, "trigger_q": "insurance", "cite": "ITA 1967 s.49(1)(b)"},
    {"id": "med_ins",    "name": {"en": "Education & medical insurance",   "bm": "Insurans pendidikan & perubatan"},
     "cap": 4000, "trigger_q": "insurance", "cite": "ITA 1967 s.49(1B)"},  # raised to 4,000 in YA 2025
    {"id": "prs",        "name": {"en": "Private Retirement Scheme (PRS)", "bm": "Skim Persaraan Swasta (PRS)"},
     "cap": 3000, "trigger_q": "prs", "cite": "ITA 1967 s.49(1D)"},
]


def build_reliefs(extracted: dict, answers: dict):
    """Return the reliefs that apply, with amount/claimed/new flags."""
    out = []
    for r in RELIEF_CATALOG:
        amount, applies = 0, False
        if r.get("auto"):
            applies = True
            if r["id"] == "personal":
                amount = r["cap"]
            elif r["id"] == "epf":
                amount = min(extracted.get("epf", 0) or 0, r["cap"])
            elif r["id"] == "socso":
                amount = min(extracted.get("socso", 0) or 0, r["cap"])
        elif r.get("trigger_q") and answers.get(r["trigger_q"]) == "yes":
            applies = True
            amount = r["cap"]  # simplified: filer claims the full cap

        if not applies:
            continue

        claimed = min(r.get("claimed", 0), amount) if r.get("claimed") is not None else 0
        is_new = bool(r.get("trigger_q")) and r.get("claimed") is None
        out.append({
            "id": r["id"], "name": r["name"], "cap": r["cap"], "cite": r["cite"],
            "amount": amount, "claimed": claimed, "isNew": is_new,
        })
    return out
