"""
chat.py
Grounded tax Q&A. Default is a deterministic rule-based responder so the app
works offline with zero API keys. If you set TAXATION_LLM=1 and provide an
ANTHROPIC_API_KEY (or wire your own GLM client in call_llm), it will defer to
that instead. Either way, answers are kept close to ITA 1967 / LHDN rulings.
"""

import os
import re

RULES = [
    {
        "match": r"(lifestyle|laptop|macbook|device|phone|tablet|ipad|computer|internet|broadband|printer|books?|magazine|subscription)",
        "reply": {
            "en": "The **lifestyle relief** (s.46(1)(p)) is capped at RM 2,500 and covers books, a laptop/phone/tablet (personal, non-business use), internet subscription and printers. Keep e-receipts. Note the separate RM 1,000 sports relief does not cover a laptop.",
            "bm": "**Pelepasan gaya hidup** (s.46(1)(p)) berhad RM 2,500 dan merangkumi buku, laptop/telefon/tablet (kegunaan peribadi), langganan internet dan pencetak. Simpan e-resit. Pelepasan sukan RM 1,000 berasingan tidak meliputi laptop.",
        },
        "cites": ["ITA s.46(1)(p)"],
    },
    {
        "match": r"(spouse|wife|husband|joint|married)",
        "reply": {
            "en": "If your spouse has no income or you file jointly, you qualify for the **spouse relief** of RM 4,000 under s.47(1). You cannot double-claim the same relief in both assessments, so for items like lifestyle or insurance only one of you claims each ringgit.",
            "bm": "Jika pasangan tiada pendapatan atau anda memfail bersama, anda layak pelepasan pasangan RM 4,000 di bawah s.47(1). Pelepasan sama tidak boleh dituntut dua kali.",
        },
        "cites": ["ITA s.47(1)"],
    },
    {
        "match": r"(relief).*(rebate)|(rebate).*(relief)|(difference|vs|versus).*(relief|rebate)",
        "reply": {
            "en": "Different mechanics. A **relief** reduces chargeable income *before* tax is computed, so a RM 1,000 relief in the 19% band saves RM 190. A **rebate** reduces tax *after* it is computed, ringgit for ringgit. Zakat is a rebate, as is the RM 400 individual rebate when chargeable income is RM 35,000 or below. Rebates are worth more per ringgit but cannot push tax below zero.",
            "bm": "Mekanik berbeza. **Pelepasan** mengurangkan pendapatan bercukai *sebelum* cukai dikira. **Rebat** mengurangkan cukai *selepas* dikira, ringgit demi ringgit. Zakat adalah rebat.",
        },
        "cites": ["ITA s.6A", "ITA s.46", "ITA s.47"],
    },
    {
        "match": r"(sspn|education.*saving)",
        "reply": {
            "en": "SSPN-i gives up to **RM 8,000** relief on *net* deposits (deposits minus withdrawals) for your child under s.46(1)(k), extended to YA 2027. The money remains yours, earmarked for education.",
            "bm": "SSPN-i memberi pelepasan sehingga RM 8,000 atas deposit bersih untuk anak di bawah s.46(1)(k), dilanjutkan ke TT 2027.",
        },
        "cites": ["ITA s.46(1)(k)"],
    },
    {
        "match": r"(prs|private retirement|pension)",
        "reply": {
            "en": "PRS contributions are deductible up to **RM 3,000** a year under s.49(1D), on top of your EPF relief. This relief has been extended to YA 2030.",
            "bm": "Sumbangan PRS boleh ditolak sehingga RM 3,000 setahun di bawah s.49(1D), dilanjutkan ke TT 2030.",
        },
        "cites": ["ITA s.49(1D)"],
    },
    {
        "match": r"(insurance|takaful|medical card|hospital plan)",
        "reply": {
            "en": "From **YA 2025** the education & medical insurance relief is **RM 4,000** (up from RM 3,000) under s.49(1B). Life insurance / Takaful for non-public-servants is a separate RM 3,000 under s.49(1)(b).",
            "bm": "Mulai **TT 2025** pelepasan insurans pendidikan & perubatan ialah **RM 4,000** (naik dari RM 3,000) di bawah s.49(1B). Insurans hayat ialah RM 3,000 berasingan di bawah s.49(1)(b).",
        },
        "cites": ["ITA s.49(1B)", "ITA s.49(1)(b)"],
    },
    {
        "match": r"(housing|home loan|house loan|mortgage|first.?time)",
        "reply": {
            "en": "New for YA 2025: **first-time homebuyers** can claim housing-loan interest relief if the SPA is signed 1 Jan 2025 to 31 Dec 2027. RM 7,000/year for homes up to RM 500k, or RM 5,000/year for RM 500k to RM 750k, for up to 3 consecutive years. Properties above RM 750k or rented out do not qualify.",
            "bm": "Baharu TT 2025: **pembeli rumah pertama** boleh tuntut pelepasan faedah pinjaman perumahan jika SPA ditandatangani 1 Jan 2025 hingga 31 Dis 2027. RM 7,000 setahun untuk rumah sehingga RM 500k, atau RM 5,000 untuk RM 500k-750k, sehingga 3 tahun.",
        },
        "cites": ["Budget 2025 Appendix 7"],
    },
    {
        "match": r"(medical|parent|hospital|treatment|dental|check.?up)",
        "reply": {
            "en": "Parental medical, care and dental expenses are claimable up to **RM 8,000 combined** for both parents under s.46(1)(c). Self/spouse/child medical (serious illness, fertility, vaccination, dental, mental health) is a separate cap of RM 10,000. Keep receipts from registered practitioners; LHDN can ask up to 7 years later.",
            "bm": "Perubatan, jagaan dan pergigian ibu bapa sehingga RM 8,000 gabungan di bawah s.46(1)(c). Perubatan diri/pasangan/anak ialah had berasingan RM 10,000. Simpan resit.",
        },
        "cites": ["ITA s.46(1)(c)"],
    },
    {
        "match": r"(zakat|fitrah)",
        "reply": {
            "en": "Zakat and fitrah are a **rebate**, not a relief: they reduce your tax payable ringgit-for-ringgit up to the full amount paid, but not below zero, under s.6A(3).",
            "bm": "Zakat dan fitrah ialah **rebat**, bukan pelepasan: mengurangkan cukai ringgit demi ringgit sehingga jumlah dibayar, di bawah s.6A(3).",
        },
        "cites": ["ITA s.6A(3)"],
    },
    {
        "match": r"(tax band|tax bracket|tax rate|how much tax|rate band|marginal rate|chargeable.*rate)",
        "reply": {
            "en": "Resident individual rates for YA 2025 are progressive: the first RM 5,000 is 0%, then 1% to RM 20k, 3% to RM 35k, 6% to RM 50k, 11% to RM 70k, 19% to RM 100k, 25% to RM 400k, 26% to RM 600k, 28% to RM 2m and 30% above RM 2m. Only the income inside each band is taxed at that band's rate.",
            "bm": "Kadar individu pemastautin TT 2025 adalah progresif: RM 5,000 pertama 0%, kemudian 1% hingga RM 20k, 3% hingga RM 35k, 6% hingga RM 50k, 11% hingga RM 70k, 19% hingga RM 100k, 25% hingga RM 400k, 26% hingga RM 600k, 28% hingga RM 2j dan 30% melebihi RM 2j. Hanya pendapatan dalam setiap band dicukai pada kadar band itu.",
        },
        "cites": ["ITA Schedule 1"],
    },
]

