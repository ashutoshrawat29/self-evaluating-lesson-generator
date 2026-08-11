from google import genai

from app.config import (
    GEMINI_API_KEY,
    MODEL_NAME,
)

from app.memory.database import (
    format_memory,
)


client = genai.Client(
    api_key=GEMINI_API_KEY
)


REGENERATOR_SYSTEM_PROMPT = """
You are an expert educational content editor.

A previously generated beginner lesson
failed an independent quality evaluation.

Rewrite the complete lesson to fix
EVERY identified problem.

Target learner:

- 12th-grade graduate from India
- Limited English vocabulary
- Non-English-medium background
- Starting from zero

Original lesson:

{lesson}

Evaluator feedback:

{feedback}

Previous memory:

{memory}

Rules:

- Fix every failed criterion.
- Preserve things that already worked.
- Use simple language.
- Explain technical terms.
- Include examples.
- Maintain logical teaching flow.
- Explain what, why and how.
- Return the COMPLETE revised lesson.
- Do not discuss the evaluation process.
- Return only the lesson.
"""


def regenerate_lesson(
    lesson: str,
    feedback: str,
    memory: list,
) -> str:

    memory_text = format_memory(
        memory
    )

    prompt = (
        REGENERATOR_SYSTEM_PROMPT.format(
            lesson=lesson,
            feedback=feedback,
            memory=memory_text,
        )
    )

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    return response.text