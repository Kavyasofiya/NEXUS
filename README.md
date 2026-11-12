# NEXUS – Evidence-Grounded Self-Evolving AI System

NEXUS is an AI-powered programming assistant designed to improve future task-solving through verified experiences and reusable failure knowledge.

It generates Python code, verifies syntax, executes test cases, analyzes failures, and stores verified solutions separately from failed experiences to prevent incorrect knowledge from contaminating its memory.

## Key Features

- **AI Code Generation:** Generates Python solutions using a locally hosted Qwen2.5-Coder model.
- **Code Verification:** Checks generated code for syntax validity.
- **Automated Testing:** Executes code against supplied test cases.
- **Verified Memory:** Stores experiences only when all test cases pass.
- **Failure Memory:** Records failed experiences separately for future diagnostic reference.
- **Context-Aware Retrieval:** Retrieves relevant previous successes and failures.
- **Interactive Web Interface:** Allows users to submit programming tasks and inspect results.

## Technology Stack

| Component | Technologies |
|---|---|
| Frontend | HTML, CSS, JavaScript |
| Backend | Python, FastAPI |
| AI Model | Ollama, Qwen2.5-Coder 3B |
| Database | SQLite |
| Testing | Python AST-based validation and test execution |
| Version Control | Git, GitHub |

## System Architecture

1. User submits a programming task.
2. NEXUS retrieves relevant verified and failure experiences.
3. The AI model generates Python code using the task and available context.
4. The generated code undergoes syntax verification.
5. Test cases are executed.
6. Successful