FALLBACK = {
    "reply": {
        "en": "Good question. Under the Income Tax Act 1967 the short answer depends on the facts, mainly whether the expense was wholly and exclusively incurred to produce income, or whether it maps to a named personal relief. Tell me the amount, the timing and who incurred it and I can point to the right section.",
        "bm": "Soalan yang baik. Di bawah Akta Cukai Pendapatan 1967, jawapannya bergantung pada fakta, sama ada perbelanjaan itu khusus untuk menjana pendapatan atau sepadan dengan pelepasan peribadi. Beri butiran lanjut dan saya akan rujuk seksyen yang betul.",
    },
    "cites": ["ITA 1967"],
}


def call_llm(question: str, lang: str):
    """Optional real-AI path. Returns (text, cites) or None to fall back.

    Plug in your own GLM/ILMU client here, or use Anthropic if a key is set.
    Kept disabled by default so the app runs with no external dependency.
    """
    if os.getenv("TAXATION_LLM") != "1":
        return None
    try:
        import anthropic  # only imported if you opt in
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
        system = ("You are Taxation, a Malaysian tax copilot. Answer strictly from the "
                  "Income Tax Act 1967 and LHDN Public Rulings for YA 2025. Be concise, "
                  "cite the exact section, and never invent figures. "
                  + ("Reply in Bahasa Malaysia." if lang == "bm" else "Reply in English."))
        msg = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=600,
            system=system,
            messages=[{"role": "user", "content": question}],
        )
        text = "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")
        return (text.strip(), ["ITA 1967 / LHDN"])
    except Exception:
        return None


def respond(question: str, lang: str = "en") -> dict:
    llm = call_llm(question, lang)
    if llm:
        return {"text": llm[0], "cites": llm[1]}
    q = question or ""
    for rule in RULES:
        if re.search(rule["match"], q, re.I):
            return {"text": rule["reply"].get(lang, rule["reply"]["en"]), "cites": rule["cites"]}
    return {"text": FALLBACK["reply"].get(lang, FALLBACK["reply"]["en"]), "cites": FALLBACK["cites"]}
