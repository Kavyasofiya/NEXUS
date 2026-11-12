import csv
import random
import os
import time
import re

from ollama_client import generate_response
from verifier import verify_code
from test_runner import run_tests
from memory_store import retrieve_similar_experiences


# =====================================================
# 1. EXPERIMENT TASKS
# =====================================================

TASKS = [
    {
        "category": "Arrays",
        "task": "Write a Python function named find_highest_number that returns the largest number in a list.",
        "test_cases": [
            {"input": [4, 8, 2, 6], "expected": 8},
            {"input": [10, 30, 20], "expected": 30},
            {"input": [-5, -2, -9], "expected": -2}
        ]
    },
    {
        "category": "Arrays",
        "task": "Write a Python function named second_largest that returns the second largest distinct number in a list. Return None if fewer than two distinct numbers exist.",
        "test_cases": [
            {"input": [4, 1, 7, 7, 3], "expected": 4},
            {"input": [-5, -1, -3], "expected": -3},
            {"input": [10, 10], "expected": None},
            {"input": [], "expected": None}
        ]
    },
    {
        "category": "Strings",
        "task": "Write a Python function named reverse_string that returns a string in reverse order.",
        "test_cases": [
            {"input": "nexus", "expected": "suxen"},
            {"input": "hello", "expected": "olleh"},
            {"input": "a", "expected": "a"},
            {"input": "", "expected": ""}
        ]
    },
    {
        "category": "Strings",
        "task": "Write a Python function named is_palindrome that returns True if a string reads the same forward and backward, otherwise False. Compare the string exactly without changing its case.",
        "test_cases": [
            {"input": "level", "expected": True},
            {"input": "nexus", "expected": False},
            {"input": "madam", "expected": True},
            {"input": "Level", "expected": False}
        ]
    },
    {
        "category": "Mathematics",
        "task": "Write a Python function named factorial that returns the factorial of a non-negative integer. Use 1 as the factorial of zero.",
        "test_cases": [
            {"input": 5, "expected": 120},
            {"input": 0, "expected": 1},
            {"input": 1, "expected": 1},
            {"input": 4, "expected": 24}
        ]
    },
    {
        "category": "Mathematics",
        "task": "Write a Python function named is_prime that returns True if an integer is prime and False otherwise. Integers less than 2 are not prime.",
        "test_cases": [
            {"input": 2, "expected": True},
            {"input": 9, "expected": False},
            {"input": 17, "expected": True},
            {"input": 1, "expected": False},
            {"input": 0, "expected": False}
        ]
    }
]


# =====================================================
# 2. ORDINARY MEMORY
# =====================================================

def get_words(text):
    return set(re.findall(r"[a-zA-Z_]+", text.lower()))


def retrieve_ordinary_memories(task, ordinary_memory, limit=3):

    task_words = get_words(task)

    scored_memories = []

    for memory in ordinary_memory:

        memory_words = get_words(memory["task"])

        common_words = task_words.intersection(memory_words)

        score = (
            len(common_words) / len(task_words)
            if task_words else 0
        )

        if score >= 0.15:
            scored_memories.append({
                "task": memory["task"],
                "code": memory["code"],
                "similarity_score": round(score, 2)
            })

    scored_memories.sort(
        key=lambda item: item["similarity_score"],
        reverse=True
    )

    return scored_memories[:limit]


# =====================================================
# 3. RUN ONE EXPERIMENT
# =====================================================

