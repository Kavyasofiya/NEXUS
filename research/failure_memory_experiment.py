
import requests
import time
import csv
import os

API_URL = "http://127.0.0.1:8000/solve"

TASKS = [
    {
        "task": "Write a Python function named square that returns the square of a number.",
        "test_cases": [
            {"input": 4, "expected": 16},
            {"input": 5, "expected": 25},
            {"input": 10, "expected": 100}
        ]
    }
]

MODES = [
    ("verified_memory_only", False),
    ("verified_and_failure_memory", True)
]

results = []

print("NEXUS FAILURE MEMORY EXPERIMENT")
print("=" * 50)

# Three rounds for each experimental condition
for round_number in range(1, 4):

    for mode_name, use_failure_memory in MODES:

        for task_data in TASKS:

            payload = {
                "task": task_data["task"],
                "test_cases": task_data["test_cases"],
                "use_failure_memory": use_failure_memory
            }

            print(f"\nRound: {round_number}")
            print(f"Mode: {mode_name}")

            start_time = time.perf_counter()

            try:
                response = requests.post(
                    API_URL,
                    json=payload,
                    timeout=300
                )

                response.raise_for_status()
                data = response.json()

                elapsed_time = time.perf_counter() - start_time

                test_results = data.get("test_results") or {}

                passed = test_results.get("passed", 0)
                total = test_results.get("total_tests", 0)

                success = (
                    test_results.get("success") is True
                    and total > 0
                    and passed == total
                )

                record = {
                    "round": round_number,
                    "mode": mode_name,
                    "task": task_data["task"],
                    "passed_tests": passed,
                    "total_tests": total,
                    "success": success,
                    "response_time_seconds": round(elapsed_time, 2),
                    "retrieved_memories": data.get(
                        "retrieved_memory_count", 0
                    ),
                    "retrieved_failures": data.get(
                        "retrieved_failure_count", 0
                    )
                }

                results.append(record)

                print("Passed:", passed, "/", total)
                print("Failure memories retrieved:",
                      record["retrieved_failures"])
                print("Response time:", elapsed_time)

            except requests.exceptions.RequestException as error:
                print("Request failed:", error)

# Save experiment results
output_path = os.path.join(
    os.path.dirname(__file__),
    "failure_memory_results.csv"
)

if results:
    with open(output_path, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(
            file,
            fieldnames=results[0].keys()
        )
        writer.writeheader()
        writer.writerows(results)

    print("\nEXPERIMENT COMPLETED")
    print("Results saved to:", output_path)

    for mode_name, _ in MODES:
        mode_results = [
            item for item in results
            if item["mode"] == mode_name
        ]

        if mode_results:
            accuracy = (
                sum(item["success"] for item in mode_results)
                / len(mode_results)
            ) * 100

            average_time = sum(
                item["response_time_seconds"]
                for item in mode_results
            ) / len(mode_results)

            print(f"\n{mode_name}")
            print("Accuracy:", accuracy, "%")
            print("Average response time:", round(average_time, 2))
