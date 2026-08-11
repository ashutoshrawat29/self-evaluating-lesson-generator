from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.workflow.graph import run_workflow


router = APIRouter(
    prefix="/api/v1/lessons",
    tags=["Lessons"],
)


class LessonRequest(BaseModel):

    topic: str = Field(
        ...,
        min_length=2,
        max_length=200,
    )


@router.post("/generate")
def generate_lesson_endpoint(
    request: LessonRequest,
):

    try:

        result = run_workflow(
            request.topic
        )

        return {
            "status":
                result["status"],

            "topic":
                result["topic"],

            "attempts":
                result["retry_count"] + 1,

            "lesson":
                result["lesson"],

            "evaluation":
                result["evaluation"],

            "rejection_log":
                result["rejection_log"],
        }

    except Exception as exc:

        raise HTTPException(
            status_code=500,
            detail=str(exc),
        )