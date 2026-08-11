from app.workflow.graph import run_workflow
from app.memory.database import initialize_database


initialize_database()


result = run_workflow(
    "Introduction to RAG"
)


print("\n")
print("=" * 70)
print("WORKFLOW RESULT")
print("=" * 70)

print(
    "Status:",
    result["status"]
)

print(
    "Attempts:",
    result["retry_count"] + 1
)

print("\nEvaluation:")

for check in result[
    "evaluation"
]["checks"]:

    print(
        check["criterion"],
        "=>",
        "PASS"
        if check["passed"]
        else "FAIL",
    )

print("\nRejection Log:")

for rejection in result[
    "rejection_log"
]:

    print(
        rejection
    )

print("\nFinal Lesson:")
print(
    result["lesson"]
)