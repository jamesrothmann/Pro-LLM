from typing import List, Dict, Any, Tuple
from collections import Counter, defaultdict
from schemas import WorkerOutput, SectionMerge, Claim

def _normalize_claim(text: str) -> str:
    return " ".join(text.lower().split())

def reduce_worker_outputs(section_id: str, worker_jsons: List[Dict[str, Any]]) -> Tuple[SectionMerge, List[Dict[str, Any]], List[Dict[str, Any]]]:
    parsed = []
    for j in worker_jsons:
        try:
            data = j.get("content", j)  # Groq SDK may store under 'content'
            if isinstance(data, dict) and "content" in j:
                data = j["content"]
            parsed.append(WorkerOutput(**data if isinstance(data, dict) else WorkerOutput.model_validate_json(str(data))))
        except Exception:
            continue

    claim_counts = Counter()
    claim_citations = defaultdict(list)
    all_conf = []

    for w in parsed:
        all_conf.append(w.confidence or 0.0)
        for c in w.claims:
            norm = _normalize_claim(c.text)
            claim_counts[norm] += 1
            claim_citations[norm].extend([ci.url for ci in c.citations])

    # Choose top claims by frequency
    top_norms = [t for t, cnt in claim_counts.most_common(20) if cnt >= 2 or len(parsed) == 1]
    md_lines = []
    bib_map = {}
    bib_list = []
    next_id = 1

    for norm in top_norms:
        urls = sorted(set(claim_citations.get(norm, [])))
        cite_ids = []
        for u in urls:
            if u not in bib_map:
                bib_map[u] = next_id
                bib_list.append({"id": next_id, "url": u})
                next_id += 1
            cite_ids.append(bib_map[u])
        # reconstruct original text from one sample
        original_text = next((c.text for w in parsed for c in w.claims if _normalize_claim(c.text) == norm), norm)
        if cite_ids:
            md_lines.append(f"- {original_text} " + " ".join([f"[{cid}]" for cid in cite_ids]))
        else:
            md_lines.append(f"- {original_text}")

    # Summaries
    summaries = [w.summary for w in parsed if w.summary]
    if summaries:
        md_lines.insert(0, "### Summary\n" + summaries[0])

    merged_md = "\n".join(md_lines).strip()
    confidence = sum(all_conf) / max(1, len(all_conf))

    merge = SectionMerge(
        section_id=section_id,
        text_md=merged_md,
        evidence_ids=[b['id'] for b in bib_list],
        confidence=confidence,
        conflicts=[]
    )
    return merge, bib_list, [w.model_dump() for w in parsed]