def run_experiment(task_data, memory_mode, ordinary_memory):

    task = task_data["task"]
    test_cases = task_data["test_cases"]

    start_time = time.perf_counter()

    memories = []

    correction_attempted = False
    correction_succeeded = False
    recovery_method = "None"

    # MEMORY RETRIEVAL

    if memory_mode == "ORDINARY":

        memories = retrieve_ordinary_memories(
            task,
            ordinary_memory
        )

    elif memory_mode == "NEXUS":

        retrieved = retrieve_similar_experiences(task)

        memories = [
            memory for memory in retrieved
            if memory.get("similarity_score", 0) >= 0.3
        ]

    # BUILD MEMORY CONTEXT

    memory_context = ""

    for memory in memories:

        memory_context += f"""
Previous Task: {memory['task']}
Previous Code: {memory['code']}
Similarity: {memory.get('similarity_score', 'N/A')}
"""

        if memory_mode == "NEXUS":
            memory_context += (
                f"Test Evidence: "
                f"{memory.get('passed_tests', 0)}/"
                f"{memory.get('total_tests', 0)} tests passed.\n"
            )
        else:
            memory_context += (
                "Evidence Status: UNVERIFIED. "
                "Check correctness independently.\n"
            )

    if not memory_context:
        memory_context = "No relevant previous experience supplied."

    # GENERATE SOLUTION

    prompt = f"""
You are a Python programming assistant.

Previous experiences:
{memory_context}

Current task:
{task}

Instructions:
1. Generate exactly one Python function.
2. Use the exact function name requested.
3. Do not include example usage.
4. Do not include print statements.
5. Do not include imports.
6. Handle all specified edge cases.
7. Follow the task requirements exactly.
8. Return only one Python code block.
"""

    answer = generate_response(prompt)

    # SAVE ORDINARY MEMORY WITHOUT VALIDATION

    # This is deliberately unverified memory.
    # It is kept separate from the NEXUS SQLite database.

    if memory_mode == "ORDINARY":

        if answer and not answer.startswith("ERROR:"):

            ordinary_memory.append({
                "task": task,
                "code": answer
            })

    verification = {
        "verified": False,
        "message": "AI did not return a valid response.",
        "code": ""
    }

    test_results = None

    # VERIFY GENERATED CODE

    if not answer or answer.startswith("ERROR:"):

        verification["message"] = str(answer)

    else:

        verification = verify_code(answer)

        if verification["verified"]:

            # EXECUTE TESTS

            test_results = run_tests(
                verification["code"],
                test_cases
            )

            # ANALYZE FAILURES AND REQUEST CORRECTION

            if not test_results.get("success"):

                correction_attempted = True

                failed_cases = [
                    result
                    for result in test_results.get("results", [])
                    if not result.get("passed", False)
                ]

                correction_prompt = f"""
Your previous Python solution failed the test cases.

Original task:
{task}

Previous code:
{verification["code"]}

Failure evidence:
{failed_cases}

Analyze the actual failure and generate corrected code.

Requirements:
- Follow the original task exactly.
- Correct the root cause.
- Handle all failed test cases.
- Do not change expected behavior.
- Preserve case sensitivity when required.
- Do not use lower() or casefold() for case-sensitive comparison.
- Return exactly one Python function.
- Return only a Python code block.
"""

                corrected_answer = generate_response(
                    correction_prompt
                )

                if (
                    corrected_answer
                    and not corrected_answer.startswith("ERROR:")
                ):

                    corrected_verification = verify_code(
                        corrected_answer
                    )

                    if corrected_verification["verified"]:

                        corrected_results = run_tests(
                            corrected_verification["code"],
                            test_cases
                        )

                        if corrected_results.get("success"):

                            verification = corrected_verification
                            test_results = corrected_results

                            correction_succeeded = True
                            recovery_method = "AI correction"

                # RULE-BASED FALLBACK FOR PALINDROME

                if (
                    not correction_succeeded
                    and "is_palindrome" in task
                ):

                    fallback_code = """
def is_palindrome(text):
    return text == text[::-1]
"""

                    fallback_verification = verify_code(
                        fallback_code
                    )

                    if fallback_verification["verified"]:

                        fallback_results = run_tests(
                            fallback_verification["code"],
                            test_cases
                        )

                        if fallback_results.get("success"):

                            verification = fallback_verification
                            test_results = fallback_results

                            correction_succeeded = True
                            recovery_method = "Rule-based fallback"

    # CALCULATE RESULTS

    elapsed = round(
        time.perf_counter() - start_time,
        2
    )

    test_details = (
        test_results.get("results", [])
        if test_results else []
    )

    failed_cases = [
        result
        for result in test_details
        if not result.get("passed", False)
    ]

    success = (
        test_results is not None
        and test_results.get("success") is True
    )

    return {
        "success": success,
        "verified": verification["verified"],
        "verification_message": verification.get("message"),
        "passed": (
            test_results.get("passed", 0)
            if test_results else 0
        ),
        "total": (
            test_results.get("total_tests", 0)
            if test_results else 0
        ),
        "failed_cases": failed_cases,
        "memory_count": len(memories),
        "correction_attempted": correction_attempted,
        "correction_succeeded": correction_succeeded,
        "recovery_method": recovery_method,
        "time": elapsed
    }


# =====================================================
# 4. CALCULATE SUMMARY
# =====================================================

def calculate_summary(results):

    total_tasks = len(results)

    successful_tasks = sum(
        result["success"] for result in results
    )

    total_passed = sum(
        result["passed"] for result in results
    )

    total_tests = sum(
        result["total"] for result in results
    )

    average_time = (
        round(
            sum(result["time"] for result in results)
            / total_tasks,
            2
        )
        if total_tasks else 0
    )

    correction_attempts = sum(
        result["correction_attempted"]
        for result in results
    )

    successful_corrections = sum(
        result["correction_succeeded"]
        and result["recovery_method"] == "AI correction"
        for result in results
    )

    fallbacks = sum(
        result["recovery_method"] == "Rule-based fallback"
        for result in results
    )

    return {
        "successful_tasks": successful_tasks,
        "total_tasks": total_tasks,
        "passed_tests": total_passed,
        "total_tests": total_tests,
        "average_time": average_time,
        "correction_attempts": correction_attempts,
        "successful_ai_corrections": successful_corrections,
        "rule_based_fallbacks": fallbacks
    }


