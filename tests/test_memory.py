from app.memory.database import (
    initialize_database,
    save_failure,
    save_successful_fix,
    get_memory,
)


def test_memory():

    initialize_database()

    save_failure(
        topic="Introduction to RAG",
        attempt=1,
        failed_checks=[
            "beginner_friendly"
        ],
        reasons=[
            "Embedding was not explained."
        ],
        changes_required=[
            "Explain embedding simply."
        ],
    )

    save_successful_fix(
        topic="Introduction to RAG",
        failed_checks=[
            "beginner_friendly"
        ],
        successful_changes=[
            "Added simple embedding explanation."
        ],
    )

    memory = get_memory(
        "Introduction to RAG"
    )

    print(memory)


if __name__ == "__main__":
    test_memory()