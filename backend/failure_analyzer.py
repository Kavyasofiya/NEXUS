
def analyze_failures(test_results):

    if not test_results:
        return {
            "status": "NO_TEST_RESULTS",
            "message": "No test results available.",
            "failure_count": 0,
            "failures": []
        }

    if test_results.get("success") is True:
        return {
            "status": "ALL_TESTS_PASSED",
            "message": "No failures detected.",
            "failure_count": 0,
            "failures": []
        }

    failures = []

    for result in test_results.get("results", []):

        if result.get("passed"):
            continue

        if "error" in result:
            failure_type = "RUNTIME_ERROR"
            evidence = str(result["error"])

        elif result.get("actual") is None:
            failure_type = "UNEXPECTED_RETURN"
            evidence = "Function returned None."

        else:
            failure_type = "OUTPUT_MISMATCH"
            evidence = (
                f"Expected {result.get('expected')}, "
                f"but received {result.get('actual')}."
            )

        failures.append({
            "failure_type": failure_type,
            "input": result.get("input"),
            "expected": result.get("expected"),
            "actual": result.get("actual"),
            "evidence": evidence
        })

    return {
        "status": "FAILURES_DETECTED",
        "message": f"{len(failures)} test failure(s) detected.",
        "failure_count": len(failures),
        "failures": failures
    }
