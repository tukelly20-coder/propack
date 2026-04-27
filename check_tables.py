import sqlite3
conn = sqlite3.connect('DB.db')
c = conn.cursor()
print('Tables:', c.execute('SELECT name FROM sqlite_master WHERE type="table"').fetchall())
print('Customers:', c.execute('SELECT * FROM customers').fetchall())
print('Users:', c.execute('SELECT user_id,username,role,full_name FROM users').fetchall())
conn.close()