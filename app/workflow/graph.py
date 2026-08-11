from typing import Literal

from langgraph.graph import (
    StateGraph,
    START,
    END,
)

from app.workflow.state import LessonState

from app.config import MAX_RETRIES

from app.agents.generator import generate_lesson
from app.agents.evaluator import evaluate_lesson
from app.agents.regenerator import regenerate_lesson

from app.memory.database import (
    get_memory,
    save_failure,
    save_successful_fix,
)

def load_memory_node(
    state: LessonState,
):
    memory = get_memory(
        topic=state["topic"],
    )

    return {
        "memory": memory,
        "status": "MEMORY_LOADED",
    }

def generate_node(
    state: LessonState,
):

    lesson = generate_lesson(
        topic=state["topic"],
        memory=state["memory"],
    )

    return {
        "lesson": lesson,
        "status": "GENERATED",
    }

def run_prechecks(
    lesson: str,
):

    text = lesson.strip()
    lower = text.lower()

    checks = {}

    checks["not_empty"] = (
        len(text) > 100
    )

    word_count = len(text.split())

    checks["reasonable_length"] = (
        400 <= word_count <= 2000
    )

    checks["what_covered"] = any(
        phrase in lower
        for phrase in [
            "what is",
            "what does",
            "means",
            "refers to",
        ]
    )

    checks["why_covered"] = any(
        phrase in lower
        for phrase in [
            "why",
            "important",
            "useful",
            "matters",
        ]
    )

    checks["how_covered"] = any(
        phrase in lower
        for phrase in [
            "how it works",
            "how does",
            "steps",
            "process",
        ]
    )

    checks["example_present"] = any(
        phrase in lower
        for phrase in [
            "example",
            "imagine",
            "suppose",
            "for instance",
        ]
    )

    return checks


def precheck_node(
    state: LessonState,
):

    results = run_prechecks(
        state["lesson"]
    )

    return {
        "precheck_results": results,
        "status": "PRECHECKED",
    }

def evaluate_node(
    state: LessonState,
):

    evaluation = evaluate_lesson(
        topic=state["topic"],
        lesson=state["lesson"],
    )

    evaluation_dict = (
        evaluation.model_dump()
    )

    # Apply deterministic checks
    prechecks = state[
        "precheck_results"
    ]

    failed_prechecks = [
        name
        for name, passed
        in prechecks.items()
        if not passed
    ]

    if failed_prechecks:

        evaluation_dict[
            "overall_pass"
        ] = False

        evaluation_dict[
            "checks"
        ].append(
            {
                "criterion":
                    "deterministic_prechecks",

                "passed": False,

                "reason": (
                    "Failed checks: "
                    + ", ".join(
                        failed_prechecks
                    )
                ),
            }
        )

    return {
        "evaluation": evaluation_dict,
        "status": "EVALUATED",
    }

def route_after_evaluation(
    state: LessonState,
) -> Literal[
    "finalize",
    "log_failure",
]:

    evaluation = state[
        "evaluation"
    ]

    # Lesson passed
    if evaluation[
        "overall_pass"
    ]:
        return "finalize"

    # Failed but retries remain
    if (
        state["retry_count"]
        < state["max_retries"]
    ):
        return "log_failure"

    # Failed and no retries remain
    return "finalize"

def log_failure_node(
    state: LessonState,
):

    evaluation = state[
        "evaluation"
    ]

    failed_checks = [
        check["criterion"]
        for check
        in evaluation["checks"]
        if not check["passed"]
    ]

    reasons = [
        check["reason"]
        for check
        in evaluation["checks"]
        if not check["passed"]
    ]

    changes_required = [
        f"Fix: {reason}"
        for reason in reasons
    ]

    attempt = (
        state["retry_count"] + 1
    )

    rejection = {
        "attempt": attempt,

        "failed_checks":
            failed_checks,

        "reasons":
            reasons,

        "changes_required":
            changes_required,
    }

    # Persist it
    save_failure(
        topic=state["topic"],
        attempt=attempt,
        failed_checks=failed_checks,
        reasons=reasons,
        changes_required=changes_required,
    )

    return {
        "rejection_log":
            state["rejection_log"]
            + [rejection],

        "status":
            "FAILURE_LOGGED",
    }

def regenerate_node(
    state: LessonState,
):

    evaluation = state[
        "evaluation"
    ]

    failed_checks = [
        check
        for check
        in evaluation["checks"]
        if not check["passed"]
    ]

    feedback = "\n".join(
        [
            (
                f"- {check['criterion']}: "
                f"{check['reason']}"
            )
            for check
            in failed_checks
        ]
    )

    new_lesson = regenerate_lesson(
        lesson=state["lesson"],
        feedback=feedback,
        memory=state["memory"],
    )

    return {
        "lesson": new_lesson,

        "retry_count":
            state["retry_count"] + 1,

        "status":
            "REGENERATED",
    }


def finalize_node(
    state: LessonState,
):

    evaluation = state[
        "evaluation"
    ]

    if (
        evaluation
        and evaluation["overall_pass"]
        and state["rejection_log"]
    ):

        last_rejection = (
            state["rejection_log"][-1]
        )

        save_successful_fix(
            topic=state["topic"],

            failed_checks=(
                last_rejection[
                    "failed_checks"
                ]
            ),

            successful_changes=(
                last_rejection[
                    "changes_required"
                ]
            ),
        )

        return {
            "status": "PASSED"
        }

    if (
        evaluation
        and evaluation["overall_pass"]
    ):
        return {
            "status": "PASSED"
        }

    return {
        "status":
            "FAILED_AFTER_MAX_RETRIES"
    }


def build_graph():

    builder = StateGraph(
        LessonState
    )

    # Nodes

    builder.add_node(
        "load_memory",
        load_memory_node,
    )

    builder.add_node(
        "generate",
        generate_node,
    )

    builder.add_node(
        "precheck",
        precheck_node,
    )

    builder.add_node(
        "evaluate",
        evaluate_node,
    )

    builder.add_node(
        "log_failure",
        log_failure_node,
    )

    builder.add_node(
        "regenerate",
        regenerate_node,
    )

    builder.add_node(
        "finalize",
        finalize_node,
    )

    # START
    builder.add_edge(
        START,
        "load_memory",
    )

    # Memory → Generator
    builder.add_edge(
        "load_memory",
        "generate",
    )

    # Generator → Pre-check
    builder.add_edge(
        "generate",
        "precheck",
    )

    # Pre-check → Evaluator
    builder.add_edge(
        "precheck",
        "evaluate",
    )

    # Evaluator → Decision
    builder.add_conditional_edges(
        "evaluate",
        route_after_evaluation,
        {
            "finalize":
                "finalize",

            "log_failure":
                "log_failure",
        },
    )

    # Failure → Regeneration
    builder.add_edge(
        "log_failure",
        "regenerate",
    )

    # Regeneration → Pre-check
    builder.add_edge(
        "regenerate",
        "precheck",
    )

    # Finalize → END
    builder.add_edge(
        "finalize",
        END,
    )

    return builder.compile()


graph = build_graph()

def run_workflow(
    topic: str,
):

    initial_state: LessonState = {

        "topic":
            topic,

        "lesson":
            "",

        "evaluation":
            None,

        "rejection_log":
            [],

        "retry_count":
            0,

        "max_retries":
            MAX_RETRIES,

        "memory":
            [],

        "precheck_results":
            {},

        "status":
            "STARTED",
    }

    result = graph.invoke(
        initial_state,
        {
            "recursion_limit": 20
        },
    )

    return result