"""Dataset-driven quality evaluator for retrieval and agent workflows."""

from __future__ import annotations

from typing import Any

from keepcontext_ai.agents.workflow import build_workflow
from keepcontext_ai.context.retrieval import ContextRetriever
from keepcontext_ai.evaluation.metrics import (
    groundedness_score,
    precision_at_k,
    recall_at_k,
    reciprocal_rank,
)
from keepcontext_ai.evaluation.schemas import (
    AgentCaseScore,
    EvaluationDataset,
    EvaluationReport,
    EvaluationSummary,
    GroundednessCaseScore,
    RetrievalCaseScore,
)
from keepcontext_ai.exceptions import EvaluationError
from keepcontext_ai.memory.schemas import MemoryQuery


class QualityEvaluator:
    """Runs quality evaluations and aggregates score metrics."""

    def __init__(
        self,
        retriever: ContextRetriever,
        llm_generate: Any,
        workflow_builder: Any = build_workflow,
    ) -> None:
        """Initialize the evaluator with retrieval and workflow dependencies."""
        self._retriever = retriever
        self._llm_generate = llm_generate
        self._workflow_builder = workflow_builder

    def evaluate(self, dataset: EvaluationDataset) -> EvaluationReport:
        """Run all available evaluation suites and return an aggregate report."""
        retrieval_scores = self._evaluate_retrieval(dataset)
        groundedness_scores = self._evaluate_groundedness(dataset)
        agent_scores = self._evaluate_agent(dataset)

        summary = EvaluationSummary(
            retrieval_precision_at_k=_mean(
                [score.precision_at_k for score in retrieval_scores]
            ),
            retrieval_recall_at_k=_mean(
                [score.recall_at_k for score in retrieval_scores]
            ),
            retrieval_mrr=_mean([score.reciprocal_rank for score in retrieval_scores]),
            answer_groundedness=_mean(
                [score.groundedness_score for score in groundedness_scores]
            ),
            agent_task_success_rate=_mean(
                [1.0 if score.task_success else 0.0 for score in agent_scores]
            ),
        )

        return EvaluationReport(
            summary=summary,
            retrieval_scores=retrieval_scores,
            groundedness_scores=groundedness_scores,
            agent_scores=agent_scores,
        )

    def _evaluate_retrieval(
        self, dataset: EvaluationDataset
    ) -> list[RetrievalCaseScore]:
        scores: list[RetrievalCaseScore] = []

        for case in dataset.retrieval_cases:
            query = MemoryQuery(
                query=case.query,
                top_k=case.top_k,
                memory_type=case.memory_type,
            )
            try:
                results = self._retriever.query(query)
            except Exception as exc:
                raise EvaluationError(
                    message=f"Retrieval evaluation failed for case '{case.case_id}'",
                    code="evaluation_retrieval_error",
                ) from exc

            retrieved_ids = [result.entry.id for result in results]
            relevant_ids = set(case.expected_memory_ids)

            scores.append(
                RetrievalCaseScore(
                    case_id=case.case_id,
                    retrieved_memory_ids=retrieved_ids,
                    precision_at_k=precision_at_k(
                        retrieved_ids, relevant_ids, case.top_k
                    ),
                    recall_at_k=recall_at_k(retrieved_ids, relevant_ids, case.top_k),
                    reciprocal_rank=reciprocal_rank(retrieved_ids, relevant_ids),
                )
            )

        return scores

    def _evaluate_groundedness(
        self, dataset: EvaluationDataset
    ) -> list[GroundednessCaseScore]:
        scores: list[GroundednessCaseScore] = []

        for case in dataset.groundedness_cases:
            query = MemoryQuery(
                query=case.query,
                top_k=case.top_k,
                memory_type=case.memory_type,
            )
            try:
                result = self._retriever.query_enriched(
                    request=query,
                    entity_name=case.entity_name,
                    use_llm=True,
                )
            except Exception as exc:
                raise EvaluationError(
                    message=f"Groundedness evaluation failed for case '{case.case_id}'",
                    code="evaluation_groundedness_error",
                ) from exc

            memory_text = " ".join(
                memory.entry.content for memory in result.memory_results
            )
            entity_text = " ".join(
                entity.name for entity in result.graph_context.entities
            )
            relationship_text = " ".join(
                f"{rel.source} {rel.relationship_type.value} {rel.target}"
                for rel in result.graph_context.relationships
            )
            evidence_text = " ".join(
                [memory_text, entity_text, relationship_text]
            ).strip()

            scores.append(
                GroundednessCaseScore(
                    case_id=case.case_id,
                    groundedness_score=groundedness_score(
                        result.llm_response,
                        evidence_text,
                    ),
                    llm_response=result.llm_response,
                )
            )

        return scores

    def _evaluate_agent(self, dataset: EvaluationDataset) -> list[AgentCaseScore]:
        if not dataset.agent_cases:
            return []

        try:
            workflow = self._workflow_builder(
                retriever=self._retriever,
                llm_generate=self._llm_generate,
            )
        except Exception as exc:
            raise EvaluationError(
                message="Failed to initialize agent workflow for evaluation",
                code="evaluation_agent_init_error",
            ) from exc

        scores: list[AgentCaseScore] = []
        for case in dataset.agent_cases:
            try:
                result = workflow.invoke(
                    {
                        "goal": case.goal,
                        "max_iterations": case.max_iterations,
                        "iteration": 0,
                    }
                )
            except Exception as exc:
                raise EvaluationError(
                    message=f"Agent evaluation failed for case '{case.case_id}'",
                    code="evaluation_agent_run_error",
                ) from exc

            approved = bool(result.get("review", {}).get("approved", False))
            code_blob = "\n".join(
                output.get("code", "")
                for output in result.get("code_outputs", [])
                if isinstance(output, dict)
            ).lower()

            matched_required_terms = sum(
                1 for term in case.required_terms if term.lower() in code_blob
            )
            terms_ok = matched_required_terms == len(case.required_terms)
            approval_ok = approved if case.require_approval else True

            scores.append(
                AgentCaseScore(
                    case_id=case.case_id,
                    approved=approved,
                    iterations_used=int(result.get("iteration", 0)),
                    matched_required_terms=matched_required_terms,
                    total_required_terms=len(case.required_terms),
                    task_success=terms_ok and approval_ok,
                )
            )

        return scores


def _mean(values: list[float]) -> float:
    """Return the arithmetic mean or 0.0 when the input is empty."""
    if not values:
        return 0.0
    return sum(values) / len(values)
