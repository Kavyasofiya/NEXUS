
from memory_store import retrieve_similar_experiences

new_task = """
Write a Python function to get the maximum element
from an array of numbers.
"""

results = retrieve_similar_experiences(new_task)

print("\nNEXUS MEMORY RETRIEVAL")
print("======================")

if results:

    for memory in results:
        print("\nMemory ID:", memory["memory_id"])
        print("Previous task:", memory["task"])
        print("Verified code:", memory["code"])
        print("Passed tests:", memory["passed_tests"])
        print("Similarity score:", memory["similarity_score"])

else:
    print("No similar verified experiences found.")
