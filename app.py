import streamlit as st
from utils import get_env, SimpleCache
from providers.gemini import GeminiClient
from providers.groq_provider import GroqClient
from orchestrator import leader_plan, run_workers_parallel, format_final
import json
import os

st.set_page_config(page_title="Pro-LLM", layout="wide")
st.title("Pro-LLM — Leader · Worker · Formatter")

with st.sidebar:
    st.subheader("Keys")
    gemini_key = st.text_input("GEMINI_API_KEY", value=get_env("GEMINI_API_KEY"), type="password")
    groq_key = st.text_input("GROQ_API_KEY", value=get_env("GROQ_API_KEY"), type="password")
    st.subheader("Orchestration")
    k_workers = st.slider("Parallel workers K", 1, 8, 3)
    url_budget = st.slider("URL budget", 2, 20, 8)
    temperature = st.slider("Worker temperature", 0.0, 1.0, 0.2)
    run_plan = st.button("Run")

if "history" not in st.session_state:
    st.session_state.history = []

user_prompt = st.chat_input("Ask Pro-LLM anything...")
if user_prompt:
    st.session_state.history.append({"role": "user", "content": user_prompt})

# Render history
for msg in st.session_state.history:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if run_plan and st.session_state.history:
    last = st.session_state.history[-1]["content"]
    if not gemini_key or not groq_key:
        st.error("Please provide both GEMINI_API_KEY and GROQ_API_KEY in the sidebar.")
        st.stop()
    gemini = GeminiClient(api_key=gemini_key)
    groq = GroqClient(api_key=groq_key)
    with st.status("Planning with Leader...", state="running") as status:
        out = leader_plan(gemini, last, url_budget)
        plan = out["plan"]
        status.update(label="Leader done", state="complete")
    with st.expander("Plan JSON"):
        st.json(json.loads(plan.model_dump_json()))

    with st.status("Running Workers in parallel...", state="running") as status:
        sections = run_workers_parallel(groq, plan, k_workers, temperature)
        status.update(label="Workers done", state="complete")
    with st.expander("Worker merges and evidence"):
        st.json(sections)

    with st.status("Formatting final output...", state="running") as status:
        final = format_final(gemini, plan, sections)
        status.update(label="Formatter done", state="complete")

    md = final.get("markdown", "")
    js = final.get("json", {})
    with st.chat_message("assistant"):
        if md:
            st.markdown(md)
    with st.expander("Final JSON"):
        st.json(js)
    with st.expander("Download artifacts"):
        st.download_button("Plan.json", data=plan.model_dump_json(indent=2), file_name="plan.json", mime="application/json")
        st.download_button("Final.json", data=json.dumps(js, indent=2), file_name="final.json", mime="application/json")
        st.download_button("Final.md", data=md, file_name="final.md", mime="text/markdown")