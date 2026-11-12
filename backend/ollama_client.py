
import requests

OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
MODEL_NAME = "qwen2.5-coder:3b"


def generate_response(prompt):
    """
    Sends a prompt to the local Ollama model
    and returns its response.
    """

    payload = {
        "model": MODEL_NAME,
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ],
        "stream": False,
        "options": {
            "temperature": 0.1
        }
    }

    try:
        response = requests.post(
            OLLAMA_URL,
            json=payload,
            timeout=300
        )

        response.raise_for_status()

        result = response.json()
        return result["message"]["content"]

    except requests.exceptions.ConnectionError:
        return "ERROR: Cannot connect to Ollama. Check whether Ollama is running."

    except requests.exceptions.Timeout:
        return "ERROR: The model took too long to respond."

    except requests.exceptions.RequestException as error:
        return f"ERROR: {error}"


if __name__ == "__main__":
    question = "Write a Python function named square that returns the square of a number."

    print("NEXUS is contacting the local AI model...")
    answer = generate_response(question)

    print("\nAI RESPONSE:")
    print(answer)
