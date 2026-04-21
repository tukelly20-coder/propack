import sqlite3

conn = sqlite3.connect('DB.db')
cursor = conn.cursor()

# Check if projects table exists
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='projects'")
row = cursor.fetchone()
print('Projects table exists:', row is not None)

if row:
    cursor.execute('PRAGMA table_info(projects)')
    cols = cursor.fetchall()
    print(f'\nTotal columns: {len(cols)}')
    print('Columns:')
    for i, col in enumerate(cols):
        print(f'  {i}: {col[1]} ({col[2]})')

conn.close()
