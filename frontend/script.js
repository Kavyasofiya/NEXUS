
const API_URL = "http://127.0.0.1:8000/solve";

let latestCode = "";

function showResult(elementId, content) {
    const element = document.getElementById(elementId);

    if (element) {
        element.textContent = content;
    }
}


// Clean generated Python code.
function cleanGeneratedCode(code) {
    if (!code) return "";

    let cleaned = String(code).trim();

    cleaned = cleaned.replace(/^```(?:python)?\s*/i, "");
    cleaned = cleaned.replace(/\s*```$/, "");

    cleaned = cleaned.replace(
        /(def\s+\w+\([^)]*\):)\s*(return\b)/,
        "$1\n    $2"
    );

    return cleaned.trim();
}

window.cleanGeneratedCode = cleanGeneratedCode;
console.log("NEXUS FORMATTER LOADED");


// Convert text values into JavaScript values.
function parseTestValue(value) {
    const cleaned = value.trim();

    try {
        return JSON.parse(cleaned);
    } catch (error) {
        return cleaned;
    }
}


// Parse test cases.
function parseTestCases(text) {

    if (!text.trim()) {
        return null;
    }

    if (text.trim().startsWith("[")) {

        const parsed = JSON.parse(text);

        if (!Array.isArray(parsed)) {
            throw new Error("Test cases must be an array.");
        }

        return parsed;
    }

    const blocks = text.trim().split(/\n\s*\n/);

    return blocks.map((block, index) => {

        const inputMatch = block.match(/^Input:\s*(.+)$/im);
        const expectedMatch = block.match(/^Expected:\s*(.+)$/im);

        if (!inputMatch || !expectedMatch) {
            throw new Error(
                `Test case ${index + 1}: Please provide both Input and Expected.`
            );
        }

        return {
            input: parseTestValue(inputMatch[1]),
            expected: parseTestValue(expectedMatch[1])
        };

    });
}


// Format test execution results.
function formatTestResults(data) {

    if (!data) {
        return "No test results returned. Check that test cases were submitted.";
    }

    const lines = [];

    lines.push(
        "Status: " +
        (data.success ? "ALL TESTS PASSED" : "TESTS FAILED")
    );

    lines.push("Passed: " + (data.passed ?? "Not provided"));
    lines.push("Total: " + (data.total_tests ?? "Not provided"));

    if (Array.isArray(data.results)) {

        data.results.forEach((test, index) => {

            lines.push("");

            lines.push(
                "Test " + (index + 1) + ": " +
                (test.passed ? "PASS" : "FAIL")
            );

            if ("expected" in test) {
                lines.push(
                    "Expected: " + JSON.stringify(test.expected)
                );
            }

            if ("actual" in test) {
                lines.push(
                    "Actual: " + JSON.stringify(test.actual)
                );
            }

            if (test.error) {
                lines.push("Error: " + test.error);
            }

        });
    }

    return lines.join("\n");
}


// Format failure analysis.
function formatFailureAnalysis(data) {

    if (!data) {
        return "No failure analysis returned.";
    }

    const lines = [
        "Status: " + (data.status ?? "Not provided"),
        "Message: " + (data.message ?? "No message")
    ];

    if (Array.isArray(data.failures) && data.failures.length > 0) {

        data.failures.forEach((failure, index) => {

            lines.push("");
            lines.push("Failure " + (index + 1));

            lines.push(
                "Type: " + (failure.failure_type ?? "Unknown")
            );

            lines.push(
                "Evidence: " + (failure.evidence ?? "Not provided")
            );

        });

    } else {
        lines.push("No individual failures reported.");
    }

    return lines.join("\n");
}


// Format retrieved verified memories.
function formatMemories(data) {

    const memories = data.retrieved_memories || [];

    const lines = [
        "Retrieved memories: " +
        (data.retrieved_memory_count ?? memories.length),

        "New memory saved: " +
        (data.memory_saved ? "YES" : "NO")
    ];

    if (memories.length > 0) {

        memories.forEach((memory, index) => {

            lines.push("");
            lines.push("Memory " + (index + 1));

            lines.push(
                "Previous task: " +
                (memory.previous_task ?? "Not provided")
            );

            lines.push(
                "Similarity: " +
                (memory.similarity_score ?? "Not provided")
            );

            lines.push(
                "Memory ID: " +
                (memory.memory_id ?? "Not provided")
            );

        });

    } else {

        lines.push("");
        lines.push("No relevant previous verified experience found.");

    }

    return lines.join("\n");
}


// Format retrieved failure memories.
function formatFailureMemories(data) {

    const failures = data.retrieved_failures || [];

    const lines = [
        "Retrieved failure memories: " +
        (data.retrieved_failure_count ?? failures.length),

        "New failure records saved: " +
        (data.failure_memory_saved ?? 0)
    ];

    if (failures.length > 0) {

        failures.forEach((failure, index) => {

            lines.push("");
            lines.push("Failure Memory " + (index + 1));

            lines.push(
                "Previous task: " +
                (failure.previous_task ?? "Not provided")
            );

            lines.push(
                "Failure type: " +
                (failure.failure_type ?? "Unknown")
            );

            lines.push(
                "Similarity: " +
                (failure.similarity_score ?? "Not provided")
            );

            lines.push(
                "Evidence: " +
                (failure.evidence ?? "Not provided")
            );

            lines.push(
                "Failure ID: " +
                (failure.failure_id ?? "Not provided")
            );

        });

    } else {

        lines.push("");
        lines.push("No relevant previous failure experience found.");

    }

    return lines.join("\n");
}
window.formatFailureMemories = formatFailureMemories;

