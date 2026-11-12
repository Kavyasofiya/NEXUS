
from failure_analyzer import analyze_failures

sample_results = {
    "success": False,
    "total_tests": 3,
    "passed": 1,
    "failed": 2,
    "results": [
        {
            "input": [3, 1, 4],
            "expected": 4,
            "actual": 4,
            "passed": True
        },
        {
            "input": [10, 20, 5],
            "expected": 20,
            "actual": 10,
            "passed": False
        },
        {
            "input": [-5, -2, -9],
            "expected": -2,
            "actual": None,
            "passed": False
        }
    ]
}

report = analyze_failures(sample_results)

print("\nNEXUS FAILURE ANALYSIS")
print("----------------------")
print(report)
