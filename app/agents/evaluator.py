from google import genai

from app.config import (
    GEMINI_API_KEY,
    MODEL_NAME,
)

from app.evaluation.schemas import (
    EvaluationResult,
)

from app.evaluation.rubric import (
    RUBRIC,
)


client = genai.Client(
    api_key=GEMINI_API_KEY
)


def evaluate_lesson(
    topic: str,
    lesson: str,
) -> EvaluationResult:

    rubric_text = "\n".join(
        [
            (
                f"{item['id']}: "
                f"{item['description']}"
            )
            for item in RUBRIC
        ]
    )

    prompt = f"""
You are a strict educational quality evaluator.

Your job is to decide whether a beginner
lesson is good enough to ship.

There is NO partial credit.

Every criterion must be PASS or FAIL.

If even ONE criterion fails,
overall_pass MUST be false.

RUBRIC:

{rubric_text}

TOPIC:

{topic}

LESSON:

{lesson}

Evaluate the actual lesson.

For every criterion:

- Return PASS or FAIL.
- Give a specific reason.
- Do not assume missing information exists.
- Be strict.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config={
            "response_mime_type": "application/json",
            "response_schema": EvaluationResult,
        },
    )

    return response.parsed