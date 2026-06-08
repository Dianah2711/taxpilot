# TaxPilot — Malaysia AI Tax Relief Finder

> Stop leaving money on the table. TaxPilot finds every ringgit you're owed, with LHDN citations.

Full-stack rebuild of the SmarTax demo: a **Flask backend** owns the tax engine,
relief catalogue and chat (so the logic is server-side and authoritative), and a
single-page frontend (React via CDN, same teal/Fraunces design) talks to it over a
small JSON API.

## What it does

Pick a profile → "read" your EA / P&L (sample data) → answer 8 yes/no questions →
see your YA 2025 assessment, the reliefs you missed, a year-end action plan, and a
grounded Q&A chat. Every relief cites the exact section of the Income Tax Act 1967.

## Tax rules (verified for YA 2025, filing in 2026)

Bands and reliefs were checked against LHDN / PwC and the Budget 2025 amendments:

- **Bands** (resident individual, YA 2024 onwards, unchanged for YA 2025): 0% up to
  RM5k, then 1 / 3 / 6 / 11 / 19 / 25 / 26 / 28 / 30%. See `tax_engine.py`.
- **Reliefs** in `reliefs.py`, including the YA 2025 changes:
  - Education & medical insurance raised RM3,000 → **RM4,000** (s.49(1B))
  - Sports relief stays **RM1,000** (now also covers parents)
  - SSPN (RM8,000) extended to YA 2027; PRS (RM3,000) to YA 2030
  - Rebates: RM400 if chargeable income ≤ RM35,000; zakat is a full rebate (s.6A)

This is an educational demo, **not** legal or tax advice — confirm with LHDN or a
licensed tax agent before filing.

## Project structure

```
taxation/
  app.py            Flask app + JSON API, serves the frontend
  tax_engine.py     Progressive band engine (pure, deterministic)
  reliefs.py        YA 2025 relief catalogue + wizard questions
  calculator.py     Full assessment + year-end action plan + sample data
  chat.py           Rule-based tax Q&A (optional real-LLM hook)
  templates/
    index.html      React single-page frontend (calls the API)
  requirements.txt
```

## API

| Method | Path                  | Purpose                                   |
|--------|-----------------------|-------------------------------------------|
| GET    | `/api/config`         | Wizard questions + relief metadata        |
| GET    | `/api/sample/<mode>`  | Sample extracted figures (individual/sme/freelancer) |
| POST   | `/api/calculate`      | `{mode, extracted, answers}` → `{calc, actions}` |
| POST   | `/api/chat`           | `{question, lang}` → `{text, cites}`      |
| GET    | `/api/health`         | Liveness check                            |

## Run it

```bash
pip install -r requirements.txt
python app.py
# open http://localhost:5000
```

(On Mac use `pip3` / `python3` if needed.)

## Optional: real AI chat

Chat is rule-based by default so it runs with no keys. To use a real model, wire your
GLM/ILMU client in `chat.py:call_llm`, or use Anthropic:

```bash
export TAXPILOT_LLM=1
export ANTHROPIC_API_KEY=sk-...
pip install anthropic
```
