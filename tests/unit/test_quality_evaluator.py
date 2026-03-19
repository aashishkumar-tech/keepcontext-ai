"""Unit tests for dataset-driven quality evaluator."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

from keepcontext_ai.evaluation.runner import QualityEvaluator
from keepcontext_ai.evaluation.schemas import EvaluationDataset
from keepcontext_ai.graph.schemas import Entity, GraphResult
from keepcontext_ai.memory.schemas import MemoryEntry, MemoryResult, MemoryType

_FIXTURE_PATH = Path(__file__).parent / "fixtures" / "quality_eval_dataset.json"


def _memory_result(memory_id: str, content: str) -> MemoryResult:
    return MemoryResult(
        entry=MemoryEntry(
            id=memory_id,
            content=content,
            memory_type=MemoryType.DECISION,
            created_at="2026-01-01T00:00:00+00:00",
        ),
        score=0.91,
    )


class _FakeWorkflow:
    def invoke(self, state: dict[str, object]) -> dict[str, object]:
        assert "goal" in state
        return {
            "review": {"approved": True},
            "iteration": 1,
            "code_outputs": [
                {
                    "filename": "auth.py",
                    "code": "def issue_auth_token():\n    return 'auth token'",
                }
            ],
        }


def _fake_workflow_builder(**_: object) -> _FakeWorkflow:
    return _FakeWorkflow()


class TestQualityEvaluator:
    """Tests for retrieval, groundedness, and agent quality evaluation."""

    def test_evaluate_dataset(self) -> None:
        dataset = EvaluationDataset.model_validate_json(_FIXTURE_PATH.read_text())

        retriever = MagicMock()
        retriever.query.return_value = [
            _memory_result("mem-auth-1", "Auth uses access token"),
            _memory_result("mem-logging-1", "Logs include request id"),
            _memory_result("mem-auth-2", "Auth refresh token flow"),
        ]
        retriever.query_enriched.return_value = MagicMock(
            memory_results=[_memory_result("mem-auth-1", "Auth token validation")],
            graph_context=GraphResult(
                entities=[Entity(name="AuthService", entity_type="Service")],
                relationships=[],
            ),
            llm_response="Auth token validation happens in AuthService",
        )

        evaluator = QualityEvaluator(
            retriever=retriever,
            llm_generate=lambda prompt: prompt,
            workflow_builder=_fake_workflow_builder,
        )

        report = evaluator.evaluate(dataset)

        assert len(report.retrieval_scores) == 1
        assert len(report.groundedness_scores) == 1
        assert len(report.agent_scores) == 1
        assert report.summary.retrieval_precision_at_k > 0.0
        assert report.summary.retrieval_recall_at_k > 0.0
        assert report.summary.retrieval_mrr > 0.0
        assert report.summary.answer_groundedness > 0.0
        assert report.summary.agent_task_success_rate == 1.0

    def test_empty_dataset_yields_zero_summary(self) -> None:
        retriever = MagicMock()
        evaluator = QualityEvaluator(
            retriever=retriever,
            llm_generate=lambda prompt: prompt,
            workflow_builder=_fake_workflow_builder,
        )

        report = evaluator.evaluate(EvaluationDataset())

        assert report.summary.retrieval_precision_at_k == 0.0
        assert report.summary.retrieval_recall_at_k == 0.0
        assert report.summary.retrieval_mrr == 0.0
        assert report.summary.answer_groundedness == 0.0
        assert report.summary.agent_task_success_rate == 0.0
