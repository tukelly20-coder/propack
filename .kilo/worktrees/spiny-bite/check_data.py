import sqlite3

conn = sqlite3.connect('DB.db')
cursor = conn.cursor()

cursor.execute('SELECT COUNT(*) FROM projects')
count = cursor.fetchone()[0]
print(f'Total project records: {count}')

if count > 0:
    cursor.execute('SELECT tracking_id, data FROM projects LIMIT 3')
    rows = cursor.fetchall()
    print('\nSample data:')
    for row in rows:
        print(f'ID: {row[0]}, data preview: {str(row[1])[:200]}')

conn.close()
