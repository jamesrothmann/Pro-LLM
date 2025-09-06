from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any

class Citation(BaseModel):
    url: str
    loc: Optional[str] = None

class Claim(BaseModel):
    text: str
    citations: List[Citation] = Field(default_factory=list)

class WorkerOutput(BaseModel):
    claims: List[Claim] = Field(default_factory=list)
    summary: str = ""
    gaps: List[str] = Field(default_factory=list)
    confidence: float = 0.0

class URLItem(BaseModel):
    u: str
    why: str

class TaskNode(BaseModel):
    id: str
    desc: str
    deps: List[str] = Field(default_factory=list)

class Plan(BaseModel):
    structure: List[str]
    task_graph: List[TaskNode]
    urls: List[URLItem]
    schema: Dict[str, Any]
    checklist: List[str]

class SectionMerge(BaseModel):
    section_id: str
    text_md: str
    evidence_ids: List[int]
    confidence: float
    conflicts: List[str] = Field(default_factory=list)