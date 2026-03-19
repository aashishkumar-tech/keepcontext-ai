"""Quality evaluation endpoint for retrieval and agent workflows."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from keepcontext_ai.evaluation import EvaluationDataset, QualityEvaluator
from keepcontext_ai.exceptions import EvaluationError

router = APIRouter(prefix="/api/v1/evaluation", tags=["evaluation"])


@router.post("/run")
async def run_evaluation(
    request: Request,
    body: EvaluationDataset,
) -> dict[str, Any]:
    """Run retrieval, groundedness, and agent quality evaluation."""
    retriever = request.app.state.retriever
    llm = getattr(request.app.state, "llm", None)

    if body.agent_cases and llm is None:
        raise EvaluationError(
            message="LLM service unavailable for agent evaluation",
            code="evaluation_dependency_error",
        )

    llm_generate = llm.generate if llm is not None else (lambda _: "")

    evaluator = QualityEvaluator(
        retriever=retriever,
        llm_generate=llm_generate,
    )
    report = evaluator.evaluate(body)

    return {"data": report.model_dump()}
