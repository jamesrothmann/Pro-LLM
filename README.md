# Pro-LLM (Leader–Worker–Formatter)

A Streamlit chat application that approximates GPT-5-Pro style behavior using:
- Leader: Gemini 2.5 Pro for planning, Google Search, and URL Context
- Workers: Groq `openai/gpt-oss-120b` in parallel
- Formatter: Gemini 2.5 Flash for schema enforcement and final polish

## Features
- Google Search + URL Context grounding
- Parallel worker iterations with evidence voting reducer
- Deterministic merge with confidence scoring
- Streamlit chat UI with expandable evidence panels
- Export of plan, sections, evidence log, and final outputs

## Quickstart

1. Python 3.10+ recommended.
2. `pip install -r requirements.txt`
3. Create `.env` from `.env.example` and add your keys.
4. `streamlit run app.py`

## Notes
- Cost control: adjust K workers, URL budget, and temperature in the sidebar.
- Respect site terms and robots; the URL Context tool avoids paywalled content.
- This repository provides example prompts and orchestration you can adapt.