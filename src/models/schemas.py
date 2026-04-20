from pydantic import BaseModel


# --- Diff Parsing ---

class ChangedSymbol(BaseModel):
    name: str                    # e.g. "PaymentService.process_refund"
    symbol_type: str             # "function" | "method" | "class"
    calls: list[str] = []        # functions this symbol calls
    imported_by: list[str] = []  # files that import the containing module


class ChangedFile(BaseModel):
    path: str
    change_type: str             # "modified" | "added" | "deleted"
    changed_symbols: list[ChangedSymbol] = []
    lines_changed: int = 0
    diff_snippet: str = ""


class ChangeManifest(BaseModel):
    changed_files: list[ChangedFile]
    change_summary: str = ""


# --- Impact Tracing ---

class Dependent(BaseModel):
    file: str
    symbol: str
    relation: str                # e.g. "calls process_refund"


class TestCoverage(BaseModel):
    covered: list[str] = []
    not_covered: list[str] = []


class ImpactMap(BaseModel):
    direct_dependents: list[Dependent] = []
    transitive_dependents: list[Dependent] = []
    test_coverage: TestCoverage = TestCoverage()
    blast_radius: int = 0        # total files affected


# --- Risk Assessment ---

class RiskFactor(BaseModel):
    risk_type: str               # "historical_incident" | "signature_change" | "missing_test" | ...
    detail: str
    severity: str                # "high" | "medium" | "low"
    evidence_source: str         # "incident_record" | "ast_analysis" | "code_search" | "commit_history"


class SimilarChange(BaseModel):
    commit_hash: str
    date: str
    description: str
    outcome: str = ""            # what happened after this change


class RiskAssessment(BaseModel):
    risk_level: str              # "HIGH" | "MEDIUM" | "LOW"
    risk_factors: list[RiskFactor] = []
    similar_past_changes: list[SimilarChange] = []


# --- RAG ---

class CodeChunk(BaseModel):
    content: str
    file_path: str
    symbol_name: str
    symbol_type: str
    imports: list[str] = []
    calls: list[str] = []
    is_test: bool = False


class CommitRecord(BaseModel):
    commit_hash: str
    author: str
    date: str
    message: str
    changed_files: list[str] = []


class IncidentRecord(BaseModel):
    incident_id: str
    severity: str
    date: str
    title: str
    affected_files: list[str] = []
    root_cause: str = ""
    resolution: str = ""


# --- Agent State (for LangGraph) ---

class AgentState(BaseModel):
    """State passed between LangGraph stages."""
    diff_text: str
    repo_path: str

    # Stage outputs (populated as workflow progresses)
    change_manifest: ChangeManifest | None = None
    impact_map: ImpactMap | None = None
    risk_assessment: RiskAssessment | None = None
    report: str | None = None