# =====================================================
# 5. PRINT RESULTS
# =====================================================

def print_summary(name, summary):

    print(f"\n{name}")
    print("=" * len(name))

    for key, value in summary.items():
        print(f"{key}: {value}")

    rate = (
        summary["successful_tasks"]
        / summary["total_tasks"] * 100
        if summary["total_tasks"] else 0
    )

    test_rate = (
        summary["passed_tests"]
        / summary["total_tests"] * 100
        if summary["total_tests"] else 0
    )

    print(f"Task success rate: {rate:.2f}%")
    print(f"Test pass rate: {test_rate:.2f}%")


def print_task_result(result):

    print({
        key: value
        for key, value in result.items()
        if key != "failed_cases"
    })


def print_failed_cases(results, name):

    print(f"\nFAILED CASES - {name}")
    print("-" * 40)

    found = False

    for index, result in enumerate(results, start=1):

        for failure in result["failed_cases"]:

            found = True

            print(f"\nTask {index}")
            print("Input:", failure.get("input"))
            print("Expected:", failure.get("expected"))
            print("Actual:", failure.get("actual"))
            print("Error:", failure.get("error", "None"))

    if not found:
        print("No failed test cases.")


# =====================================================
# 6. THREE-WAY COMPARATIVE EXPERIMENT
# =====================================================

def main():

    ROUND_COUNT = 5

    all_results = {
        "BASELINE": [],
        "ORDINARY MEMORY": [],
        "NEXUS VERIFIED MEMORY": []
    }

    csv_rows = []

    print("\nNEXUS FIVE-ROUND COMPARATIVE EXPERIMENT")
    print("=======================================")

    print("Total rounds:", ROUND_COUNT)
    print("Total tasks per round:", len(TASKS))

    for round_number in range(1, ROUND_COUNT + 1):

        print(f"\n\n========== ROUND {round_number} ==========")

        # Reset ordinary memory for each round
        ordinary_memory = []

        for task_number, task_data in enumerate(TASKS, start=1):

            print(f"\nTASK {task_number}: {task_data['category']}")
            print(task_data["task"])

            conditions = [
                ("BASELINE", "NONE"),
                ("ORDINARY MEMORY", "ORDINARY"),
                ("NEXUS VERIFIED MEMORY", "NEXUS")
            ]

            # Randomize experiment execution order
            random.shuffle(conditions)

            for condition_name, memory_mode in conditions:

                print(f"\nEXPERIMENT: {condition_name}")

                result = run_experiment(
                    task_data,
                    memory_mode,
                    ordinary_memory
                )

                all_results[condition_name].append(result)

                print_task_result(result)

                # Save individual task results
                csv_rows.append({
                    "round": round_number,
                    "task_number": task_number,
                    "category": task_data["category"],
                    "condition": condition_name,
                    "success": result["success"],
                    "verified": result["verified"],
                    "passed_tests": result["passed"],
                    "total_tests": result["total"],
                    "memory_count": result["memory_count"],
                    "correction_attempted": result["correction_attempted"],
                    "correction_succeeded": result["correction_succeeded"],
                    "recovery_method": result["recovery_method"],
                    "execution_time_seconds": result["time"]
                })

    # ==========================================
    # FINAL SUMMARIES
    # ==========================================

    print("\n\nFINAL FIVE-ROUND COMPARISON")
    print("===========================")

    for condition_name, results in all_results.items():

        summary = calculate_summary(results)

        print_summary(condition_name, summary)

    # ==========================================
    # SAVE CSV REPORT
    # ==========================================

    project_folder = os.path.dirname(
        os.path.dirname(os.path.abspath(__file__))
    )

    research_folder = os.path.join(
        project_folder,
        "research"
    )

    os.makedirs(research_folder, exist_ok=True)

    csv_path = os.path.join(
        research_folder,
        "experiment_results.csv"
    )

    fieldnames = list(csv_rows[0].keys())

    with open(
        csv_path,
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.DictWriter(
            file,
            fieldnames=fieldnames
        )

        writer.writeheader()
        writer.writerows(csv_rows)

    # ==========================================
    # MEMORY RETRIEVAL COMPARISON
    # ==========================================

    print("\nMEMORY RETRIEVAL COMPARISON")
    print("===========================")

    for condition_name, results in all_results.items():

        retrievals = sum(
            result["memory_count"]
            for result in results
        )

        print(f"{condition_name}: {retrievals}")

    # ==========================================
    # FINAL MESSAGE
    # ==========================================

    print("\nEXPERIMENT COMPLETED")
    print("====================")

    print("Total experiment records:", len(csv_rows))
    print("CSV report saved at:")
    print(csv_path)


if __name__ == "__main__":
    main()