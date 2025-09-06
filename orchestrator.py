import json
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, Any, List
from providers.gemini import GeminiClient
from providers.groq_provider import GroqClient
from prompts import LEADER_SYSTEM_PROMPT, WORKER_SYSTEM_PROMPT, FORMATTER_SYSTEM_PROMPT
from schemas import Plan, SectionMerge
from reducers import reduce_worker_outputs
from utils import SimpleCache, clean_markdown

def parse_plan(raw_json_text: str) -> Plan:
    # Expect {"plan": {...}}
    try:
        data = json.loads(raw_json_text)
        if "plan" in data:
            return Plan(**data["plan"])
        # Fallback if the model returned the plan fields at root
        return Plan(**data)
    except Exception as e:
        raise ValueError(f"Leader plan JSON parse failed: {e}\nRaw: {raw_json_text[:500]}")

def leader_plan(gemini: GeminiClient, user_prompt: str, url_budget: int) -> Dict[str, Any]:
    resp = gemini.leader_plan(user_prompt=user_prompt, system_prompt=LEADER_SYSTEM_PROMPT, url_budget=url_budget)
    plan = parse_plan(resp["raw"])
    # Trim URL list to budget
    plan.urls = plan.urls[:url_budget]
    return {"plan": plan, "meta": resp.get("url_context_metadata")}

def run_workers_parallel(groq: GroqClient, plan: Plan, k_workers: int, temperature: float) -> List[Dict[str, Any]]:
    # For simplicity, concatenate URL list as evidence bundle
    evidence_bundle = "\n".join([u.u for u in plan.urls])
    # Each task node is run with K parallel workers that paraphrase the subtask slightly
    results = []
    for node in plan.task_graph:
        futures = []
        with ThreadPoolExecutor(max_workers=k_workers) as ex:
            for i in range(k_workers):
                subtask = f"{node.desc}\nParaphrase variant: {i+1}"
                futures.append(ex.submit(groq.worker, WORKER_SYSTEM_PROMPT, subtask, evidence_bundle, temperature))
            worker_jsons = []
            for fut in as_completed(futures):
                try:
                    worker_jsons.append(fut.result())
                except Exception as e:
                    worker_jsons.append({"error": str(e)})
        merge, bib, parsed_workers = reduce_worker_outputs(node.id, worker_jsons)
        results.append({"node_id": node.id, "merge": merge, "bibliography": bib, "workers": parsed_workers})
    return results

def format_final(gemini: GeminiClient, plan: Plan, sections: List[Dict[str, Any]]) -> Dict[str, Any]:
    # Combine merged markdown with a unified bibliography
    md_parts = []
    bib_all = []
    seen = set()
    for s in sections:
        m: SectionMerge = s["merge"]
        md_parts.append(f"## Section {m.section_id}\n\n{m.text_md}\n")
        for b in s["bibliography"]:
            key = b["url"]
            if key not in seen:
                seen.add(key)
                bib_all.append(b)
    merged_md = clean_markdown("\n".join(md_parts))
    resp = gemini.formatter(
        merged_markdown=merged_md,
        bibliography=bib_all,
        target_schema=plan.schema,
        system_prompt=FORMATTER_SYSTEM_PROMPT
    )
    try:
        data = json.loads(resp["raw"])
    except Exception:
        data = {"markdown": merged_md, "json": {"_warning": "formatter returned non-JSON", "raw": resp["raw"]}}
    return data