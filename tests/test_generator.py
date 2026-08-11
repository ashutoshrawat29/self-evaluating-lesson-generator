from app.agents.generator import generate_lesson
from app.memory.database import initialize_database


initialize_database()

lesson = generate_lesson(
    topic="Introduction to RAG",
    memory=[],
)

print(lesson)