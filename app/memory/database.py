import json
import sqlite3
from typing import List, Dict, Any

from app.config import DATABASE_PATH


def get_connection():
    connection = sqlite3.connect(
        DATABASE_PATH
    )

    connection.row_factory = sqlite3.Row

    return connection


def initialize_database():
    connection = get_connection()

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS failures (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            attempt INTEGER NOT NULL,
            failed_checks TEXT NOT NULL,
            reasons TEXT NOT NULL,
            changes_required TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.execute(
        """
        CREATE TABLE IF NOT EXISTS successful_fixes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            topic TEXT NOT NULL,
            failed_checks TEXT NOT NULL,
            successful_changes TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    connection.commit()
    connection.close()

def save_failure(
    topic: str,
    attempt: int,
    failed_checks: List[str],
    reasons: List[str],
    changes_required: List[str],
):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO failures (
            topic,
            attempt,
            failed_checks,
            reasons,
            changes_required
        )
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            topic,
            attempt,
            json.dumps(failed_checks),
            json.dumps(reasons),
            json.dumps(changes_required),
        ),
    )

    connection.commit()
    connection.close()

def save_successful_fix(
    topic: str,
    failed_checks: List[str],
    successful_changes: List[str],
):
    connection = get_connection()

    connection.execute(
        """
        INSERT INTO successful_fixes (
            topic,
            failed_checks,
            successful_changes
        )
        VALUES (?, ?, ?)
        """,
        (
            topic,
            json.dumps(failed_checks),
            json.dumps(successful_changes),
        ),
    )

    connection.commit()
    connection.close()

def get_memory(
    topic: str,
    limit: int = 5,
) -> List[Dict[str, Any]]:

    connection = get_connection()

    failures = connection.execute(
        """
        SELECT
            topic,
            attempt,
            failed_checks,
            reasons,
            changes_required,
            created_at
        FROM failures
        WHERE topic = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (
            topic,
            limit,
        ),
    ).fetchall()

    successful_fixes = connection.execute(
        """
        SELECT
            topic,
            failed_checks,
            successful_changes,
            created_at
        FROM successful_fixes
        WHERE topic = ?
        ORDER BY created_at DESC
        LIMIT ?
        """,
        (
            topic,
            limit,
        ),
    ).fetchall()

    connection.close()

    result = []

    for row in failures:

        result.append(
            {
                "type": "failure",
                "topic": row["topic"],
                "attempt": row["attempt"],
                "failed_checks": json.loads(
                    row["failed_checks"]
                ),
                "reasons": json.loads(
                    row["reasons"]
                ),
                "changes_required": json.loads(
                    row["changes_required"]
                ),
                "created_at": row["created_at"],
            }
        )

    for row in successful_fixes:

        result.append(
            {
                "type": "successful_fix",
                "topic": row["topic"],
                "failed_checks": json.loads(
                    row["failed_checks"]
                ),
                "successful_changes": json.loads(
                    row["successful_changes"]
                ),
                "created_at": row["created_at"],
            }
        )

    return result

def format_memory(
    memory: List[Dict[str, Any]]
) -> str:

    if not memory:
        return (
            "No previous memory exists "
            "for this topic."
        )

    lines = []

    for item in memory:

        if item["type"] == "failure":

            lines.append(
                f"""
Previous failure:
- Failed checks: {item["failed_checks"]}
- Reasons: {item["reasons"]}
- Required changes: {item["changes_required"]}
"""
            )

        elif item["type"] == "successful_fix":

            lines.append(
                f"""
Previous successful correction:
- Failed checks: {item["failed_checks"]}
- Successful changes: {item["successful_changes"]}
"""
            )

    return "\n".join(lines)