// Main NEXUS pipeline.
async function generateCode() {

    const task = document.getElementById("taskInput").value.trim();

    const testCasesText =
        document.getElementById("testCases").value.trim();

    const button = document.getElementById("generateBtn");

    const status = document.getElementById("statusMessage");

    const generatedCode =
        document.getElementById("generatedCode");

    if (!task) {
        status.textContent = "Please enter a programming task.";
        return;
    }

    let testCases = null;

    if (testCasesText) {

        try {
            testCases = parseTestCases(testCasesText);
        } catch (error) {
            status.textContent =
                "Invalid test cases: " + error.message;
            return;
        }

    }

    button.disabled = true;
    button.textContent = "Processing...";

    status.textContent =
        "NEXUS is generating and verifying your solution.";

    latestCode = "";

    document.getElementById("copyBtn").disabled = true;

    generatedCode.textContent = "Waiting for AI response...";

    showResult("verificationResult", "Processing...");
    showResult("testResult", "Processing...");
    showResult("failureResult", "Processing...");
    showResult("memoryResult", "Processing...");
    showResult("failureMemoryResult", "Processing...");

    try {

        const response = await fetch(API_URL, {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                task: task,
                test_cases: testCases
            })

        });

        const data = await response.json();

        window.lastNexusResponse = data;

        console.log("NEXUS RAW RESPONSE:", data);

        if (!response.ok) {
            throw new Error(
                data.detail || "Backend returned HTTP " + response.status
            );
        }

        // Generated code.
        const rawCode =
            data.verification?.code || data.ai_response || "";

        latestCode = cleanGeneratedCode(rawCode);

        generatedCode.textContent =
            latestCode || "No code generated.";

        // Syntax verification.
        const verification = data.verification;

        if (verification) {

            showResult(
                "verificationResult",
                "Syntax: " +
                (verification.verified ? "VALID" : "INVALID") +
                "\n\n" +
                (verification.message || "No verification message.")
            );

        } else {

            showResult(
                "verificationResult",
                "No verification data returned."
            );

        }

        // Test execution.
        showResult(
            "testResult",
            formatTestResults(data.test_results)
        );

        // Failure analysis.
        showResult(
            "failureResult",
            formatFailureAnalysis(data.failure_analysis)
        );

        // Verified memory.
        showResult(
            "memoryResult",
            formatMemories(data)
        );

        // Failure memory.
        showResult(
            "failureMemoryResult",
            formatFailureMemories(data)
        );

        document.getElementById("copyBtn").disabled = !latestCode;

        status.textContent =
            "NEXUS pipeline completed successfully.";

    } catch (error) {

        generatedCode.textContent =
            "Unable to complete the NEXUS request.\n\n" +
            error.message;

        showResult("verificationResult", "Request failed.");
        showResult("testResult", "Request failed.");
        showResult("failureResult", "Request failed.");
        showResult("memoryResult", "Request failed.");
        showResult("failureMemoryResult", "Request failed.");

        status.textContent =
            "Error: Check that FastAPI and Ollama are running.";

        console.error("NEXUS ERROR:", error);

    } finally {

        button.disabled = false;
        button.textContent = "Run NEXUS Pipeline →";

    }

}


// Copy generated code.
async function copyCode() {

    if (!latestCode) {
        return;
    }

    try {

        await navigator.clipboard.writeText(latestCode);

        document.getElementById("statusMessage").textContent =
            "Generated code copied to clipboard.";

    } catch (error) {

        document.getElementById("statusMessage").textContent =
            "Copy failed. Select the code and copy it manually.";

    }

}


// Sidebar navigation.
document.querySelectorAll(".nav-item").forEach((item) => {

    item.addEventListener("click", function () {

        document.querySelectorAll(".nav-item").forEach((nav) => {
            nav.classList.remove("active");
        });

        this.classList.add("active");

    });

});


// Update active navigation item while scrolling.
const navigationSections = document.querySelectorAll(
    "#ai-workspace, #code-generation, #verification, #experience-memory"
);

const navigationItems = document.querySelectorAll(".nav-item");

if ("IntersectionObserver" in window) {

    const observer = new IntersectionObserver((entries) => {

        entries.forEach((entry) => {

            if (entry.isIntersecting) {

                navigationItems.forEach((item) => {
                    item.classList.toggle(
                        "active",
                        item.getAttribute("href") === "#" + entry.target.id
                    );
                });

            }

        });

    }, {
        rootMargin: "-20% 0px -65% 0px"
    });

    navigationSections.forEach((section) => {
        observer.observe(section);
    });

}
