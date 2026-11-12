from verifier import verify_code

sample_code = """
def add(a, b):
    return a + b
"""

result = verify_code(sample_code)

print("NEXUS VERIFICATION RESULT")
print(result)