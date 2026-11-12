
from test_runner import run_tests

# Sample AI-generated function
code = """
def find_largest_number(numbers):
    return max(numbers)
"""

# NEXUS test cases
test_cases = [
    {
        "input": [3, 1, 4, 2],
        "expected": 4
    },
    {
        "input": [10, 20, 5],
        "expected": 20
    },
    {
        "input": [-5, -2, -9],
        "expected": -2
    }
]

result = run_tests(code, test_cases)

print("\nNEXUS TEST EXECUTION")
print("--------------------")
print("Total tests:", result.get("total_tests"))
print("Passed:", result.get("passed"))
print("Failed:", result.get("failed"))
print("\nDetailed results:")

for test in result.get("results", []):
    print(test)
