import sqlite3
conn = sqlite3.connect('DB.db')
c = conn.cursor()
res = c.execute('SELECT name FROM sqlite_master WHERE type="table"').fetchall()
print('tables:', res)
for row in res:
    print('table:', row[0])
    c.execute('SELECT * FROM ' + row[0])
    rows = c.fetchall()
    for r in rows:
        print('  row:', r)
conn.close()