
from memory_store import get_connection

connection = get_connection()
cursor = connection.cursor()

cursor.execute("""
    SELECT
        id,
        task,
        passed_tests,
        total_tests,
        evidence_summary,
        created_at
    FROM verified_experiences
    ORDER BY id DESC
""")

records = cursor.fetchall()

print("\nNEXUS MEMORY DATABASE")
print("=====================")
print("Total stored experiences:", len(records))

for record in records:
    print("\nMemory ID:", record[0])
    print("Task:", record[1])
    print("Passed tests:", record[2])
    print("Total tests:", record[3])
    print("Evidence:", record[4])
    print("Created at:", record[5])

connection.close()
