import os

import psycopg
from dotenv import load_dotenv

load_dotenv()

connection = psycopg.connect(
    host=os.getenv("POSTGRES_HOST"),
    port=os.getenv("POSTGRES_PORT"),
    dbname=os.getenv("POSTGRES_DB"),
    user=os.getenv("POSTGRES_USER"),
    password=os.getenv("POSTGRES_PASSWORD"),
)

print("Connected to PostgreSQL")

cursor = connection.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS test_table (
    id SERIAL PRIMARY KEY,
    message TEXT NOT NULL
)
""")

connection.commit()

cursor.execute("""
INSERT INTO test_table (message)
VALUES ('Hello from Python')
""")

connection.commit()

cursor.execute("""
SELECT * FROM test_table
""")

rows = cursor.fetchall()

print(rows)

cursor.close()
connection.close()

print("Done")