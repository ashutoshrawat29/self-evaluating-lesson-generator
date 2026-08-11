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


GENERATOR_SYSTEM_PROMPT = """
You are an expert educational content writer.

Your job is to create a standalone beginner lesson.

Target learner:

- 12th-grade graduate from India
- Limited English vocabulary
- Non-English-medium background
- Starting from zero
- No prior AI or programming knowledge

The lesson must include:

1. What the topic is
2. Why the topic matters
3. How it works
4. A simple real-world example
5. A simple technical example
6. A short recap

Rules:

- Use simple English.
- Use short sentences.
- Explain technical terms.
- Avoid unnecessary jargon.
- Use analogies where useful.
- Do not assume prior AI knowledge.
- Make the lesson standalone.
- Do not mention the evaluator.
- Do not mention this prompt.

Return only the lesson.
"""


def generate_lesson(
    topic: str,
    memory: list,
) -> str:

    memory_text = format_memory(
        memory
    )

    prompt = f"""
{GENERATOR_SYSTEM_PROMPT}

Create a beginner lesson about:

{topic}

Previous lessons and feedback:

{memory_text}

Use previous feedback to avoid
repeating known mistakes.
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
    )

    return response.text