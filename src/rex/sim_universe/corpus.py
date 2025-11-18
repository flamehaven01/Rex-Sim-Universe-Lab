from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel


class ClaimType(str, Enum):
    AXIOM = "axiom"
    THEOREM = "theorem"
    CONJECTURE = "conjecture"
    OBJECTION = "objection"
    CONTEXT = "context"


class AssumptionRole(str, Enum):
    SUPPORT = "support"
    CONTEST = "contest"
    CONTEXT = "context"


class PaperEntry(BaseModel):
    id: str
    title: str
    authors: List[str]
    year: int
    venue: Optional[str] = None
    doi: Optional[str] = None
    tags: List[str] = []


class ClaimEntry(BaseModel):
    id: str
    paper_id: str
    type: ClaimType
    section_label: Optional[str] = None
    location_hint: Optional[str] = None
    summary: str
    tags: List[str] = []


class ToeAssumption(BaseModel):
    claim_id: str
    role: AssumptionRole
    weight: float = 1.0

    def __init__(self, **data):
        super().__init__(**data)
        if isinstance(self.role, str):
            self.role = AssumptionRole(self.role)



class ToeCandidate(BaseModel):
    id: str
    label: str
    assumptions: List[ToeAssumption]

    def __init__(self, **data):
        super().__init__(**data)
        self.assumptions = [
            a if isinstance(a, ToeAssumption) else ToeAssumption(**a) for a in self.assumptions
        ]



class SimUniverseCorpus(BaseModel):
    """Evidence-aware corpus for simulation-universe experiments."""

    id: str
    version: str
    description: Optional[str] = None
    papers: List[PaperEntry]
    claims: List[ClaimEntry]
    toe_candidates: List[ToeCandidate]

    def __init__(self, **data):
        super().__init__(**data)
        self.papers = [p if isinstance(p, PaperEntry) else PaperEntry(**p) for p in self.papers]
        self.claims = [c if isinstance(c, ClaimEntry) else ClaimEntry(**c) for c in self.claims]
        self.toe_candidates = [
            t if isinstance(t, ToeCandidate) else ToeCandidate(**t) for t in self.toe_candidates
        ]


    def paper_index(self) -> Dict[str, PaperEntry]:
        return {paper.id: paper for paper in self.papers}

    def claim_index(self) -> Dict[str, ClaimEntry]:
        return {claim.id: claim for claim in self.claims}

    def toe_index(self) -> Dict[str, ToeCandidate]:
        return {toe.id: toe for toe in self.toe_candidates}
