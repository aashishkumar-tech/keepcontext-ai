"""Schemas for retrieval and agent quality evaluation."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field

from keepcontext_ai.memory.schemas import MemoryType


class RetrievalEvalCase(BaseModel):
    """A single retrieval evaluation case with expected memory IDs."""

    model_config = ConfigDict(frozen=True)

    case_id: str = Field(..., min_length=1, max_length=100)
    query: str = Field(..., min_length=1, max_length=5000)
    expected_memory_ids: list[str] = Field(default_factory=list)
    top_k: int = Field(default=5, ge=1, le=50)
    memory_type: MemoryType | None = Field(default=None)


class GroundednessEvalCase(BaseModel):
    """A single LLM groundedness evaluation case."""

    model_config = ConfigDict(frozen=True)

    case_id: str = Field(..., min_length=1, max_length=100)
    query: str = Field(..., min_length=1, max_length=5000)
    top_k: int = Field(default=5, ge=1, le=50)
    memory_type: MemoryType | None = Field(default=None)
    entity_name: str | None = Field(default=None)


class AgentEvalCase(BaseModel):
    """A single agent workflow case with success expectations."""

    model_config = ConfigDict(frozen=True)

    case_id: str = Field(..., min_length=1, max_length=100)
    goal: str = Field(..., min_length=1, max_length=5000)
    required_terms: list[str] = Field(default_factory=list)
    max_iterations: int = Field(default=3, ge=1, le=10)
    require_approval: bool = Field(default=True)


class EvaluationDataset(BaseModel):
    """Full dataset for quality evaluation."""

    model_config = ConfigDict(frozen=True)

    retrieval_cases: list[RetrievalEvalCase] = Field(default_factory=list)
    groundedness_cases: list[GroundednessEvalCase] = Field(default_factory=list)
    agent_cases: list[AgentEvalCase] = Field(default_factory=list)


class RetrievalCaseScore(BaseModel):
    """Metrics for one retrieval case."""

    model_config = ConfigDict(frozen=True)

    case_id: str
    retrieved_memory_ids: list[str]
    precision_at_k: float = Field(ge=0.0, le=1.0)
    recall_at_k: float = Field(ge=0.0, le=1.0)
    reciprocal_rank: float = Field(ge=0.0, le=1.0)


class GroundednessCaseScore(BaseModel):
    """Metrics for one groundedness case."""

    model_config = ConfigDict(frozen=True)

    case_id: str
    groundedness_score: float = Field(ge=0.0, le=1.0)
    llm_response: str | None = Field(default=None)


class AgentCaseScore(BaseModel):
    """Metrics for one agent workflow case."""

    model_config = ConfigDict(frozen=True)

    case_id: str
    approved: bool
    iterations_used: int = Field(ge=0)
    matched_required_terms: int = Field(ge=0)
    total_required_terms: int = Field(ge=0)
    task_success: bool


class EvaluationSummary(BaseModel):
    """Aggregate quality metrics across all evaluated cases."""

    model_config = ConfigDict(frozen=True)

    retrieval_precision_at_k: float = Field(default=0.0, ge=0.0, le=1.0)
    retrieval_recall_at_k: float = Field(default=0.0, ge=0.0, le=1.0)
    retrieval_mrr: float = Field(default=0.0, ge=0.0, le=1.0)
    answer_groundedness: float = Field(default=0.0, ge=0.0, le=1.0)
    agent_task_success_rate: float = Field(default=0.0, ge=0.0, le=1.0)


class EvaluationReport(BaseModel):
    """Final report for retrieval + groundedness + agent evaluation."""

    model_config = ConfigDict(frozen=True)

    summary: EvaluationSummary
    retrieval_scores: list[RetrievalCaseScore] = Field(default_factory=list)
    groundedness_scores: list[GroundednessCaseScore] = Field(default_factory=list)
    agent_scores: list[AgentCaseScore] = Field(default_factory=list)
