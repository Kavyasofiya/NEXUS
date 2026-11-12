
import requests
import time
import csv
import os
import random

API_URL = "http://127.0.0.1:8000/solve"

TASKS = [
    {
        "task": "Write a Python function named square that returns the square of a number.",
        "test_cases": [
            {"input": 4, "expected": 16},
            {"input": 5, "expected": 25},
            {"input": 10, "expected": 100}
        ]
    },
    {
        "task": "Write a Python function named cube that returns the cube of a number.",
        "test_cases": [
            {"input": 2, "expected": 8},
            {"input": 3, "expected": 27},
            {"input": 4, "expected": 64}
        ]
    },
    {
        "task": "Write a Python function named is_even that returns True if a number is even.",
        "test_cases": [
            {"input": 2, "expected": True},
            {"input": 5, "expected": False},
            {"input": 10, "expected": True}
        ]
    },
    {
        "task": "Write a Python function named factorial that returns the factorial of a number.",
        "test_cases": [
            {"input": 3, "expected": 6},
            {"input": 5, "expected": 120},
            {"input": 0, "expected": 1}
        ]
    },
    {
        "task": "Write a Python function named reverse_string that reverses a string.",
        "test_cases": [
            {"input": "hello", "expected": "olleh"},
            {"input": "python", "expected": "nohtyp"},
            {"input": "abc", "expected": "cba"}
        ]
    },
    {
        "task": "Write a Python function named find_largest_number that returns the largest number in a list.",
        "test_cases": [
            {"input": [2, 8, 4], "expected": 8},
            {"input": [10, 3, 7], "expected": 10},
            {"input": [-5, -2, -9], "expected": -2}
        ]
    },
    {
        "task": "Write a Python function named sum_numbers that returns the sum of a list of numbers.",
        "test_cases": [
            {"input": [1, 2, 3], "expected": 6},
            {"input": [5, 5], "expected": 10},
            {"input": [0, 4, 6], "expected": 10}
        ]
    },
    {
        "task": "Write a Python function named count_vowels that counts vowels in a string.",
        "test_cases": [
            {"input": "hello", "expected": 2},
            {"input": "education", "expected": 5},
            {"input": "sky", "expected": 0}
        ]
    },
    {
        "task": "Write a Python function named is_palindrome that returns True if a string is a palindrome.",
        "test_cases": [
            {"input": "madam", "expected": True},
            {"input": "hello", "expected": False},
            {"input": "level", "expected": True}
        ]
    },
    {
        "task": "Write a Python function named fibonacci that returns the nth Fibonacci number, with fibonacci(0) equal to 0 and fibonacci(1) equal to 1.",
        "test_cases": [
            {"input": 0, "expected": 0},
            {"input": 1, "expected": 1},
            {"input": 6, "expected": 8}
        ]
    }
]

MODES = [
    ("verified_memory_only", False),
    ("verified_and_failure_memory", True)
]

results = []
random_generator = random.Random(42)

print("NEXUS CONTROLLED FAILURE MEMORY EXPERIMENT")
print("=" * 55)
print("Tasks:", len(TASKS))
print("Rounds: 5")
print("Conditions: 2")
print("Maximum runs: 100")

for round_number in range(1, 6):

    run_order = [
        (task, mode_name, use_failure_memory)
        for task in TASKS
        for mode_name, use_failure_memory in MODES
    ]

    random_generator.shuffle(run_order)

    for task_data, mode_name, use_failure_memory in run_order:

        payload = {
            "task": task_data["task"],
            "test_cases": task_data["test_cases"],
            "use_failure_memory": use_failure_memory,
            "save_memory": False
        }

        print("\n" + "-" * 55)
        print("Round:", round_number)
        print("Mode:", mode_name)
        print("Task:", task_data["task"])

        start_time = time.perf_counter()

        record = {
            "round": round_number,
            "mode": mode_name,
            "task": task_data["task"],
            "passed_tests": 0,
            "total_tests": len(task_data["test_cases"]),
            "success": False,
            "status": "INVALID_RUN",
            "response_time_seconds": None,
            "retrieved_memories": 0,
            "retrieved_failures": 0,
            "error": "",
            "response_preview": ""
        }

        try:
            response = requests.post(
                API_URL,
                json=payload,
                timeout=300
            )

            response.raise_for_status()

            record["response_preview"] = response.text[:2000]

            data = response.json()

            elapsed_time = time.perf_counter() - start_time
            test_results = data.get("test_results") or {}

            passed = test_results.get("passed", 0)
            total = test_results.get(
                "total_tests", 0
            )

            success = (
                test_results.get("success") is True
                and total > 0
                and passed == total
            )

            record.update({
                "passed_tests": passed,
                "total_tests": total,
                "success": success,
                "status": (
                    "SUCCESS" if success else "TEST_FAILURE"
                ),
                "response_time_seconds": round(
                    elapsed_time, 2
                ),
                "retrieved_memories": data.get(
                    "retrieved_memory_count", 0
                ),
                "retrieved_failures": data.get(
                    "retrieved_failure_count", 0
                )
            })

            if total == 0:
                record["status"] = "INVALID_RUN"
                print("INVALID RESPONSE:")
                print(response.text[:2000])

            print("Passed:", passed, "/", total)
            print(
                "Failure memories:",
                record["retrieved_failures"]
            )
            print("Success:", success)
            print("Time:", round(elapsed_time, 2), "seconds")

        except Exception as error:
            record["error"] = str(error)
            print("ERROR:", error)

        results.append(record)

        # Save progress after every run
        output_path = os.path.join(
            os.path.dirname(__file__),
            "controlled_failure_memory_results.csv"
        )

        with open(
            output_path,
            "w",
            newline="",
            encoding="utf-8"
        ) as file:
            writer = csv.DictWriter(
                file,
                fieldnames=results[0].keys()
            )
            writer.writeheader()
            writer.writerows(results)

print("\n" + "=" * 55)
print("EXPERIMENT COMPLETED")

for mode_name, _ in MODES:

    mode_results = [
        item for item in results
        if item["mode"] == mode_name
    ]

    valid_results = [
        item for item in mode_results
        if item["status"] in ("SUCCESS", "TEST_FAILURE")
    ]

    if not valid_results:
        print("\n", mode_name, ": No valid runs")
        continue

    accuracy = (
        sum(item["success"] for item in valid_results)
        / len(valid_results)
    ) * 100

    average_time = sum(
        item["response_time_seconds"]
        for item in valid_results
    ) / len(valid_results)

    print("\nCondition:", mode_name)
    print("Valid runs:", len(valid_results))
    print("Successful runs:", sum(
        item["success"] for item in valid_results
    ))
    print("Accuracy:", round(accuracy, 2), "%")
    print("Average response time:", round(average_time, 2), "seconds")

print("\nResults saved to:")
print(output_path)

