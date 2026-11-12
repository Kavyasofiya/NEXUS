
from fastapi.middleware.cors import CORSMiddleware
from fastapi import FastAPI
from pydantic import BaseModel
from typing import Optional

from ollama_client import generate_response
from verifier import verify_code
from test_runner import run_tests
from failure_analyzer import analyze_failures

from memory_store import (
    initialize_memory,
    save_verified_experience,
    retrieve_similar_experiences,
    save_failure_experience,
    retrieve_similar_failures
)


# Initialize NEXUS memory database
initialize_memory()


app = FastAPI(
    title="NEXUS AI System",
    description="Evidence-Grounded Self-Evolving AI System",
    version="1.0"
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TaskRequest(BaseModel):
    task: str
    test_cases: Optional[list[dict]] = None
    use_failure_memory: bool = True
    save_memory: bool = True

@app.get("/")
def home():
    return {
        "project": "NEXUS",
        "message": "NEXUS AI System is running!"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "ai_model": "qwen2.5-coder:3b"
    }


@app.post("/solve")
def solve_task(request: TaskRequest):

    # Stage 1: Retrieve previous verified experiences
    retrieved_memories = retrieve_similar_experiences(
        request.task,
        limit=3
    )

    if request.use_failure_memory:
        retrieved_failures = retrieve_similar_failures(
            request.task,
            limit=3
    )
    else:
        retrieved_failures = []

    # Stage 3: Prepare verified memory context
    if retrieved_memories:

        memory_context = ""

        for memory in retrieved_memories:

            memory_context += f"""
Previous Task:
{memory['task']}

Previously Verified Code:
{memory['code']}

Test Evidence:
{memory['passed_tests']} out of
{memory['total_tests']} supplied tests passed.

Evidence Summary:
{memory['evidence']}

Similarity Score:
{memory['similarity_score']}

--------------------------------
"""

    else:
        memory_context = (
            "No relevant previous verified experience found."
        )

    # Stage 4: Prepare failure memory context
    if retrieved_failures:

        failure_context = ""

        for failure in retrieved_failures:

            failure_context += f"""
Previous Failed Task:
{failure['task']}

Failure Type:
{failure['failure_type']}

Input:
{failure['input']}

Expected Output:
{failure['expected']}

Incorrect Actual Output:
{failure['actual']}

Failure Evidence:
{failure['evidence']}

Similarity Score:
{failure['similarity_score']}

--------------------------------
"""

    else:
        failure_context = (
            "No relevant previous failure experience found."
        )

    # Stage 5: Generate solution using both memory types
    prompt = f"""
You are a Python programming assistant inside NEXUS.

Solve the current programming task.

PREVIOUS VERIFIED EXPERIENCES:
{memory_context}

PREVIOUS FAILURE EXPERIENCES:
{failure_context}

INSTRUCTIONS:

1. Use relevant verified experiences as references.
2. Study previous failure evidence carefully.
3. Avoid repeating mistakes identified by previous failures.
4. Do not blindly copy previous code.
5. Adapt the solution to the current task.
6. Generate exactly one Python function.
7. Do not include example usage.
8. Do not include print statements.
9. Do not include explanations.
10. Return one Python code block only.

IMPORTANT:
Previous failure records are diagnostic evidence.
They are not verified solutions.
Do not treat incorrect outputs as correct answers.

CURRENT TASK:
{request.task}
"""

    answer = generate_response(prompt)

    # Stage 6: Verify generated syntax
    verification = verify_code(answer)

    test_results = None
    failure_analysis = None
    memory_saved = False
    failure_memory_saved = 0

    # Stage 7: Execute supplied test cases
    if verification["verified"] and request.test_cases:

        test_results = run_tests(
            verification["code"],
            request.test_cases
        )

        # Stage 8: Analyze test results
        if "results" in test_results:

            failure_analysis = analyze_failures(test_results)

        # Stage 9: Save failed experiences separately
        if (
            request.save_memory
            and failure_analysis
            and failure_analysis.get("status")
            == "FAILURES_DETECTED"
     ):

            for failure in failure_analysis.get("failures", []):

                saved = save_failure_experience(
                    task=request.task,
                    failure_type=failure["failure_type"],
                    input_data=failure.get("input"),
                    expected_output=failure.get("expected"),
                    actual_output=failure.get("actual"),
                    evidence=failure["evidence"]
                )

                if saved:
                    failure_memory_saved += 1

        # Stage 10: Save only fully verified experiences
        if (
            request.save_memory
            and test_results
            and test_results.get("success")
            and test_results.get("total_tests", 0) > 0
            and test_results.get("passed", 0)
            == test_results.get("total_tests", 0)
     ):
            memory_saved = save_verified_experience(
                task=request.task,
                code=verification["code"],
                test_cases=request.test_cases,
                passed_tests=test_results["passed"],
                total_tests=test_results["total_tests"]
            )

    # Stage 11: Return complete NEXUS results
    return {
        "task": request.task,

        "retrieved_memory_count": len(retrieved_memories),

        "retrieved_memories": [
            {
                "memory_id": memory["memory_id"],
                "similarity_score": memory["similarity_score"],
                "previous_task": memory["task"]
            }
            for memory in retrieved_memories
        ],

        "retrieved_failure_count": len(retrieved_failures),

        "retrieved_failures": [
            {
                "failure_id": failure["failure_id"],
                "similarity_score": failure["similarity_score"],
                "previous_task": failure["task"],
                "failure_type": failure["failure_type"],
                "evidence": failure["evidence"]
            }
            for failure in retrieved_failures
        ],

        "ai_response": answer,
        "verification": verification,
        "test_results": test_results,
        "failure_analysis": failure_analysis,

        "memory_saved": memory_saved,
        "failure_memory_saved": failure_memory_saved
    }
