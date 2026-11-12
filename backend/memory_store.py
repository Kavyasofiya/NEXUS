
import sqlite3
import json
from pathlib import Path
from datetime import datetime, timezone


# ==========================================
# DATABASE CONFIGURATION
# ==========================================

PROJECT_DIR = Path(__file__).resolve().parent.parent
DATABASE_DIR = PROJECT_DIR / "database"
DATABASE_PATH = DATABASE_DIR / "nexus_memory.db"


def get_connection():
    DATABASE_DIR.mkdir(parents=True, exist_ok=True)
    return sqlite3.connect(DATABASE_PATH)


# ==========================================
# INITIALIZE MEMORY DATABASE
# ==========================================

def initialize_memory():

    connection = get_connection()
    cursor = connection.cursor()

    # Store successfully verified experiences
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS verified_experiences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            code TEXT NOT NULL,
            test_cases TEXT NOT NULL,
            passed_tests INTEGER NOT NULL,
            total_tests INTEGER NOT NULL,
            evidence_summary TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    # Store failed experiences separately
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS failure_experiences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            task TEXT NOT NULL,
            failure_type TEXT NOT NULL,
            input_data TEXT,
            expected_output TEXT,
            actual_output TEXT,
            evidence TEXT NOT NULL,
            created_at TEXT NOT NULL
        )
    """)

    connection.commit()
    connection.close()

    print("NEXUS memory database initialized.")
    print("Verified and failure memory tables are ready.")


# ==========================================
# SAVE VERIFIED EXPERIENCE
# ==========================================

def save_verified_experience(
    task,
    code,
    test_cases,
    passed_tests,
    total_tests
):

    # Reject incomplete or failed experiences
    if total_tests <= 0 or passed_tests != total_tests:
        return False

    connection = get_connection()
    cursor = connection.cursor()

    # Prevent duplicate records
    cursor.execute("""
        SELECT id
        FROM verified_experiences
        WHERE task = ? AND code = ?
        LIMIT 1
    """, (task, code))

    existing_record = cursor.fetchone()

    if existing_record:
        connection.close()
        print("Duplicate experience detected. Not saved.")
        return False

    cursor.execute("""
        INSERT INTO verified_experiences (
            task,
            code,
            test_cases,
            passed_tests,
            total_tests,
            evidence_summary,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        task,
        code,
        json.dumps(test_cases),
        passed_tests,
        total_tests,
        "All supplied test cases passed.",
        datetime.now(timezone.utc).isoformat()
    ))

    connection.commit()
    connection.close()

    return True


# ==========================================
# NORMALIZE TASK FOR RETRIEVAL
# ==========================================

def normalize_task(task):

    synonyms = {
        "maximum": "largest",
        "max": "largest",
        "maximums": "largest",
        "numbers": "number",
        "array": "list",
        "elements": "element",
        "values": "number",
        "find": "get",
        "obtain": "get",
        "is_even": "even",
        "check_even": "even",
        "iseven": "even",
        "is_odd": "odd",
        "check_odd": "odd",
        "isodd": "odd",
        "reverse": "reversed",
        "reverses": "reversed",
        "reversing": "reversed"
    }

    stop_words = {
        "the", "a", "an", "to", "in", "of",
        "and", "or", "write", "create", "function",
        "python", "program", "that", "returns",
        "using", "from", "for", "on", "named",
        "number", "numbers", "integer", "integers",
        "value", "values", "list", "array",
        "string", "strings", "takes"
    }

    words = set()

    for word in task.lower().split():

        word = word.strip(".,!?()[]{}")

        if word in stop_words:
            continue

        word = synonyms.get(word, word)

        words.add(word)

    return words


# ==========================================
# RETRIEVE VERIFIED EXPERIENCES
# ==========================================

def retrieve_similar_experiences(task, limit=3):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            task,
            code,
            passed_tests,
            total_tests,
            evidence_summary
        FROM verified_experiences
        WHERE passed_tests = total_tests
        AND total_tests > 0
        ORDER BY id DESC
    """)

    records = cursor.fetchall()
    connection.close()

    query_words = normalize_task(task)
    matches = []

    for record in records:

        old_words = normalize_task(record[1])

        common_words = query_words.intersection(old_words)

        if not common_words:
            continue

        score = len(common_words) / max(len(query_words), 1)

        matches.append({
            "memory_id": record[0],
            "task": record[1],
            "code": record[2],
            "passed_tests": record[3],
            "total_tests": record[4],
            "evidence": record[5],
            "similarity_score": round(score, 2)
        })

    matches.sort(
        key=lambda item: item["similarity_score"],
        reverse=True
    )

    MIN_SIMILARITY = 0.50

    relevant_matches = [
        item for item in matches
        if item["similarity_score"] >= MIN_SIMILARITY
    ]

    return relevant_matches[:limit]


# ==========================================
# SAVE FAILURE EXPERIENCE
# ==========================================

def save_failure_experience(
    task,
    failure_type,
    input_data,
    expected_output,
    actual_output,
    evidence
):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        INSERT INTO failure_experiences (
            task,
            failure_type,
            input_data,
            expected_output,
            actual_output,
            evidence,
            created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        task,
        failure_type,
        json.dumps(input_data),
        json.dumps(expected_output),
        json.dumps(actual_output),
        str(evidence),
        datetime.now(timezone.utc).isoformat()
    ))

    connection.commit()
    connection.close()

    return True


# ==========================================
# RETRIEVE SIMILAR FAILURE EXPERIENCES
# ==========================================

def retrieve_similar_failures(task, limit=3):

    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT
            id,
            task,
            failure_type,
            input_data,
            expected_output,
            actual_output,
            evidence
        FROM failure_experiences
        ORDER BY id DESC
    """)

    records = cursor.fetchall()
    connection.close()

    query_words = normalize_task(task)
    matches = []

    for record in records:

        old_words = normalize_task(record[1])

        common_words = query_words.intersection(old_words)

        if not common_words:
            continue

        score = len(common_words) / max(len(query_words), 1)

        if score >= 0.50:

            matches.append({
                "failure_id": record[0],
                "task": record[1],
                "failure_type": record[2],
                "input": json.loads(record[3]),
                "expected": json.loads(record[4]),
                "actual": json.loads(record[5]),
                "evidence": record[6],
                "similarity_score": round(score, 2)
            })

    matches.sort(
        key=lambda item: item["similarity_score"],
        reverse=True
    )

    return matches[:limit]


# ==========================================
# INITIALIZE DATABASE WHEN RUN DIRECTLY
# ==========================================

if __name__ == "__main__":
    initialize_memory()
