import sqlite3
import os

db_path = r'C:\Users\Kelly\Desktop\Source code 自动生成图纸编码- V8 大日程\DB.db'

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get table schema
cursor.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='projects'")
row = cursor.fetchone()
if row:
    print("=== Projects Table Schema ===")
    print(row[0])
    print()

# Get column info
cursor.execute("PRAGMA table_info(projects)")
columns = cursor.fetchall()
print("=== Current Columns ===")
for col in columns:
    cid, name, type_, notnull, default, pk = col
    print(f"  {name}: {type_}{' (PK)' if pk else ''}{' NOT NULL' if notnull else ''}")

conn.close()
