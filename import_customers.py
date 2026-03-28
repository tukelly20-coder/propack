# -*- coding: utf-8 -*-
"""
Script import du lieu khach hang tu file markdown vao database
File nguon: docs/客户档案.md
"""

import sqlite3
import re
import os
import sys

# Fix Unicode output for Windows console
if sys.platform == 'win32':
    import io
    try:
        if not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if not isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

# Thread-safe print
_print_lock = __import__('threading').Lock()

def safe_print(*args, **kwargs):
    """Thread-safe print"""
    try:
        with _print_lock:
            print(*args, **kwargs)
    except (ValueError, OSError):
        pass

# Duong dan database
DB_PATH = 'DB.db'
MD_FILE = 'docs/客户档案.md'


def get_connection():
    """Lay ket noi database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def update_customers_schema():
    """
    Cap nhat schema bang customers - them cac columns moi
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Kiem tra va them cac columns moi
    columns_to_add = [
        ('code', 'VARCHAR(10)'),
        ('phonetic', 'VARCHAR(100)'),
        ('english_name', 'VARCHAR(100)')
    ]
    
    # Lay danh sach columns hien tai
    cursor.execute("PRAGMA table_info(customers)")
    existing_columns = {row[1] for row in cursor.fetchall()}
    
    for col_name, col_type in columns_to_add:
        if col_name not in existing_columns:
            try:
                cursor.execute(f"ALTER TABLE customers ADD COLUMN {col_name} {col_type}")
                safe_print("[Schema] Da them column: " + col_name)
            except sqlite3.OperationalError as err:
                safe_print("[Schema] Loi khi them column " + col_name + ": " + str(err))
    
    conn.commit()
    conn.close()
    safe_print("[Schema] Cap nhat schema hoan tat")


def parse_md_file(file_path):
    """
    Parse file markdown de lay danh sach khach hang
    """
    if not os.path.exists(file_path):
        safe_print("[Error] File khong ton tai: " + file_path)
        return []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    customers = []
    
    # Pattern de match cac dong trong bang
    # Vi du: | 0001 | 歌尔 | Gē'ěr | Goertek |
    pattern = r'\|\s*(\d+)\s*\|\s*([^|]+)\s*\|\s*([^|]*)\s*\|\s*([^|]*)\s*\|'
    
    matches = re.findall(pattern, content)
    
    for match in matches:
        code = match[0].strip()
        name = match[1].strip()
        phonetic = match[2].strip()
        english_name = match[3].strip()
        
        # Skip dong tieu de va dong trong
        if code == 'Ma':
            continue
        if not name:
            continue
            
        customers.append({
            'code': code,
            'name': name,
            'phonetic': phonetic,
            'english_name': english_name
        })
    
    return customers


def import_customers(customers):
    """
    Import danh sach khach hang vao database
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    imported_count = 0
    skipped_count = 0
    
    for customer in customers:
        # Kiem tra xem khach hang da ton tai chua (theo code hoac name)
        cursor.execute('SELECT id FROM customers WHERE code = ? OR name = ?', 
                      (customer['code'], customer['name']))
        existing = cursor.fetchone()
        
        if existing:
            # Cap nhat neu da ton tai
            cursor.execute('''
                UPDATE customers 
                SET name = ?, phonetic = ?, english_name = ?
                WHERE code = ?
            ''', (
                customer['name'],
                customer['phonetic'],
                customer['english_name'],
                customer['code']
            ))
            safe_print("[Update] Da cap nhat: " + customer['code'] + " - " + customer['name'])
        else:
            # Insert moi
            cursor.execute('''
                INSERT INTO customers (code, name, phonetic, english_name)
                VALUES (?, ?, ?, ?)
            ''', (
                customer['code'],
                customer['name'],
                customer['phonetic'],
                customer['english_name']
            ))
            safe_print("[Insert] Da them moi: " + customer['code'] + " - " + customer['name'])
            imported_count += 1
    
    conn.commit()
    conn.close()
    
    safe_print("")
    safe_print("[Ket qua] Import hoan tat:")
    safe_print("  - Them moi: " + str(imported_count) + " khach hang")
    safe_print("  - Bo qua (da ton tai): " + str(skipped_count) + " khach hang")
    safe_print("  - Tong: " + str(len(customers)) + " khach hang")


def show_customers():
    """
    Hien thi danh sach khach hang trong database
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT code, name, phonetic, english_name FROM customers ORDER BY code')
    rows = cursor.fetchall()
    
    safe_print("")
    safe_print("[Danh sach khach hang trong database]")
    safe_print("-" * 80)
    safe_print("Ma          Ten khach hang                  Phien am                Ten tieng Anh")
    safe_print("-" * 80)
    
    for row in rows:
        code = row['code'] or ''
        name = row['name'] or ''
        phonetic = row['phonetic'] or ''
        english_name = row['english_name'] or ''
        safe_print(code.ljust(10) + name.ljust(30) + phonetic.ljust(20) + english_name.ljust(20))
    
    safe_print("-" * 80)
    safe_print("Tong cong: " + str(len(rows)) + " khach hang")
    
    conn.close()


def main():
    """
    Main function - chay toan bo qua trinh import
    """
    safe_print("=" * 60)
    safe_print("Import du lieu khach hang tu 客户档案.md vao database")
    safe_print("=" * 60)
    
    # Buoc 1: Cap nhat schema
    safe_print("")
    safe_print("[Buoc 1] Cap nhat schema bang customers...")
    update_customers_schema()
    
    # Buoc 2: Parse file markdown
    safe_print("")
    safe_print("[Buoc 2] Doc file markdown...")
    customers = parse_md_file(MD_FILE)
    safe_print("Da doc duoc " + str(len(customers)) + " khach hang tu file")
    
    # Buoc 3: Import vao database
    safe_print("")
    safe_print("[Buoc 3] Import du lieu vao database...")
    import_customers(customers)
    
    # Buoc 4: Hien thi ket qua
    safe_print("")
    safe_print("[Buoc 4] Kiem tra du lieu...")
    show_customers()
    
    safe_print("")
    safe_print("=" * 60)
    safe_print("Hoan tat!")
    safe_print("=" * 60)


if __name__ == '__main__':
    main()