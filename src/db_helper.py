"""
SQLite Database Helper for Project Tracking V2
Module này cung cấp các hàm để làm việc với SQLite database
Bao gồm: Projects, Users, Customers management
"""

import sqlite3
import json
import os
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any, Union

# Đường dẫn database
DB_PATH = 'DB.db'
MAX_PROJECT_PAGE_LIMIT = 5000

# In-memory cache for load_all
_data_cache = None
_cache_loaded = False


def get_db_path():
    """Lấy đường dẫn database"""
    return DB_PATH


def init_db():
    """Khởi tạo database với bảng projects (id và tracking_id đã hợp nhất)"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Tạo bảng projects - tracking_id làm PRIMARY KEY duy nhất
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            tracking_id INTEGER PRIMARY KEY,
            data TEXT NOT NULL,
            sales_name VARCHAR(100),
            user_id INTEGER,
            is_pending VARCHAR(10) DEFAULT 'no',
            accepted_by VARCHAR(100),
            accepted_at TEXT,
            urgency_level VARCHAR(20),
            desired_solution_time TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    print(f"[DB] Database initialized at {DB_PATH}")


def init_db_v2():
    """
    Khởi tạo database V2 với tất cả bảng mới
    Bao gồm: users, customers, projects (normalized với columns riêng biệt)
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Bảng users (User Profile)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            passwords VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'sales',
            full_name VARCHAR(100) NOT NULL,
            employee_id VARCHAR(20),
            department VARCHAR(50) DEFAULT 'Sales',
            status VARCHAR(20) DEFAULT 'active',
            last_login TEXT
        )
    ''')
    
    # Bảng customers (Danh sách khách hàng)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code VARCHAR(50),
            name VARCHAR(200) UNIQUE NOT NULL,
            phonetic VARCHAR(100),
            english_name VARCHAR(200),
            contact_person VARCHAR(100),
            phone VARCHAR(50),
            email VARCHAR(100),
            address TEXT
        )
    ''')
    
    # Bảng projects - NORMALIZED với columns riêng biệt (thay vì JSON blob)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            tracking_id INTEGER PRIMARY KEY,
            -- 19 cột dữ liệu từ JSON trước đây
            Created_Date DATE,
            khach_hang VARCHAR(200),
            nhan_vien_kinh_doanh VARCHAR(100),
            ten_san_pham VARCHAR(200),
            quy_cach TEXT,
            khach_hang_yeu_cau_ky_thuat TEXT,
            nguoi_lien_he_kh VARCHAR(100),
            so_luong INTEGER,
            ma_po VARCHAR(50),
            ma_ban_ve VARCHAR(50),
            ma_ban_ve_ky_thuat VARCHAR(50),
            ma_me VARCHAR(50),
            loai_san_pham VARCHAR(100),
            nhan_vien_thiet_ke VARCHAR(100),
            tinh_trang_hoan_thanh VARCHAR(100),
            urgency_level VARCHAR(20),
            thoi_gian_mong_muon_ban_ve TEXT,
            thoi_gian_hoan_thanh_ke_hoach TEXT,
            -- Metadata columns
            sales_name VARCHAR(100),
            user_id INTEGER,
            is_pending VARCHAR(10) DEFAULT 'no',
            accepted_by VARCHAR(100),
            accepted_at TEXT,
            desired_solution_time TEXT
        )
    ''')
    
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_ma_po ON projects(ma_po)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_ten_san_pham ON projects(ten_san_pham)')
    
    conn.commit()
    conn.close()
    print(f"[DB] Database V2 normalized initialized at {DB_PATH}")


def migrate_ngay_to_created_date():
    """
    Migration: Đổi tên cột 'ngay' thành 'Created_Date'
    Returns: bool
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Kiểm tra nếu cột 'ngay' còn tồn tại
        cursor.execute("PRAGMA table_info(projects)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if 'ngay' not in columns and 'Created_Date' not in columns:
            print("[DB] Cột 'ngay' và 'Created_Date' không tồn tại")
            conn.close()
            return True
        
        if 'Created_Date' in columns:
            print("[DB] Cột 'Created_Date' đã tồn tại, không cần migrate")
            conn.close()
            return True
        
        print("[DB] Bắt đầu migrate 'ngay' → 'Created_Date'...")
        
        # Bước 1: Tạo bảng tạm với schema mới (đổi tên ngay → Created_Date)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects_new (
                tracking_id INTEGER PRIMARY KEY,
                Created_Date DATE,
                khach_hang VARCHAR(200),
                nhan_vien_kinh_doanh VARCHAR(100),
                ten_san_pham VARCHAR(200),
                quy_cach TEXT,
                khach_hang_yeu_cau_ky_thuat TEXT,
                nguoi_lien_he_kh VARCHAR(100),
                so_luong INTEGER,
                ma_po VARCHAR(50),
                ma_ban_ve VARCHAR(50),
                ma_ban_ve_ky_thuat VARCHAR(50),
                ma_me VARCHAR(50),
                loai_san_pham VARCHAR(100),
                nhan_vien_thiet_ke VARCHAR(100),
                tinh_trang_hoan_thanh VARCHAR(100),
                urgency_level VARCHAR(20),
                thoi_gian_mong_muon_ban_ve TEXT,
                thoi_gian_hoan_thanh_ke_hoach TEXT,
                sales_name VARCHAR(100),
                user_id INTEGER,
                is_pending VARCHAR(10) DEFAULT 'no',
                accepted_by VARCHAR(100),
                accepted_at TEXT,
                desired_solution_time TEXT
            )
        ''')
        
        # Bước 2: Copy dữ liệu từ bảng cũ sang bảng mới
        cursor.execute("SELECT * FROM projects")
        old_columns = [desc[0] for desc in cursor.description]
        
        # Map columns (đổi ngay → Created_Date)
        column_mapping = {}
        for col in old_columns:
            if col == 'ngay':
                column_mapping[col] = 'Created_Date'
            else:
                column_mapping[col] = col
        
        # Insert dữ liệu
        insert_cols = ', '.join(column_mapping.values())
        placeholders = ', '.join(['?' for _ in column_mapping])
        
        cursor.execute(f"SELECT {', '.join(old_columns)} FROM projects")
        for row in cursor.fetchall():
            # Chuyển đổi row dict với key mới
            row_dict = dict(zip(old_columns, row))
            new_row = [row_dict.get(col) for col in old_columns]
            cursor.execute(
                f"INSERT INTO projects_new ({insert_cols}) VALUES ({placeholders})",
                new_row
            )
        
        # Bước 3: Xóa bảng cũ và đổi tên bảng mới
        cursor.execute("DROP TABLE projects")
        cursor.execute("ALTER TABLE projects_new RENAME TO projects")
        
        # Bước 4: Cập nhật index
        cursor.execute("DROP INDEX IF EXISTS idx_projects_ngay")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_projects_created_date ON projects(Created_Date)")
        
        conn.commit()
        conn.close()
        
        print("[DB] Migration 'ngay' → 'Created_Date' hoàn tất")
        return True
    
    except Exception as e:
        print(f"[DB] Error migrating 'ngay' to 'Created_Date': {e}")
        import traceback
        traceback.print_exc()
        return False


def migrate_projects_schema():
    """
    Migration: Hợp nhất id và tracking_id trong bảng projects
    - Tạo bảng mới với tracking_id làm PRIMARY KEY
    - Copy dữ liệu từ bảng cũ (hỗ trợ cả user_id và sales_id)
    - Xóa bảng cũ và đổi tên bảng mới
    Returns: bool
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Kiểm tra nếu bảng cũ có cột 'id' hoặc 'user_id' (cần migration)
        cursor.execute("PRAGMA table_info(projects)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Nếu bảng đã không có cột 'data' thì đã là V2 normalized schema
        if 'data' not in columns:
            print("[DB] Projects table already normalized (no 'data' column)")
            conn.close()
            return True
        
        # Nếu bảng đã có sales_id và không có user_id thì đã migrate
        if 'sales_id' in columns and 'user_id' not in columns:
            print("[DB] Projects table already migrated (has sales_id, no user_id)")
            conn.close()
            return True
        
        print("[DB] Starting projects schema migration (user_id -> sales_id)...")
        
        # Bước 1: Tạo bảng tạm với schema mới (dùng sales_id)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects_new (
                tracking_id INTEGER PRIMARY KEY,
                data TEXT NOT NULL,
                sales_name VARCHAR(100),
                sales_id INTEGER,
                is_pending VARCHAR(10) DEFAULT 'no',
                accepted_by VARCHAR(100),
                accepted_at TEXT,
                urgency_level VARCHAR(20),
                desired_solution_time TEXT
            )
        ''')
        
        # Bước 2: Copy dữ liệu từ bảng cũ sang bảng mới
        # Lấy tất cả columns từ bảng cũ, map user_id -> sales_id
        cursor.execute("SELECT * FROM projects")
        old_columns = [desc[0] for desc in cursor.description]
        
        # Build mapping: column cũ -> column mới
        column_mapping = {
            'tracking_id': 'tracking_id',
            'data': 'data',
            'sales_name': 'sales_name',
            'is_pending': 'is_pending',
            'accepted_by': 'accepted_by',
            'accepted_at': 'accepted_at',
            'urgency_level': 'urgency_level',
            'desired_solution_time': 'desired_solution_time'
        }
        
        # Map user_id -> sales_id (nếu có)
        if 'user_id' in old_columns:
            column_mapping['user_id'] = 'sales_id'
        elif 'sales_id' in old_columns:
            column_mapping['sales_id'] = 'sales_id'
        else:
            column_mapping['user_id'] = 'sales_id'  # sẽ là NULL
        
        # Build select and insert
        select_cols = list(column_mapping.keys())
        insert_cols = list(column_mapping.values())
        placeholders = ', '.join(['?' for _ in insert_cols])
        
        cursor.execute(f"SELECT {', '.join(select_cols)} FROM projects")
        for row in cursor.fetchall():
            # row theo thứ tự select_cols
            values = list(row)
            cursor.execute(
                f"INSERT INTO projects_new ({', '.join(insert_cols)}) VALUES ({placeholders})",
                values
            )
        
        # Bước 3: Xóa bảng cũ và đổi tên bảng mới
        cursor.execute("DROP TABLE projects")
        cursor.execute("ALTER TABLE projects_new RENAME TO projects")
        
        conn.commit()
        conn.close()
        
        print("[DB] Projects schema migration completed successfully (user_id -> sales_id)")
        return True
    
    except Exception as e:
        print(f"[DB] Error migrating projects schema: {e}")
        import traceback
        traceback.print_exc()
        return False


def migrate_to_v2():
    """
    Migrate database từ V1 sang V2
    - Tạo bảng users và customers mới
    - Thêm columns mới vào projects
    - Hợp nhất id và tracking_id
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Kiểm tra và tạo bảng users
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            username VARCHAR(50) UNIQUE NOT NULL,
            passwords VARCHAR(255) NOT NULL,
            role VARCHAR(20) NOT NULL DEFAULT 'sales',
            full_name VARCHAR(100) NOT NULL,
            employee_id VARCHAR(20),
            department VARCHAR(50) DEFAULT 'Sales',
            status VARCHAR(20) DEFAULT 'active',
            last_login TEXT,
            user_created_at TEXT
        )
    ''')
    
    # Migration: Thêm cột user_created_at nếu chưa có (cho DB cũ)
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN user_created_at TEXT')
    except sqlite3.OperationalError:
        pass  # Column đã tồn tại
    
    # Migration: Thêm cột email và phone cho profile
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN email VARCHAR(100)')
    except sqlite3.OperationalError:
        pass  # Column đã tồn tại
    
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN phone VARCHAR(50)')
    except sqlite3.OperationalError:
        pass  # Column đã tồn tại
    
    # Tạo bảng user_permissions (permissions cho từng user)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_permissions (
            permission_id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            permission VARCHAR(50) NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(user_id) ON DELETE CASCADE,
            UNIQUE(user_id, permission)
        )
    ''')
    
    # Kiểm tra và tạo bảng customers
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS customers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code VARCHAR(50),
            name VARCHAR(200) UNIQUE NOT NULL,
            phonetic VARCHAR(100),
            english_name VARCHAR(200),
            contact_person VARCHAR(100),
            phone VARCHAR(50),
            email VARCHAR(100),
            address TEXT
        )
    ''')
    
    # Migration: Thêm các cột mới cho customers (nếu chưa có) - CHO DB CŨ
    try:
        cursor.execute('ALTER TABLE customers ADD COLUMN code VARCHAR(50)')
    except sqlite3.OperationalError:
        pass  # Column đã tồn tại
    try:
        cursor.execute('ALTER TABLE customers ADD COLUMN phonetic VARCHAR(100)')
    except sqlite3.OperationalError:
        pass  # Column đã tồn tại
    try:
        cursor.execute('ALTER TABLE customers ADD COLUMN english_name VARCHAR(200)')
    except sqlite3.OperationalError:
        pass  # Column đã tồn tại
    
    # Thêm columns mới vào bảng projects (nếu chưa có)
    try:
        cursor.execute('ALTER TABLE projects ADD COLUMN sales_name VARCHAR(100)')
    except sqlite3.OperationalError:
        pass  # Column đã tồn tại
    
    try:
        cursor.execute('ALTER TABLE projects ADD COLUMN sales_id INTEGER')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute("ALTER TABLE projects ADD COLUMN is_pending VARCHAR(10) DEFAULT 'no'")
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE projects ADD COLUMN accepted_by VARCHAR(100)')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE projects ADD COLUMN accepted_at TEXT')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE projects ADD COLUMN urgency_level VARCHAR(20)')
    except sqlite3.OperationalError:
        pass

    try:
        cursor.execute('ALTER TABLE projects ADD COLUMN khach_hang_yeu_cau_ky_thuat TEXT')
    except sqlite3.OperationalError:
        pass
    
    try:
        cursor.execute('ALTER TABLE projects ADD COLUMN desired_solution_time TEXT')
    except sqlite3.OperationalError:
        pass
    
    # Tạo indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_user_permissions_user_id ON user_permissions(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_customers_name ON customers(name)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_pending ON projects(is_pending)')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS parent_code_cache (
            engineer_fig_no TEXT PRIMARY KEY,
            parent_code TEXT NOT NULL,
            source TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_parent_code_cache_parent ON parent_code_cache(parent_code)')
    
    conn.commit()
    conn.close()
    
    # Migration: Hợp nhất id và tracking_id
    migrate_projects_schema()
    
    # Migration: Chuyển từ JSON blob sang columns (nếu cần)
    # Hàm này sẽ tạo bảng mới với đầy đủ columns nếu chưa có
    migrate_json_to_columns()
    
    print(f"[DB] Database migrated to V2")


def get_connection():
    """Lấy kết nối database"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def normalize_parent_lookup_code(code: str) -> str:
    """Chuẩn hóa mã bản vẽ trước khi tra cache mã mẹ."""
    return str(code or '').upper().strip()


def get_parent_code_cache(code: str) -> Optional[str]:
    """Lấy mã mẹ đã cache trong database."""
    lookup_code = normalize_parent_lookup_code(code)
    if not lookup_code:
        return None

    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'SELECT parent_code FROM parent_code_cache WHERE engineer_fig_no = ?',
            (lookup_code,)
        )
        row = cursor.fetchone()
        conn.close()
        return row['parent_code'] if row else None
    except Exception as e:
        print(f"[DB] Error reading parent_code_cache: {e}")
        return None


def get_parent_code_cache_many(codes: List[str]) -> Dict[str, str]:
    """Lấy nhiều mã mẹ đã cache, trả về mapping theo input code gốc."""
    normalized_to_original = {}
    for code in codes:
        lookup_code = normalize_parent_lookup_code(code)
        if lookup_code:
            normalized_to_original[lookup_code] = code

    if not normalized_to_original:
        return {}

    try:
        conn = get_connection()
        cursor = conn.cursor()
        placeholders = ', '.join(['?' for _ in normalized_to_original])
        cursor.execute(
            f'SELECT engineer_fig_no, parent_code FROM parent_code_cache WHERE engineer_fig_no IN ({placeholders})',
            list(normalized_to_original.keys())
        )
        rows = cursor.fetchall()
        conn.close()
        return {
            normalized_to_original[row['engineer_fig_no']]: row['parent_code']
            for row in rows
        }
    except Exception as e:
        print(f"[DB] Error reading parent_code_cache batch: {e}")
        return {}


def save_parent_code_cache(code: str, parent_code: str, source: str = 'excel') -> bool:
    """Lưu mã mẹ đã tìm thấy để lần sau không cần quét Excel nữa."""
    lookup_code = normalize_parent_lookup_code(code)
    clean_parent = str(parent_code or '').strip()
    if not lookup_code or not clean_parent:
        return False

    try:
        now = datetime.now().isoformat()
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO parent_code_cache
                (engineer_fig_no, parent_code, source, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(engineer_fig_no) DO UPDATE SET
                parent_code = excluded.parent_code,
                source = excluded.source,
                updated_at = excluded.updated_at
        ''', (lookup_code, clean_parent, source, now, now))
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB] Error saving parent_code_cache: {e}")
        return False


# Mapping từ JSON keys sang database columns
JSON_TO_COLUMN_MAP = {
    "Tracking ID": "tracking_id",
    "Ngày": "Created_Date",
    "Khách hàng": "khach_hang",
    "Nhân viên kinh doanh": "nhan_vien_kinh_doanh",
    "Nhân viên KD": "nhan_vien_kinh_doanh",  # Thêm mapping cho frontend
    "Tên sản phẩm": "ten_san_pham",
    "Quy cách": "quy_cach",
    "客户技术要求": "khach_hang_yeu_cau_ky_thuat",
    "Yêu cầu kỹ thuật KH": "khach_hang_yeu_cau_ky_thuat",
    "Người liên hệ\n(KH)": "nguoi_lien_he_kh",
    "Người liên hệ (KH)": "nguoi_lien_he_kh",
    "Số lượng": "so_luong",
    "Mã PO": "ma_po",
    "Mã bản vẽ": "ma_ban_ve",
    "Mã bản vẽ kỹ thuật (sau khi đặt hàng)": "ma_ban_ve_ky_thuat",
    "Mã mẹ ": "ma_me",
    "Loại sản phẩm": "loai_san_pham",
    "Nhân viên thiết kế": "nhan_vien_thiet_ke",
    "Tình trạng hoàn thành dự án": "tinh_trang_hoan_thanh",
    "Mức độ khẩn cấp": "urgency_level",
    "Thời gian mong muốn có bản vẽ": "thoi_gian_mong_muon_ban_ve",
    "Thời gian hoàn thành kế hoạch": "thoi_gian_hoan_thanh_ke_hoach"
}

# Database columns cho projects (normalized)
PROJECT_COLUMNS = [
    "tracking_id", "Created_Date", "khach_hang", "nhan_vien_kinh_doanh",
    "ten_san_pham", "quy_cach", "khach_hang_yeu_cau_ky_thuat", "nguoi_lien_he_kh", "so_luong",
    "ma_po", "ma_ban_ve", "ma_ban_ve_ky_thuat", "ma_me",
    "loai_san_pham", "nhan_vien_thiet_ke", "tinh_trang_hoan_thanh",
    "urgency_level",
    "thoi_gian_mong_muon_ban_ve", "thoi_gian_hoan_thanh_ke_hoach",
    "sales_name", "user_id", "is_pending", "accepted_by",
    "accepted_at", "desired_solution_time"
]

PROJECT_COLUMN_MAPPING = {
    'Ngày': 'Created_Date',
    'Ngày khởi tạo': 'Created_Date',
    'Khách hàng': 'khach_hang',
    'Nhân viên KD': 'nhan_vien_kinh_doanh',
    'Nhân viên kinh doanh': 'nhan_vien_kinh_doanh',
    'Tên sản phẩm': 'ten_san_pham',
    'Quy cách': 'quy_cach',
    '客户技术要求': 'khach_hang_yeu_cau_ky_thuat',
    'Yêu cầu kỹ thuật KH': 'khach_hang_yeu_cau_ky_thuat',
    'khach_hang_yeu_cau_ky_thuat': 'khach_hang_yeu_cau_ky_thuat',
    'Người liên hệ\n(KH)': 'nguoi_lien_he_kh',
    'Người liên hệ (KH)': 'nguoi_lien_he_kh',
    'Số lượng': 'so_luong',
    'Mã PO': 'ma_po',
    'Mã bản vẽ': 'ma_ban_ve',
    'Mã bản vẽ chính': 'ma_ban_ve',
    'Mã bản vẽ phương án (mã trước khi đặt hàng)': 'ma_ban_ve',
    'Mã bản vẽ kỹ thuật': 'ma_ban_ve_ky_thuat',
    'Mã bản vẽ kỹ thuật (sau khi đặt hàng)': 'ma_ban_ve_ky_thuat',
    'Mã bản vẽ kỹ thuật (mã sau khi đặt hàng)': 'ma_ban_ve_ky_thuat',
    'Mã mẹ ': 'ma_me',
    'Mã mẹ': 'ma_me',
    'Mã thành phẩm (Mã mẹ)': 'ma_me',
    'Loại sản phẩm': 'loai_san_pham',
    'Hạng mục': 'loai_san_pham',
    'Nhân viên thiết kế': 'nhan_vien_thiet_ke',
    'Kỹ sư': 'nhan_vien_thiet_ke',
    'Kỹ sư thiết kế': 'nhan_vien_thiet_ke',
    'Tình trạng hoàn thành dự án': 'tinh_trang_hoan_thanh',
    'Tình trạng': 'tinh_trang_hoan_thanh',
    'Mức độ khẩn cấp': 'urgency_level',
    'Tính cấp bách': 'urgency_level',
    'Độ khẩn': 'urgency_level',
    'Thời gian mong muốn có bản vẽ': 'thoi_gian_mong_muon_ban_ve',
    'TG mong muốn': 'thoi_gian_mong_muon_ban_ve',
    'Thời gian hoàn thành kế hoạch': 'thoi_gian_hoan_thanh_ke_hoach',
    'TG hoàn thành': 'thoi_gian_hoan_thanh_ke_hoach',
    'sales_name': 'sales_name',
    'user_id': 'user_id',
    'User ID': 'user_id',
    'sales_id': 'user_id',
    'is_pending': 'is_pending',
    'Trạng thái chờ': 'is_pending',
    'accepted_by': 'accepted_by',
    'Người nhận': 'accepted_by',
    'accepted_at': 'accepted_at',
    'Thời gian nhận': 'accepted_at',
    'urgency_level': 'urgency_level',
    'desired_solution_time': 'desired_solution_time',
}

LOCK_TIMEOUT_SECONDS = 30


def _extract_customer_name(payload: Dict[str, Any]) -> str:
    """Lấy tên khách hàng từ payload theo các key có thể có."""
    if not isinstance(payload, dict):
        return ''

    for key in ('Khách hàng', 'khach_hang', 'khachhang'):
        value = payload.get(key)
        if value is None:
            continue
        name = str(value).strip()
        if name:
            return name
    return ''


def _upsert_customer_name(cursor: sqlite3.Cursor, customer_name: str) -> None:
    """
    Thêm khách hàng vào bảng customers nếu chưa tồn tại.
    Chỉ lưu cột name để không làm thay đổi các thông tin contact hiện có.
    """
    if not customer_name:
        return

    try:
        cursor.execute(
            'INSERT OR IGNORE INTO customers (name) VALUES (?)',
            (customer_name,)
        )
    except sqlite3.OperationalError as e:
        # Tương thích DB cũ chưa có bảng customers
        if 'no such table' not in str(e).lower():
            raise
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS customers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(200) UNIQUE NOT NULL,
                contact_person VARCHAR(100),
                phone VARCHAR(50),
                email VARCHAR(100),
                address TEXT
            )
        ''')
        cursor.execute(
            'INSERT OR IGNORE INTO customers (name) VALUES (?)',
            (customer_name,)
        )


def ensure_realtime_schema() -> bool:
    """Bổ sung schema phục vụ realtime collaboration nếu DB cũ chưa có."""
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(projects)")
        project_columns = {col[1] for col in cursor.fetchall()}
        if 'version' not in project_columns:
            cursor.execute('ALTER TABLE projects ADD COLUMN version INTEGER DEFAULT 1')
        if 'updated_by' not in project_columns:
            cursor.execute('ALTER TABLE projects ADD COLUMN updated_by TEXT')
        if 'updated_at' not in project_columns:
            cursor.execute('ALTER TABLE projects ADD COLUMN updated_at TEXT')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_cell_locks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                locked_by TEXT NOT NULL,
                locked_by_name TEXT,
                locked_at TEXT NOT NULL,
                expires_at TEXT NOT NULL,
                UNIQUE(tracking_id, field_name)
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_change_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_id INTEGER NOT NULL,
                field_name TEXT NOT NULL,
                old_value TEXT,
                new_value TEXT,
                changed_by TEXT,
                changed_by_name TEXT,
                changed_at TEXT NOT NULL
            )
        ''')
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS project_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                tracking_id INTEGER NOT NULL,
                field_name TEXT,
                comment_text TEXT NOT NULL,
                created_by TEXT,
                created_by_name TEXT,
                created_at TEXT NOT NULL,
                deleted_at TEXT
            )
        ''')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_cell_locks_expires ON project_cell_locks(expires_at)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_change_logs_tracking ON project_change_logs(tracking_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_project_comments_tracking ON project_comments(tracking_id)')
        cursor.execute('UPDATE projects SET version = 1 WHERE version IS NULL')

        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB] Error ensuring realtime schema: {e}")
        return False


def cleanup_expired_project_locks(cursor: sqlite3.Cursor) -> None:
    cursor.execute('DELETE FROM project_cell_locks WHERE expires_at <= ?', (datetime.now().isoformat(),))


def normalize_project_field_name(field_name: str) -> str:
    field = str(field_name or '').strip()
    return PROJECT_COLUMN_MAPPING.get(field, field)


def get_project_version(tracking_id: int) -> Optional[int]:
    ensure_realtime_schema()
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT version FROM projects WHERE tracking_id = ?', (tracking_id,))
    row = cursor.fetchone()
    conn.close()
    return int(row['version']) if row and row['version'] is not None else None


def get_active_project_locks() -> List[Dict[str, Any]]:
    ensure_realtime_schema()
    conn = get_connection()
    cursor = conn.cursor()
    cleanup_expired_project_locks(cursor)
    cursor.execute('''
        SELECT tracking_id, field_name, locked_by, locked_by_name, locked_at, expires_at
        FROM project_cell_locks
        ORDER BY locked_at DESC
    ''')
    rows = [dict(row) for row in cursor.fetchall()]
    conn.commit()
    conn.close()
    return rows


def lock_project_cell(tracking_id: int, field_name: str, locked_by: str, locked_by_name: str = '') -> Dict[str, Any]:
    ensure_realtime_schema()
    db_field = normalize_project_field_name(field_name)
    now = datetime.now()
    expires_at = now + timedelta(seconds=LOCK_TIMEOUT_SECONDS)
    conn = get_connection()
    cursor = conn.cursor()
    cleanup_expired_project_locks(cursor)

    cursor.execute(
        'SELECT * FROM project_cell_locks WHERE tracking_id = ? AND field_name = ?',
        (tracking_id, db_field)
    )
    existing = cursor.fetchone()
    if existing and str(existing['locked_by']) != str(locked_by):
        conn.close()
        return {
            "success": False,
            "error": "Ô này đang được người khác chỉnh sửa",
            "lock": dict(existing)
        }

    cursor.execute('''
        INSERT INTO project_cell_locks (tracking_id, field_name, locked_by, locked_by_name, locked_at, expires_at)
        VALUES (?, ?, ?, ?, ?, ?)
        ON CONFLICT(tracking_id, field_name) DO UPDATE SET
            locked_by = excluded.locked_by,
            locked_by_name = excluded.locked_by_name,
            locked_at = excluded.locked_at,
            expires_at = excluded.expires_at
    ''', (tracking_id, db_field, locked_by, locked_by_name, now.isoformat(), expires_at.isoformat()))
    conn.commit()
    conn.close()
    return {
        "success": True,
        "lock": {
            "tracking_id": tracking_id,
            "field_name": db_field,
            "locked_by": locked_by,
            "locked_by_name": locked_by_name,
            "locked_at": now.isoformat(),
            "expires_at": expires_at.isoformat()
        }
    }


def unlock_project_cell(tracking_id: int, field_name: str, locked_by: str = '') -> bool:
    ensure_realtime_schema()
    db_field = normalize_project_field_name(field_name)
    conn = get_connection()
    cursor = conn.cursor()
    if locked_by:
        cursor.execute(
            'DELETE FROM project_cell_locks WHERE tracking_id = ? AND field_name = ? AND locked_by = ?',
            (tracking_id, db_field, locked_by)
        )
    else:
        cursor.execute(
            'DELETE FROM project_cell_locks WHERE tracking_id = ? AND field_name = ?',
            (tracking_id, db_field)
        )
    conn.commit()
    changed = cursor.rowcount > 0
    conn.close()
    return changed


def migrate_json_to_columns():
    """
    Migration: Parse JSON từ cột 'data' và insert vào các columns riêng biệt
    Returns: (success: bool, migrated_count: int)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Kiểm tra nếu bảng đã có columns mới
        cursor.execute("PRAGMA table_info(projects)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "Created_Date" in columns:
            print("[DB] Projects table already normalized (has 'Created_Date' column)")
            conn.close()
            return True, 0
        
        print("[DB] Starting JSON to columns migration...")

        # Determine which user identifier column exists in old table
        user_id_col = 'user_id' if 'user_id' in columns else 'sales_id'

        # Build SELECT column list (old table schema)
        select_cols = ['tracking_id', 'data', 'sales_name', user_id_col, 'is_pending', 'accepted_by', 'accepted_at', 'urgency_level', 'desired_solution_time']

        cursor.execute(f"SELECT {', '.join(select_cols)} FROM projects")
        rows = cursor.fetchall()

        # Tạo bảng mới với schema normalized (luôn thực hiện, ngay cả khi không có dữ liệu)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS projects_new (
                tracking_id INTEGER PRIMARY KEY,
                Created_Date DATE,
                khach_hang VARCHAR(200),
                nhan_vien_kinh_doanh VARCHAR(100),
                ten_san_pham VARCHAR(200),
                quy_cach TEXT,
                khach_hang_yeu_cau_ky_thuat TEXT,
                nguoi_lien_he_kh VARCHAR(100),
                so_luong INTEGER,
                ma_po VARCHAR(50),
                ma_ban_ve VARCHAR(50),
                ma_ban_ve_ky_thuat VARCHAR(50),
                ma_me VARCHAR(50),
                loai_san_pham VARCHAR(100),
                nhan_vien_thiet_ke VARCHAR(100),
                tinh_trang_hoan_thanh VARCHAR(100),
                urgency_level VARCHAR(20),
                thoi_gian_mong_muon_ban_ve TEXT,
                thoi_gian_hoan_thanh_ke_hoach TEXT,
                sales_name VARCHAR(100),
                user_id INTEGER,
                is_pending VARCHAR(10) DEFAULT 'no',
                accepted_by VARCHAR(100),
                accepted_at TEXT,
                desired_solution_time TEXT
            )
        ''')
        
        migrated_count = 0
        if rows:
            for row in rows:
                tracking_id = row['tracking_id']
                metadata = {
                    'sales_name': row['sales_name'],
                    'user_id': row[user_id_col],  # Map from either user_id or sales_id
                    'is_pending': row['is_pending'],
                    'accepted_by': row['accepted_by'],
                    'accepted_at': row['accepted_at'],
                    'urgency_level': row['urgency_level'],
                    'desired_solution_time': row['desired_solution_time']
                }
                
                # Parse JSON
                try:
                    data_json = json.loads(row['data']) if row['data'] else {}
                except:
                    data_json = {}
                
                # Map JSON sang columns
                record = {'tracking_id': tracking_id}
                for json_key, col_name in JSON_TO_COLUMN_MAP.items():
                    record[col_name] = data_json.get(json_key, '')
                
                # Thêm metadata
                for key, value in metadata.items():
                    if value is not None:
                        record[key] = value
                
                # Insert vào bảng mới
                placeholders = ', '.join(['?' for _ in PROJECT_COLUMNS])
                insert_cols = ', '.join(PROJECT_COLUMNS)
                values = [record.get(col) for col in PROJECT_COLUMNS]
                
                cursor.execute(
                    f"INSERT INTO projects_new ({insert_cols}) VALUES ({placeholders})",
                    values
                )
                migrated_count += 1
        else:
            print("[DB] No data to migrate, but creating new table anyway")
        
        # Xóa bảng cũ và đổi tên
        cursor.execute("DROP TABLE projects")
        cursor.execute("ALTER TABLE projects_new RENAME TO projects")
        
        # Tạo indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_created_date ON projects(Created_Date)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_khach_hang ON projects(khach_hang)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_user_id ON projects(user_id)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_pending ON projects(is_pending)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_ma_po ON projects(ma_po)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_projects_ten_san_pham ON projects(ten_san_pham)')
        
        conn.commit()
        conn.close()
        
        print(f"[DB] Migration completed: {migrated_count} records migrated")
        return True, migrated_count
        
    except Exception as e:
        print(f"[DB] Error migrating JSON to columns: {e}")
        import traceback
        traceback.print_exc()
        return False, 0


def load_all():
    """
    Load tất cả dữ liệu từ DB.db
    Sử dụng in-memory cache để tăng hiệu suất
    Returns: list of dictionaries (danh sách records)
    """
    global _data_cache, _cache_loaded
    
    # Return cached data if available
    if _cache_loaded and _data_cache is not None:
        return _data_cache
    
    try:
        if not os.path.exists(DB_PATH):
            print(f"[DB] Database file {DB_PATH} not found, creating new one")
            init_db_v2()
            return []
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Kiểm tra schema - nếu có column 'Created_Date' thì dùng normalized query
        cursor.execute("PRAGMA table_info(projects)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "Created_Date" in columns:
            # Schema mới - đọc trực tiếp từ columns
            cursor.execute('SELECT * FROM projects ORDER BY tracking_id DESC')
            rows = cursor.fetchall()
            conn.close()
            
            # Chuyển đổi sang format cũ để tương thích với UI
            # Lưu ý: sales_name được map về "Nhân viên kinh doanh" thay vì metadata riêng
            data = []
            for row in rows:
                record = dict(row)
                # Lấy giá trị sales_name hoặc fallback về nhan_vien_kinh_doanh
                sales_name_value = record.get("sales_name") or record.get("nhan_vien_kinh_doanh", "")
                
                # Rename columns về format cũ (với khoảng trắng)
                # Bao gồm cả "Nhân viên KD" cho frontend
                old_format = {
                    "Tracking ID": record.get("tracking_id"),
                    "Ngày": record.get("Created_Date"),
                    "Ngày khởi tạo": record.get("Created_Date"),
                    "Khách hàng": record.get("khach_hang"),
                    "Nhân viên KD": sales_name_value,  # Thêm cho frontend
                    "Nhân viên kinh doanh": sales_name_value,
                    "Tên sản phẩm": record.get("ten_san_pham"),
                    "Quy cách": record.get("quy_cach"),
                    "客户技术要求": record.get("khach_hang_yeu_cau_ky_thuat"),
                    "Yêu cầu kỹ thuật KH": record.get("khach_hang_yeu_cau_ky_thuat"),
                    "Người liên hệ\n(KH)": record.get("nguoi_lien_he_kh"),
                    "Người liên hệ (KH)": record.get("nguoi_lien_he_kh"),
                    "Số lượng": record.get("so_luong"),
                    "Mã PO": record.get("ma_po"),
                    "Mã bản vẽ": record.get("ma_ban_ve"),
                    "Mã bản vẽ phương án (mã trước khi đặt hàng)": record.get("ma_ban_ve"),
                    "Mã bản vẽ kỹ thuật (sau khi đặt hàng)": record.get("ma_ban_ve_ky_thuat"),
                    "Mã bản vẽ kỹ thuật (mã sau khi đặt hàng)": record.get("ma_ban_ve_ky_thuat"),
                    "Mã mẹ ": record.get("ma_me"),
                    "Mã thành phẩm (Mã mẹ)": record.get("ma_me"),
                    "Loại sản phẩm": record.get("loai_san_pham"),
                    "Hạng mục": record.get("loai_san_pham"),
                    "Nhân viên thiết kế": record.get("nhan_vien_thiet_ke"),
                    "Kỹ sư": record.get("nhan_vien_thiet_ke"),
                    "Kỹ sư thiết kế": record.get("nhan_vien_thiet_ke"),
                    "Tình trạng hoàn thành dự án": record.get("tinh_trang_hoan_thanh"),
                    "Mức độ khẩn cấp": record.get("urgency_level"),
                    "Thời gian mong muốn có bản vẽ": record.get("thoi_gian_mong_muon_ban_ve"),
                    "Thời gian hoàn thành kế hoạch": record.get("thoi_gian_hoan_thanh_ke_hoach"),
                    # Metadata columns (không bao gồm sales_name vì đã gộp vào Nhân viên kinh doanh)
                    "user_id": record.get("user_id"),
                    "User ID": record.get("user_id"),
                    "is_pending": record.get("is_pending"),
                    "Trạng thái chờ": record.get("is_pending"),
                    "accepted_by": record.get("accepted_by"),
                    "Người nhận": record.get("accepted_by"),
                    "accepted_at": record.get("accepted_at"),
                    "Thời gian nhận": record.get("accepted_at"),
                    "urgency_level": record.get("urgency_level"),
                    "Mức độ khẩn cấp": record.get("urgency_level"),
                    "desired_solution_time": record.get("desired_solution_time"),
                    "version": record.get("version") or 1,
                    "updated_by": record.get("updated_by"),
                    "updated_at": record.get("updated_at")
                }
                data.append(old_format)
        else:
            # Schema cũ - đọc từ JSON
            cursor.execute('SELECT tracking_id, data FROM projects ORDER BY tracking_id DESC')
            rows = cursor.fetchall()
            conn.close()
            
            # Chuyển đổi từ JSON string sang dictionary
            data = []
            for row in rows:
                record = json.loads(row['data'])
                data.append(record)
            
            # Auto-migrate
            print("[DB] Auto-migrating JSON to columns...")
            migrate_json_to_columns()
        
        print(f"[DB] Loaded {len(data)} records from database")
        
        # Save to cache
        _data_cache = data
        _cache_loaded = True
        
        return data
    
    except Exception as e:
        print(f"[DB] Error loading data: {e}")
        return []


def invalidate_cache():
    """
    Xóa cache để buộc load lại dữ liệu từ DB
    Được gọi khi có thay đổi dữ liệu (add, update, delete)
    """
    global _data_cache, _cache_loaded
    _data_cache = None
    _cache_loaded = False
    print("[DB] Cache invalidated")


def save_all(data):
    """
    Lưu tất cả dữ liệu vào DB
    Args:
        data: list of dictionaries (danh sách records)
    Returns: bool
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Xóa tất cả dữ liệu cũ
        cursor.execute('DELETE FROM projects')
        
        # Thêm dữ liệu mới vào columns
        for record in data:
            tracking_id = record.get('Tracking ID')
            
            # Map từ format cũ sang columns
            # Hỗ trợ nhiều key: 'Mã mẹ ', 'Mã mẹ', 'Mã thành phẩm (Mã mẹ)'
            ma_me = record.get('Mã mẹ ') or record.get('Mã mẹ') or record.get('Mã thành phẩm (Mã mẹ)', '')
            nguoi_lien_he = record.get('Người liên hệ\n(KH)') or record.get('Người liên hệ (KH)', '')
            
            # Xử lý nhân viên KD - hỗ trợ cả 'Nhân viên KD' và 'Nhân viên kinh doanh'
            nhan_vien_kd = record.get('Nhân viên KD') or record.get('Nhân viên kinh doanh') or ''
            
            values = [
                tracking_id,
                record.get('Ngày'),
                record.get('Khách hàng'),
                nhan_vien_kd,  # Sử dụng biến đã xử lý
                record.get('Tên sản phẩm'),
                record.get('Quy cách'),
                record.get('客户技术要求') or record.get('Yêu cầu kỹ thuật KH'),
                nguoi_lien_he,
                record.get('Số lượng'),
                record.get('Mã PO'),
                record.get('Mã bản vẽ'),
                record.get('Mã bản vẽ kỹ thuật (sau khi đặt hàng)'),
                ma_me,
                record.get('Loại sản phẩm'),
                record.get('Nhân viên thiết kế'),
                record.get('Tình trạng hoàn thành dự án'),
                record.get('Tính cấp bách') or record.get('Mức độ khẩn cấp') or record.get('Độ khẩn'),
                record.get('Thời gian mong muốn có bản vẽ'),
                record.get('Thời gian hoàn thành kế hoạch'),
                None, None, 'no', None, None, None
            ]
            
            placeholders = ', '.join(['?' for _ in PROJECT_COLUMNS])
            insert_cols = ', '.join(PROJECT_COLUMNS)
            
            cursor.execute(
                f"INSERT INTO projects ({insert_cols}) VALUES ({placeholders})",
                values
            )
        
        conn.commit()
        conn.close()
        
        # Invalidate cache
        invalidate_cache()
        
        print(f"[DB] Saved {len(data)} records to database")
        return True
    
    except Exception as e:
        print(f"[DB] Error saving data: {e}")
        return False


def add_record(record):
    """
    Thêm một bản ghi mới
    Args:
        record: dictionary (bản ghi mới)
    Returns:
        record với tracking_id mới, hoặc None nếu lỗi
    """
    try:
        # Debug: log schema và dữ liệu đầu vào
        conn_check = get_connection()
        cursor_check = conn_check.cursor()
        cursor_check.execute("PRAGMA table_info(projects)")
        cols = [col[1] for col in cursor_check.fetchall()]
        print(f"[DB DEBUG] add_record - Current columns: {cols}")
        # Encode keys safely to avoid Windows console encoding errors (e.g. cp936/gbk)
        safe_record_keys = [str(k).encode('ascii', errors='backslashreplace').decode('ascii') for k in record.keys()]
        print(f"[DB DEBUG] add_record - Input record keys: {safe_record_keys}")
        conn_check.close()
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Lấy tracking_id lớn nhất hiện tại
        cursor.execute('SELECT MAX(tracking_id) as max_id FROM projects')
        result = cursor.fetchone()
        new_tracking_id = (result['max_id'] or 0) + 1
        
        # Map từ format cũ sang columns
        # Hỗ trợ nhiều key: 'Mã mẹ ', 'Mã mẹ', 'Mã thành phẩm (Mã mẹ)'
        ma_me = record.get('Mã mẹ ') or record.get('Mã mẹ') or record.get('Mã thành phẩm (Mã mẹ)', '')
        nguoi_lien_he = record.get('Người liên hệ\n(KH)') or record.get('Người liên hệ (KH)', '')
        
        # Xử lý nhân viên KD - hỗ trợ cả 'Nhân viên KD' và 'Nhân viên kinh doanh'
        nhan_vien_kd = record.get('Nhân viên KD') or record.get('Nhân viên kinh doanh') or ''
        
        # Xử lý Nhân viên thiết kế - hỗ trợ 'Nhân viên thiết kế', 'Kỹ sư', 'Kỹ sư thiết kế'
        nhan_vien_thiet_ke = record.get('Nhân viên thiết kế') or record.get('Kỹ sư') or record.get('Kỹ sư thiết kế') or ''
        
        # Xử lý Tình trạng - hỗ trợ 'Tình trạng hoàn thành dự án', 'Tình trạng'
        tinh_trang = record.get('Tình trạng hoàn thành dự án') or record.get('Tình trạng') or ''
        
        # Xử lý Mức độ khẩn cấp - hỗ trợ 'Mức độ khẩn cấp', 'Tính cấp bách', 'Độ khẩn'
        muc_khan = record.get('Mức độ khẩn cấp') or record.get('Tính cấp bách') or record.get('Độ khẩn') or ''
        
        values = [
            new_tracking_id,                                      # tracking_id
            record.get('Ngày'),                                    # Created_Date
            record.get('Khách hàng'),                              # khach_hang
            nhan_vien_kd,                                         # nhan_vien_kinh_doanh
            record.get('Tên sản phẩm'),                            # ten_san_pham
            record.get('Quy cách'),                                # quy_cách
            record.get('客户技术要求') or record.get('Yêu cầu kỹ thuật KH'),  # khach_hang_yeu_cau_ky_thuat
            nguoi_lien_he,                                        # nguoi_lien_he_kh
            record.get('Số lượng'),                                # so_luong
            record.get('Mã PO'),                                   # ma_po
            record.get('Mã bản vẽ') or record.get('Mã bản vẽ chính'),  # ma_ban_ve
            record.get('Mã bản vẽ kỹ thuật (sau khi đặt hàng)') or record.get('Mã bản vẽ kỹ thuật'),  # ma_ban_ve_ky_thuat
            ma_me,                                                # ma_me
            record.get('Loại sản phẩm'),                           # loai_san_pham
            nhan_vien_thiet_ke,                                   # nhan_vien_thiet_ke
            tinh_trang,                                           # tinh_trang_hoan_thanh
            muc_khan,                                             # urgency_level
            record.get('Thời gian mong muốn có bản vẽ') or record.get('TG mong muốn'),   # thoi_gian_mong_muon_ban_ve
            record.get('Thời gian hoàn thành kế hoạch') or record.get('TG hoàn thành'), # thoi_gian_hoan_thanh_ke_hoach
            record.get('sales_name'),                              # sales_name
            record.get('user_id') or record.get('sales_id'),       # user_id
            record.get('is_pending', 'no'),                        # is_pending
            record.get('accepted_by'),                             # accepted_by
            record.get('accepted_at'),                             # accepted_at
            record.get('desired_solution_time')                   # desired_solution_time
        ]
        
        placeholders = ', '.join(['?' for _ in PROJECT_COLUMNS])
        insert_cols = ', '.join(PROJECT_COLUMNS)
        
        cursor.execute(
            f"INSERT INTO projects ({insert_cols}) VALUES ({placeholders})",
            values
        )

        # Đồng bộ danh sách khách hàng từ dữ liệu project vào bảng customers
        customer_name = _extract_customer_name(record)
        _upsert_customer_name(cursor, customer_name)
        
        record['Tracking ID'] = new_tracking_id
        
        conn.commit()
        conn.close()
        
        # Invalidate cache
        invalidate_cache()
        
        print(f"[DB] Added record with tracking_id={new_tracking_id}")
        return record
    
    except Exception as e:
        print(f"[DB] Error adding record: {e}")
        import traceback
        traceback.print_exc()
        return None


def update_record(tracking_id, new_data):
    """
    Cập nhật một bản ghi theo tracking_id
    Args:
        tracking_id: int
        new_data: dictionary (dữ liệu mới)
    Returns:
        bool: True nếu thành công, False nếu lỗi
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Kiểm tra schema
        cursor.execute("PRAGMA table_info(projects)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "Created_Date" in columns:
            # Schema mới - update columns riêng biệt
            # Xây dựng SET clause (không có updated_at)
            set_clauses = []
            values = []
            
            ensure_realtime_schema()

            for old_key, col_name in PROJECT_COLUMN_MAPPING.items():
                if old_key in new_data:
                    set_clauses.append(f"{col_name} = ?")
                    values.append(new_data[old_key])

            if not set_clauses:
                conn.close()
                return False

            set_clauses.append("version = COALESCE(version, 1) + 1")
            set_clauses.append("updated_at = ?")
            values.append(datetime.now().isoformat())
            if 'updated_by' in columns:
                set_clauses.append("updated_by = ?")
                values.append(str(new_data.get('updated_by') or new_data.get('changed_by') or ''))
            
            values.append(tracking_id)
            
            query = f"UPDATE projects SET {', '.join(set_clauses)} WHERE tracking_id = ?"
            cursor.execute(query, values)
        else:
            # Schema cũ - update JSON
            new_data['Tracking ID'] = tracking_id
            data_json = json.dumps(new_data, ensure_ascii=False)
            
            cursor.execute(
                'UPDATE projects SET data = ?, updated_at = ? WHERE tracking_id = ?',
                (data_json, datetime.now().isoformat(), tracking_id)
            )
        
        # Nếu payload có tên khách hàng thì tự thêm vào bảng customers
        customer_name = _extract_customer_name(new_data)
        _upsert_customer_name(cursor, customer_name)

        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        
        # Invalidate cache
        invalidate_cache()
        
        print(f"[DB] Updated record tracking_id={tracking_id}, success={success}")
        return success
    
    except Exception as e:
        print(f"[DB] Error updating record: {e}")
        import traceback
        traceback.print_exc()
        return False


def update_project_with_version(
    tracking_id: int,
    new_data: Dict[str, Any],
    expected_version: Optional[int],
    changed_by: str = '',
    changed_by_name: str = ''
) -> Dict[str, Any]:
    """Update project với optimistic locking và ghi change log."""
    ensure_realtime_schema()
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cleanup_expired_project_locks(cursor)
        cursor.execute('SELECT * FROM projects WHERE tracking_id = ?', (tracking_id,))
        current = cursor.fetchone()
        if not current:
            conn.close()
            return {"success": False, "error": "Không tìm thấy dự án", "status": 404}

        current_dict = dict(current)
        current_version = int(current_dict.get('version') or 1)
        if expected_version is not None and int(expected_version) != current_version:
            conn.close()
            return {
                "success": False,
                "error": "Dữ liệu đã được người khác cập nhật. Vui lòng tải lại trước khi lưu.",
                "code": "VERSION_CONFLICT",
                "status": 409,
                "current_version": current_version
            }

        db_updates = {}
        for old_key, value in new_data.items():
            db_col = PROJECT_COLUMN_MAPPING.get(old_key)
            if db_col and db_col not in {'tracking_id', 'version', 'updated_at', 'updated_by'}:
                db_updates[db_col] = value

        if not db_updates:
            conn.close()
            return {"success": False, "error": "Không có trường hợp lệ để cập nhật", "status": 400}

        for db_col in db_updates:
            cursor.execute(
                'SELECT * FROM project_cell_locks WHERE tracking_id = ? AND field_name = ?',
                (tracking_id, db_col)
            )
            lock = cursor.fetchone()
            if lock and changed_by and str(lock['locked_by']) != str(changed_by):
                conn.close()
                return {
                    "success": False,
                    "error": "Ô này đang được người khác chỉnh sửa",
                    "code": "CELL_LOCKED",
                    "status": 423,
                    "lock": dict(lock)
                }

        now = datetime.now().isoformat()
        set_clauses = [f"{db_col} = ?" for db_col in db_updates]
        values = list(db_updates.values())
        set_clauses.extend(["version = ?", "updated_at = ?", "updated_by = ?"])
        new_version = current_version + 1
        values.extend([new_version, now, str(changed_by or changed_by_name or '')])
        values.append(tracking_id)
        cursor.execute(
            f"UPDATE projects SET {', '.join(set_clauses)} WHERE tracking_id = ?",
            values
        )

        for db_col, new_value in db_updates.items():
            old_value = current_dict.get(db_col)
            if str(old_value or '') == str(new_value or ''):
                continue
            cursor.execute('''
                INSERT INTO project_change_logs
                    (tracking_id, field_name, old_value, new_value, changed_by, changed_by_name, changed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                tracking_id,
                db_col,
                '' if old_value is None else str(old_value),
                '' if new_value is None else str(new_value),
                str(changed_by or ''),
                str(changed_by_name or ''),
                now
            ))
            if changed_by:
                cursor.execute(
                    'DELETE FROM project_cell_locks WHERE tracking_id = ? AND field_name = ? AND locked_by = ?',
                    (tracking_id, db_col, str(changed_by))
                )

        customer_name = _extract_customer_name(new_data)
        _upsert_customer_name(cursor, customer_name)

        conn.commit()
        conn.close()
        invalidate_cache()
        updated_record = get_record_by_id(tracking_id)
        return {
            "success": True,
            "record": updated_record,
            "version": new_version,
            "changed_fields": list(db_updates.keys())
        }
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"[DB] Error update_project_with_version: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e), "status": 500}


def get_project_change_logs(tracking_id: int, field_name: str = '', limit: int = 100) -> List[Dict[str, Any]]:
    """Lấy lịch sử chỉnh sửa của một project, có thể lọc theo field."""
    ensure_realtime_schema()
    db_field = normalize_project_field_name(field_name) if field_name else ''
    safe_limit = max(1, min(int(limit or 100), 500))

    try:
        conn = get_connection()
        cursor = conn.cursor()
        if db_field:
            cursor.execute('''
                SELECT id, tracking_id, field_name, old_value, new_value, changed_by, changed_by_name, changed_at
                FROM project_change_logs
                WHERE tracking_id = ? AND field_name = ?
                ORDER BY changed_at DESC, id DESC
                LIMIT ?
            ''', (tracking_id, db_field, safe_limit))
        else:
            cursor.execute('''
                SELECT id, tracking_id, field_name, old_value, new_value, changed_by, changed_by_name, changed_at
                FROM project_change_logs
                WHERE tracking_id = ?
                ORDER BY changed_at DESC, id DESC
                LIMIT ?
            ''', (tracking_id, safe_limit))
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[DB] Error reading project change logs: {e}")
        return []


def get_project_change_log(change_id: int) -> Optional[Dict[str, Any]]:
    """Lấy một dòng audit log theo id."""
    ensure_realtime_schema()
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, tracking_id, field_name, old_value, new_value, changed_by, changed_by_name, changed_at
            FROM project_change_logs
            WHERE id = ?
        ''', (change_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"[DB] Error reading project change log: {e}")
        return None


def revert_project_change_log(
    change_id: int,
    expected_version: Optional[int],
    changed_by: str = '',
    changed_by_name: str = ''
) -> Dict[str, Any]:
    """Hoàn tác một thay đổi đã ghi trong project_change_logs."""
    ensure_realtime_schema()
    conn = get_connection()
    cursor = conn.cursor()

    try:
        cleanup_expired_project_locks(cursor)
        cursor.execute('''
            SELECT id, tracking_id, field_name, old_value, new_value, changed_by, changed_by_name, changed_at
            FROM project_change_logs
            WHERE id = ?
        ''', (change_id,))
        log = cursor.fetchone()
        if not log:
            conn.close()
            return {"success": False, "error": "Không tìm thấy lịch sử chỉnh sửa", "status": 404}

        log_dict = dict(log)
        tracking_id = int(log_dict['tracking_id'])
        db_col = normalize_project_field_name(log_dict.get('field_name'))
        if db_col not in PROJECT_COLUMNS or db_col in {'tracking_id', 'version', 'updated_at', 'updated_by'}:
            conn.close()
            return {"success": False, "error": "Trường này không hỗ trợ hoàn tác", "status": 400}

        cursor.execute('SELECT * FROM projects WHERE tracking_id = ?', (tracking_id,))
        current = cursor.fetchone()
        if not current:
            conn.close()
            return {"success": False, "error": "Không tìm thấy dự án", "status": 404}

        current_dict = dict(current)
        current_version = int(current_dict.get('version') or 1)
        if expected_version is not None and int(expected_version) != current_version:
            conn.close()
            return {
                "success": False,
                "error": "Dữ liệu đã được người khác cập nhật. Vui lòng tải lại trước khi hoàn tác.",
                "code": "VERSION_CONFLICT",
                "status": 409,
                "current_version": current_version
            }

        cursor.execute(
            'SELECT * FROM project_cell_locks WHERE tracking_id = ? AND field_name = ?',
            (tracking_id, db_col)
        )
        lock = cursor.fetchone()
        if lock and changed_by and str(lock['locked_by']) != str(changed_by):
            conn.close()
            return {
                "success": False,
                "error": "Ô này đang được người khác chỉnh sửa",
                "code": "CELL_LOCKED",
                "status": 423,
                "lock": dict(lock)
            }

        now = datetime.now().isoformat()
        old_current_value = current_dict.get(db_col)
        revert_value = log_dict.get('old_value') or ''
        new_version = current_version + 1
        cursor.execute(
            f'UPDATE projects SET {db_col} = ?, version = ?, updated_at = ?, updated_by = ? WHERE tracking_id = ?',
            (revert_value, new_version, now, str(changed_by or changed_by_name or ''), tracking_id)
        )

        if str(old_current_value or '') != str(revert_value or ''):
            cursor.execute('''
                INSERT INTO project_change_logs
                    (tracking_id, field_name, old_value, new_value, changed_by, changed_by_name, changed_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                tracking_id,
                db_col,
                '' if old_current_value is None else str(old_current_value),
                '' if revert_value is None else str(revert_value),
                str(changed_by or ''),
                str(changed_by_name or ''),
                now
            ))

        if changed_by:
            cursor.execute(
                'DELETE FROM project_cell_locks WHERE tracking_id = ? AND field_name = ? AND locked_by = ?',
                (tracking_id, db_col, str(changed_by))
            )

        conn.commit()
        conn.close()
        invalidate_cache()
        return {
            "success": True,
            "record": get_record_by_id(tracking_id),
            "version": new_version,
            "tracking_id": tracking_id,
            "changed_fields": [db_col],
            "reverted_change_id": change_id
        }
    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"[DB] Error revert_project_change_log: {e}")
        import traceback
        traceback.print_exc()
        return {"success": False, "error": str(e), "status": 500}


def get_project_comments(tracking_id: int, field_name: str = '', include_resolved: bool = False) -> List[Dict[str, Any]]:
    """Lấy bình luận của một project, có thể lọc theo field."""
    ensure_realtime_schema()
    db_field = normalize_project_field_name(field_name) if field_name else ''
    try:
        conn = get_connection()
        cursor = conn.cursor()
        where = ['tracking_id = ?']
        params = [tracking_id]
        if db_field:
            where.append('field_name = ?')
            params.append(db_field)
        if not include_resolved:
            where.append('deleted_at IS NULL')
        cursor.execute(f'''
            SELECT id, tracking_id, field_name, comment_text, created_by, created_by_name, created_at, deleted_at
            FROM project_comments
            WHERE {' AND '.join(where)}
            ORDER BY created_at ASC, id ASC
        ''', params)
        rows = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return rows
    except Exception as e:
        print(f"[DB] Error reading project comments: {e}")
        return []


def add_project_comment(
    tracking_id: int,
    comment_text: str,
    field_name: str = '',
    created_by: str = '',
    created_by_name: str = ''
) -> Optional[Dict[str, Any]]:
    """Thêm bình luận vào project/cell."""
    ensure_realtime_schema()
    text = str(comment_text or '').strip()
    if not text:
        return None
    db_field = normalize_project_field_name(field_name) if field_name else ''
    now = datetime.now().isoformat()
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO project_comments
                (tracking_id, field_name, comment_text, created_by, created_by_name, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (tracking_id, db_field, text, str(created_by or ''), str(created_by_name or ''), now))
        comment_id = cursor.lastrowid
        conn.commit()
        cursor.execute('''
            SELECT id, tracking_id, field_name, comment_text, created_by, created_by_name, created_at, deleted_at
            FROM project_comments
            WHERE id = ?
        ''', (comment_id,))
        row = cursor.fetchone()
        conn.close()
        return dict(row) if row else None
    except Exception as e:
        print(f"[DB] Error adding project comment: {e}")
        return None


def delete_project_comment(comment_id: int, deleted_by: str = '') -> bool:
    """Xóa mềm bình luận."""
    ensure_realtime_schema()
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute(
            'UPDATE project_comments SET deleted_at = ? WHERE id = ? AND deleted_at IS NULL',
            (datetime.now().isoformat(), comment_id)
        )
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        return success
    except Exception as e:
        print(f"[DB] Error deleting project comment: {e}")
        return False


def delete_records(tracking_ids):
    """
    Xóa các bản ghi theo danh sách tracking_ids
    Args:
        tracking_ids: list of int
    Returns:
        int: số bản ghi đã xóa
    """
    try:
        if not tracking_ids:
            return 0
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Xóa theo thứ tự giảm dần để tránh index issues
        for tid in sorted(tracking_ids, reverse=True):
            cursor.execute('DELETE FROM projects WHERE tracking_id = ?', (tid,))
        
        deleted_count = cursor.rowcount
        conn.commit()
        conn.close()
        
        # Invalidate cache
        invalidate_cache()
        
        print(f"[DB] Deleted {deleted_count} records")
        return deleted_count
    
    except Exception as e:
        print(f"[DB] Error deleting records: {e}")
        return 0


def restore_records(records):
    """
    Khôi phục các bản ghi đã xóa, giữ lại tracking_id cũ để undo đúng dòng.
    Args:
        records: list[dict]
    Returns:
        int: số bản ghi đã khôi phục
    """
    if not records:
        return 0

    def first_value(record, *keys):
        for key in keys:
            value = record.get(key)
            if value is not None:
                return value
        return None

    restored = 0
    try:
        conn = get_connection()
        cursor = conn.cursor()
        placeholders = ', '.join(['?' for _ in PROJECT_COLUMNS])
        insert_cols = ', '.join(PROJECT_COLUMNS)

        for record in records:
            if not isinstance(record, dict):
                continue

            tracking_id = first_value(record, 'tracking_id', 'Tracking ID')
            if tracking_id in (None, ''):
                continue

            values = [
                tracking_id,
                first_value(record, 'Created_Date', 'Ngày', 'ngay'),
                first_value(record, 'khach_hang', 'Khách hàng', 'khachhang'),
                first_value(record, 'nhan_vien_kinh_doanh', 'Nhân viên KD', 'Nhân viên kinh doanh', 'nhanvienkd'),
                first_value(record, 'ten_san_pham', 'Tên sản phẩm', 'tensanpham'),
                first_value(record, 'quy_cach', 'Quy cách', 'quycach'),
                first_value(record, 'khach_hang_yeu_cau_ky_thuat', '客户技术要求', 'Yêu cầu kỹ thuật KH', 'yeucaukythuat'),
                first_value(record, 'nguoi_lien_he_kh', 'Người liên hệ (KH)', 'Người liên hệ\n(KH)', 'lienhe'),
                first_value(record, 'so_luong', 'Số lượng', 'soluong'),
                first_value(record, 'ma_po', 'Mã PO', 'mapo'),
                first_value(record, 'ma_ban_ve', 'Mã bản vẽ', 'Mã bản vẽ phương án', 'Mã bản vẽ phương án (mã trước khi đặt hàng)', 'mabave'),
                first_value(record, 'ma_ban_ve_ky_thuat', 'Mã bản vẽ kỹ thuật', 'Mã bản vẽ kỹ thuật (sau khi đặt hàng)', 'mabavkythuat'),
                first_value(record, 'ma_me', 'Mã mẹ', 'Mã mẹ ', 'mame'),
                first_value(record, 'loai_san_pham', 'Loại sản phẩm', 'loaisanpham'),
                first_value(record, 'nhan_vien_thiet_ke', 'Nhân viên thiết kế', 'Kỹ sư thiết kế', 'nhanvienthietke'),
                first_value(record, 'tinh_trang_hoan_thanh', 'Tình trạng hoàn thành dự án', 'Tình trạng', 'tinhtrang'),
                first_value(record, 'urgency_level', 'Tính cấp bách', 'Mức độ khẩn cấp', 'Độ khẩn', 'dokhan'),
                first_value(record, 'thoi_gian_mong_muon_ban_ve', 'Thời gian mong muốn có bản vẽ', 'TG mong muốn', 'tg_mongmuon'),
                first_value(record, 'thoi_gian_hoan_thanh_ke_hoach', 'Thời gian hoàn thành kế hoạch', 'TG hoàn thành', 'tg_hoanthanh'),
                first_value(record, 'sales_name'),
                first_value(record, 'user_id', 'sales_id'),
                first_value(record, 'is_pending', 'Trạng thái chờ', 'trangthai'),
                first_value(record, 'accepted_by', 'Người nhận', 'nguoinhan'),
                first_value(record, 'accepted_at', 'Thời gian nhận', 'tg_tiepnhan'),
                first_value(record, 'desired_solution_time')
            ]

            cursor.execute(
                f"INSERT OR REPLACE INTO projects ({insert_cols}) VALUES ({placeholders})",
                values
            )
            _upsert_customer_name(cursor, _extract_customer_name(record))
            restored += 1

        conn.commit()
        conn.close()
        invalidate_cache()
        print(f"[DB] Restored {restored} records")
        return restored

    except Exception as e:
        print(f"[DB] Error restoring records: {e}")
        import traceback
        traceback.print_exc()
        return restored


def reindex_tracking_id():
    """
    Đánh lại Tracking ID cho tất cả bản ghi (bắt đầu từ 1)
    Returns: bool
    """
    try:
        # Load tất cả dữ liệu
        all_data = load_all()
        
        if not all_data:
            return True
        
        # Sắp xếp theo tracking_id cũ
        all_data.sort(key=lambda x: x.get('Tracking ID', 0))
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Xóa tất cả
        cursor.execute('DELETE FROM projects')
        
        # Thêm lại với tracking_id mới
        for i, record in enumerate(all_data, start=1):
            record['Tracking ID'] = i
            # Hỗ trợ nhiều key: 'Mã mẹ ', 'Mã mẹ', 'Mã thành phẩm (Mã mẹ)'
            ma_me = record.get('Mã mẹ ') or record.get('Mã mẹ') or record.get('Mã thành phẩm (Mã mẹ)', '')
            nguoi_lien_he = record.get('Người liên hệ\n(KH)') or record.get('Người liên hệ (KH)', '')
            
            values = [
                i,
                record.get('Ngày'),
                record.get('Khách hàng'),
                record.get('Nhân viên kinh doanh'),
                record.get('Tên sản phẩm'),
                record.get('Quy cách'),
                record.get('客户技术要求') or record.get('Yêu cầu kỹ thuật KH'),
                nguoi_lien_he,
                record.get('Số lượng'),
                record.get('Mã PO'),
                record.get('Mã bản vẽ'),
                record.get('Mã bản vẽ kỹ thuật (sau khi đặt hàng)'),
                ma_me,
                record.get('Loại sản phẩm'),
                record.get('Nhân viên thiết kế'),
                record.get('Tình trạng hoàn thành dự án'),
                record.get('Tính cấp bách') or record.get('Mức độ khẩn cấp') or record.get('Độ khẩn'),
                record.get('Thời gian mong muốn có bản vẽ'),
                record.get('Thời gian hoàn thành kế hoạch'),
                None, None, 'no', None, None, None
            ]
            
            placeholders = ', '.join(['?' for _ in PROJECT_COLUMNS])
            insert_cols = ', '.join(PROJECT_COLUMNS)
            
            cursor.execute(
                f"INSERT INTO projects ({insert_cols}) VALUES ({placeholders})",
                values
            )
        
        conn.commit()
        conn.close()
        
        print(f"[DB] Reindexed {len(all_data)} records")
        return True
    
    except Exception as e:
        print(f"[DB] Error reindexing: {e}")
        return False


def search_data(data, search_text, columns=None):
    """
    Tìm kiếm trong dữ liệu
    Args:
        data: list of records
        search_text: string to search
        columns: list of columns to search in (optional)
    Returns:
        list: kết quả tìm kiếm
    """
    if not search_text:
        return data
    
    search_text = search_text.lower().strip()
    if not columns:
        columns = []
    
    results = []
    for item in data:
        found = False
        for key, value in item.items():
            if value and search_text in str(value).lower():
                found = True
                break
        if found:
            results.append(item)
    
    return results


def filter_data(data, column_filters):
    """
    Lọc dữ liệu theo column filters
    Args:
        data: list of records
        column_filters: dict {column_key: [selected_values]}
    Returns:
        list: kết quả lọc
    """
    if not column_filters:
        return data
    
    results = []
    for item in data:
        match = True
        for column_key, selected_values in column_filters.items():
            item_value = str(item.get(column_key, ""))
            if item_value not in selected_values:
                match = False
                break
        if match:
            results.append(item)
    
    return results


def search_data_sql(search_text, page=1, limit=50, sort_by="Tracking ID", sort_order="asc"):
    """
    Tìm kiếm TRỰC TIẾP bằng SQL (hiệu suất cao)
    Thay vì load all data rồi filter bằng Python, sử dụng SQL WHERE
    
    Args:
        search_text: string to search
        page: int (trang hiện tại, bắt đầu từ 1)
        limit: int (số bản ghi mỗi trang)
        sort_by: string (tên cột sắp xếp)
        sort_order: string ('asc' hoặc 'desc')
    Returns:
        dict: {data, total, page, limit, total_pages}
    """
    try:
        if not os.path.exists(DB_PATH):
            return {"data": [], "total": 0, "page": page, "limit": limit, "total_pages": 0}
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Kiểm tra schema
        cursor.execute("PRAGMA table_info(projects)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "Created_Date" not in columns:
            # Schema cũ - fallback về Python filter
            conn.close()
            all_data = load_all()
            filtered = search_data(all_data, search_text)
            return get_paged_data(filtered, page, limit, sort_by, sort_order)
        
        # Validate limit
        limit = min(limit, MAX_PROJECT_PAGE_LIMIT)
        offset = (page - 1) * limit
        
        # Build search query with SQL LIKE
        # Tìm kiếm trên nhiều cột quan trọng
        search_columns = [
            "khach_hang", "ten_san_pham", "quy_cach", "khach_hang_yeu_cau_ky_thuat", "ma_po", 
            "ma_ban_ve", "ma_ban_ve_ky_thuat", "ma_me",
            "nhan_vien_kinh_doanh", "nhan_vien_thiet_ke",
            "loai_san_pham", "tinh_trang_hoan_thanh"
        ]
        
        search_pattern = f"%{search_text}%"
        where_clauses = []
        for col in search_columns:
            if col in columns:
                where_clauses.append(f"{col} LIKE ?")
        
        if not where_clauses:
            where_clause = "1=1"
            params = []
        else:
            where_clause = " OR ".join(where_clauses)
            params = [search_pattern] * len(where_clauses)
        
        # Get total count with search
        count_sql = f"SELECT COUNT(*) as total FROM projects WHERE {where_clause}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()["total"]
        
        if total == 0:
            conn.close()
            return {"data": [], "total": 0, "page": page, "limit": limit, "total_pages": 0}
        
        # Map sort_by
        sort_column_map = {
            "Tracking ID": "tracking_id",
            "Ngày": "Created_Date",
            "Khách hàng": "khach_hang",
            "Nhân viên kinh doanh": "nhan_vien_kinh_doanh",
            "Tên sản phẩm": "ten_san_pham",
            "Quy cách": "quy_cach",
            "客户技术要求": "khach_hang_yeu_cau_ky_thuat",
            "Yêu cầu kỹ thuật KH": "khach_hang_yeu_cau_ky_thuat",
            "Số lượng": "so_luong",
            "Mã PO": "ma_po",
            "Mã bản vẽ": "ma_ban_ve",
            "Loại sản phẩm": "loai_san_pham",
            "Tình trạng hoàn thành dự án": "tinh_trang_hoan_thanh"
        }
        
        db_sort_column = sort_column_map.get(sort_by, "tracking_id")
        order_dir = "DESC" if sort_order == "desc" else "ASC"
        
        # Build main query with pagination
        query = f"""
            SELECT * FROM projects 
            WHERE {where_clause}
            ORDER BY {db_sort_column} {order_dir}
            LIMIT ? OFFSET ?
        """
        
        cursor.execute(query, params + [limit, offset])
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to frontend format
        data = _convert_rows_to_format(rows)
        
        total_pages = (total + limit - 1) // limit
        
        return {
            "data": data,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
    
    except Exception as e:
        print(f"[DB] Error in search_data_sql: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to Python filter
        all_data = load_all()
        filtered = search_data(all_data, search_text)
        return get_paged_data(filtered, page, limit, sort_by, sort_order)


def filter_data_sql(column_filters, page=1, limit=50, sort_by="Tracking ID", sort_order="asc"):
    """
    Lọc dữ liệu TRỰC TIẾP bằng SQL (hiệu suất cao)
    
    Args:
        column_filters: dict {column_key: [selected_values]}
        page: int
        limit: int
        sort_by: string
        sort_order: string
    Returns:
        dict: {data, total, page, limit, total_pages}
    """
    try:
        if not os.path.exists(DB_PATH):
            return {"data": [], "total": 0, "page": page, "limit": limit, "total_pages": 0}
        
        if not column_filters:
            return get_paged_data_sql(page, limit, sort_by, sort_order)
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Kiểm tra schema
        cursor.execute("PRAGMA table_info(projects)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "Created_Date" not in columns:
            conn.close()
            all_data = load_all()
            filtered = filter_data(all_data, column_filters)
            return get_paged_data(filtered, page, limit, sort_by, sort_order)
        
        # Validate limit
        limit = min(limit, MAX_PROJECT_PAGE_LIMIT)
        offset = (page - 1) * limit
        
        # Build WHERE clauses from filters
        # Map frontend column names to DB columns
        filter_column_map = {
            "Khách hàng": "khach_hang",
            "Nhân viên kinh doanh": "nhan_vien_kinh_doanh",
            "Tên sản phẩm": "ten_san_pham",
            "Quy cách": "quy_cach",
            "客户技术要求": "khach_hang_yeu_cau_ky_thuat",
            "Yêu cầu kỹ thuật KH": "khach_hang_yeu_cau_ky_thuat",
            "Loại sản phẩm": "loai_san_pham",
            "Mã PO": "ma_po",
            "Tình trạng hoàn thành dự án": "tinh_trang_hoan_thanh"
        }
        
        where_clauses = []
        params = []
        
        for col_key, selected_values in column_filters.items():
            if not selected_values:
                continue
            
            db_col = filter_column_map.get(col_key, col_key)
            if db_col in columns:
                # Use IN clause for multiple values
                placeholders = ','.join(['?' for _ in selected_values])
                where_clauses.append(f"{db_col} IN ({placeholders})")
                params.extend(selected_values)
        
        if not where_clauses:
            where_clause = "1=1"
        else:
            where_clause = " AND ".join(where_clauses)
        
        # Get total count
        count_sql = f"SELECT COUNT(*) as total FROM projects WHERE {where_clause}"
        cursor.execute(count_sql, params)
        total = cursor.fetchone()["total"]
        
        if total == 0:
            conn.close()
            return {"data": [], "total": 0, "page": page, "limit": limit, "total_pages": 0}
        
        # Map sort_by
        sort_column_map = {
            "Tracking ID": "tracking_id",
            "Ngày": "Created_Date",
            "Khách hàng": "khach_hang",
            "Nhân viên kinh doanh": "nhan_vien_kinh_doanh",
            "Tên sản phẩm": "ten_san_pham",
            "Quy cách": "quy_cach",
            "客户技术要求": "khach_hang_yeu_cau_ky_thuat",
            "Yêu cầu kỹ thuật KH": "khach_hang_yeu_cau_ky_thuat",
            "Số lượng": "so_luong",
            "Mã PO": "ma_po",
            "Mã bản vẽ": "ma_ban_ve",
            "Loại sản phẩm": "loai_san_pham",
            "Tình trạng hoàn thành dự án": "tinh_trang_hoan_thanh"
        }
        
        db_sort_column = sort_column_map.get(sort_by, "tracking_id")
        order_dir = "DESC" if sort_order == "desc" else "ASC"
        
        # Build main query
        query = f"""
            SELECT * FROM projects 
            WHERE {where_clause}
            ORDER BY {db_sort_column} {order_dir}
            LIMIT ? OFFSET ?
        """
        
        cursor.execute(query, params + [limit, offset])
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to frontend format
        data = _convert_rows_to_format(rows)
        
        total_pages = (total + limit - 1) // limit
        
        return {
            "data": data,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
    
    except Exception as e:
        print(f"[DB] Error in filter_data_sql: {e}")
        import traceback
        traceback.print_exc()
        # Fallback to Python filter
        all_data = load_all()
        filtered = filter_data(all_data, column_filters)
        return get_paged_data(filtered, page, limit, sort_by, sort_order)


def ensure_indexes():
    """
    Đảm bảo các indexes cần thiết tồn tại trong database
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Các indexes cần thiết cho tìm kiếm/sắp xếp
        indexes = [
            ("idx_projects_khach_hang", "projects", "khach_hang"),
            ("idx_projects_ten_san_pham", "projects", "ten_san_pham"),
            ("idx_projects_nhan_vien_kinh_doanh", "projects", "nhan_vien_kinh_doanh"),
            ("idx_projects_ma_po", "projects", "ma_po"),
            ("idx_projects_loai_san_pham", "projects", "loai_san_pham"),
            ("idx_projects_tinh_trang_hoan_thanh", "projects", "tinh_trang_hoan_thanh"),
        ]
        
        for index_name, table_name, column_name in indexes:
            try:
                cursor.execute(f"CREATE INDEX IF NOT EXISTS {index_name} ON {table_name}({column_name})")
            except sqlite3.OperationalError as e:
                # Index có thể đã tồn tại
                pass
        
        conn.commit()
        conn.close()
        
        print("[DB] Database indexes ensured")
        return True
    
    except Exception as e:
        print(f"[DB] Error ensuring indexes: {e}")
        return False


def _convert_rows_to_format(rows):
    """
    Convert database rows to frontend format (tối ưu - chỉ tạo keys cần thiết)
    Frontend chỉ sử dụng 20 keys:
    - Tracking ID, Ngày, Khách hàng, Nhân viên KD, Tên sản phẩm
    - Quy cách, Người liên hệ\n(KH), Số lượng, Mã PO, Mã bản vẽ
    - Mã bản vẽ kỹ thuật (sau khi đặt hàng), Mã mẹ, Loại sản phẩm
    - Nhân viên thiết kế, Tình trạng hoàn thành dự án, Tính cấp bách
    - Thời gian mong muốn có bản vẽ, Thời gian hoàn thành kế hoạch
    - is_pending, accepted_by
    """
    data = []
    for row in rows:
        record = dict(row)
        sales_name_value = record.get("sales_name") or record.get("nhan_vien_kinh_doanh", "")
        
        # Tối ưu: Chỉ tạo 20 keys cần thiết cho frontend
        # Bao gồm cả "Nhân viên KD" để frontend hiển thị đúng
        old_format = {
            "Tracking ID": record.get("tracking_id"),
            "Ngày": record.get("Created_Date"),
            "Khách hàng": record.get("khach_hang"),
            "Nhân viên KD": sales_name_value,  # Thêm cho frontend
            "Nhân viên kinh doanh": sales_name_value,  # Giữ lại để tương thích
            "Tên sản phẩm": record.get("ten_san_pham"),
            "Quy cách": record.get("quy_cach"),
            "客户技术要求": record.get("khach_hang_yeu_cau_ky_thuat"),
            "Yêu cầu kỹ thuật KH": record.get("khach_hang_yeu_cau_ky_thuat"),
            "Người liên hệ\n(KH)": record.get("nguoi_lien_he_kh"),
            "Người liên hệ (KH)": record.get("nguoi_lien_he_kh"),
            "Số lượng": record.get("so_luong"),
            "Mã PO": record.get("ma_po"),
            "Mã bản vẽ": record.get("ma_ban_ve"),
            "Mã bản vẽ kỹ thuật (sau khi đặt hàng)": record.get("ma_ban_ve_ky_thuat"),
            "Mã mẹ": record.get("ma_me"),
            "Loại sản phẩm": record.get("loai_san_pham"),
            "Nhân viên thiết kế": record.get("nhan_vien_thiet_ke"),
            "Tình trạng hoàn thành dự án": record.get("tinh_trang_hoan_thanh"),
            "Tính cấp bách": record.get("urgency_level"),
            "Thời gian mong muốn có bản vẽ": record.get("thoi_gian_mong_muon_ban_ve"),
            "Thời gian hoàn thành kế hoạch": record.get("thoi_gian_hoan_thanh_ke_hoach"),
            "is_pending": record.get("is_pending"),
            "Trạng thái chờ": record.get("is_pending"),
            "accepted_by": record.get("accepted_by"),
            "Người nhận": record.get("accepted_by"),
            "accepted_at": record.get("accepted_at"),
            "Thời gian nhận": record.get("accepted_at"),
            "version": record.get("version") or 1,
            "updated_by": record.get("updated_by"),
            "updated_at": record.get("updated_at")
        }
        data.append(old_format)
    
    return data


def get_paged_data(data, page=1, limit=50, sort_by="Tracking ID", sort_order="asc"):
    """
    Lấy dữ liệu phân trang với sắp xếp
    Args:
        data: list of records
        page: int (trang hiện tại, bắt đầu từ 1)
        limit: int (số bản ghi mỗi trang)
        sort_by: string (tên cột sắp xếp)
        sort_order: string ('asc' hoặc 'desc')
    Returns:
        dict: {data, total, page, limit, total_pages}
    """
    # Sắp xếp dữ liệu
    reverse = (sort_order == "desc")
    
    if sort_by == "Tracking ID":
        sorted_data = sorted(data, key=lambda x: int(x.get(sort_by, 0)), reverse=reverse)
    else:
        sorted_data = sorted(data, key=lambda x: str(x.get(sort_by, "")).lower(), reverse=reverse)
    
    # Phân trang
    start_idx = (page - 1) * limit
    end_idx = min(start_idx + limit, len(sorted_data))
    paged_data = sorted_data[start_idx:end_idx]
    
    return {
        "data": paged_data,
        "total": len(sorted_data),
        "page": page,
        "limit": limit,
        "total_pages": (len(sorted_data) + limit - 1) // limit
    }


def get_paged_data_sql(page=1, limit=50, sort_by="Tracking ID", sort_order="asc"):
    """
    Lấy dữ liệu phân trang TRỰC TIẾP từ SQL (hiệu suất cao hơn)
    Thay vì load all data rồi phân trang ở Python, thực hiện LIMIT/OFFSET ở SQL
    
    Args:
        page: int (trang hiện tại, bắt đầu từ 1)
        limit: int (số bản ghi mỗi trang)
        sort_by: string (tên cột sắp xếp)
        sort_order: string ('asc' hoặc 'desc')
    Returns:
        dict: {data, total, page, limit, total_pages}
    """
    try:
        if not os.path.exists(DB_PATH):
            return {"data": [], "total": 0, "page": page, "limit": limit, "total_pages": 0}
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Kiểm tra schema
        cursor.execute("PRAGMA table_info(projects)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "Created_Date" not in columns:
            # Schema cũ - fallback về phân trang Python
            conn.close()
            data = load_all()
            return get_paged_data(data, page, limit, sort_by, sort_order)
        
        # Map sort_by từ format client sang database column
        sort_column_map = {
            "Tracking ID": "tracking_id",
            "Ngày": "Created_Date",
            "Khách hàng": "khach_hang",
            "Nhân viên kinh doanh": "nhan_vien_kinh_doanh",
            "Tên sản phẩm": "ten_san_pham",
            "Quy cách": "quy_cach",
            "客户技术要求": "khach_hang_yeu_cau_ky_thuat",
            "Yêu cầu kỹ thuật KH": "khach_hang_yeu_cau_ky_thuat",
            "Số lượng": "so_luong",
            "Mã PO": "ma_po",
            "Mã bản vẽ": "ma_ban_ve",
            "Loại sản phẩm": "loai_san_pham",
            "Tình trạng hoàn thành dự án": "tinh_trang_hoan_thanh"
        }
        
        db_sort_column = sort_column_map.get(sort_by, "tracking_id")
        
        # Validate limit to prevent excessive memory usage
        limit = min(limit, MAX_PROJECT_PAGE_LIMIT)
        
        # Calculate offset
        offset = (page - 1) * limit
        
        # Get total count first (efficient with SQL COUNT)
        cursor.execute("SELECT COUNT(*) as total FROM projects")
        total = cursor.fetchone()["total"]
        
        if total == 0:
            conn.close()
            return {"data": [], "total": 0, "page": page, "limit": limit, "total_pages": 0}
        
        # Build query with SQL LIMIT/OFFSET and ORDER BY
        order_dir = "DESC" if sort_order == "desc" else "ASC"
        
        # Use parameterized query to prevent SQL injection
        query = f"""
            SELECT * FROM projects 
            ORDER BY {db_sort_column} {order_dir}
            LIMIT ? OFFSET ?
        """
        
        cursor.execute(query, (limit, offset))
        rows = cursor.fetchall()
        conn.close()
        
        # Convert to format compatible with frontend (reuse optimized function)
        data = _convert_rows_to_format(rows)
        
        total_pages = (total + limit - 1) // limit
        
        return {
            "data": data,
            "total": total,
            "page": page,
            "limit": limit,
            "total_pages": total_pages
        }
    
    except Exception as e:
        print(f"[DB] Error in get_paged_data_sql: {e}")
        # Fallback to Python-based pagination
        data = load_all()
        return get_paged_data(data, page, limit, sort_by, sort_order)


def migrate_from_json(json_path='DB.json', backup=True):
    """
    Migration dữ liệu từ JSON file sang SQLite database
    Args:
        json_path: đường dẫn file JSON cũ
        backup: bool, có backup file JSON cũ không
    Returns:
        bool: True nếu thành công
    """
    try:
        print(f"[DB] Starting migration from {json_path} to {DB_PATH}")
        
        # Kiểm tra file JSON tồn tại
        if not os.path.exists(json_path):
            print(f"[DB] JSON file {json_path} not found, creating new database")
            init_db()
            return True
        
        # Load dữ liệu từ JSON
        for encoding in ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin-1']:
            try:
                with open(json_path, 'r', encoding=encoding) as f:
                    raw_data = f.read()
                    clean_data = ''.join(c for c in raw_data if c.isprintable() or c in ['\n', '\r'])
                    data = json.loads(clean_data)
                    print(f"[DB] Loaded {len(data)} records from JSON with encoding {encoding}")
                    break
            except Exception as e:
                print(f"[DB] Try encoding {encoding} failed: {e}")
                continue
        else:
            print(f"[DB] Failed to load JSON file")
            return False
        
        # Backup file JSON cũ nếu cần
        if backup:
            backup_path = json_path + '.backup'
            try:
                os.rename(json_path, backup_path)
                print(f"[DB] Backed up JSON to {backup_path}")
            except Exception as e:
                print(f"[DB] Warning: Could not backup JSON file: {e}")
        
        # Khởi tạo database mới
        init_db()
        
        # Import dữ liệu
        conn = get_connection()
        cursor = conn.cursor()
        
        for record in data:
            tracking_id = record.get('Tracking ID')
            data_json = json.dumps(record, ensure_ascii=False)
            cursor.execute(
                'INSERT INTO projects (tracking_id, data) VALUES (?, ?)',
                (tracking_id, data_json)
            )
        
        conn.commit()
        conn.close()
        
        print(f"[DB] Migration completed. {len(data)} records migrated.")
        return True
    
    except Exception as e:
        print(f"[DB] Migration error: {e}")
        import traceback
        traceback.print_exc()
        return False


# Các hàm bổ sung cho SQLite-specific queries

def get_record_by_tracking_id(tracking_id):
    """
    Lấy một bản ghi theo tracking_id
    Args:
        tracking_id: int
    Returns:
        dict hoặc None
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Kiểm tra schema
        cursor.execute("PRAGMA table_info(projects)")
        columns = [col[1] for col in cursor.fetchall()]
        
        if "Created_Date" in columns:
            # Schema mới - đọc trực tiếp từ columns
            cursor.execute('SELECT * FROM projects WHERE tracking_id = ?', (tracking_id,))
            row = cursor.fetchone()
            conn.close()
            
            if row:
                record = dict(row)
                # Lấy giá trị sales_name hoặc fallback về nhan_vien_kinh_doanh
                sales_name_value = record.get("sales_name") or record.get("nhan_vien_kinh_doanh", "")
                
                # Chuyển về format cũ để tương thích
                return {
                    "Tracking ID": record.get("tracking_id"),
                    "Ngày": record.get("Created_Date"),
                    "Ngày khởi tạo": record.get("Created_Date"),
                    "Khách hàng": record.get("khach_hang"),
                    "Nhân viên kinh doanh": sales_name_value,
                    "Tên sản phẩm": record.get("ten_san_pham"),
                    "Quy cách": record.get("quy_cach"),
                    "客户技术要求": record.get("khach_hang_yeu_cau_ky_thuat"),
                    "Yêu cầu kỹ thuật KH": record.get("khach_hang_yeu_cau_ky_thuat"),
                    "Người liên hệ\n(KH)": record.get("nguoi_lien_he_kh"),
                    "Người liên hệ (KH)": record.get("nguoi_lien_he_kh"),
                    "Số lượng": record.get("so_luong"),
                    "Mã PO": record.get("ma_po"),
                    "Mã bản vẽ": record.get("ma_ban_ve"),
                    "Mã bản vẽ phương án (mã trước khi đặt hàng)": record.get("ma_ban_ve"),
                    "Mã bản vẽ kỹ thuật (sau khi đặt hàng)": record.get("ma_ban_ve_ky_thuat"),
                    "Mã bản vẽ kỹ thuật (mã sau khi đặt hàng)": record.get("ma_ban_ve_ky_thuat"),
                    "Mã mẹ ": record.get("ma_me"),
                    "Mã thành phẩm (Mã mẹ)": record.get("ma_me"),
                    "Loại sản phẩm": record.get("loai_san_pham"),
                    "Hạng mục": record.get("loai_san_pham"),
                    "Nhân viên thiết kế": record.get("nhan_vien_thiet_ke"),
                    "Kỹ sư thiết kế": record.get("nhan_vien_thiet_ke"),
                    "Tình trạng hoàn thành dự án": record.get("tinh_trang_hoan_thanh"),
                    "Tính cấp bách": record.get("urgency_level"),
                    "Thời gian mong muốn có bản vẽ": record.get("thoi_gian_mong_muon_ban_ve"),
                    "Thời gian hoàn thành kế hoạch": record.get("thoi_gian_hoan_thanh_ke_hoach"),
                    "user_id": record.get("user_id"),
                    "User ID": record.get("user_id"),
                    "is_pending": record.get("is_pending"),
                    "Trạng thái chờ": record.get("is_pending"),
                    "accepted_by": record.get("accepted_by"),
                    "Người nhận": record.get("accepted_by"),
                    "accepted_at": record.get("accepted_at"),
                    "Thời gian nhận": record.get("accepted_at"),
                    "urgency_level": record.get("urgency_level"),
                    "Mức độ khẩn cấp": record.get("urgency_level"),
                    "desired_solution_time": record.get("desired_solution_time"),
                    "version": record.get("version") or 1,
                    "updated_by": record.get("updated_by"),
                    "updated_at": record.get("updated_at")
                }
            return None
        else:
            # Schema cũ - đọc từ JSON
            cursor.execute('SELECT data FROM projects WHERE tracking_id = ?', (tracking_id,))
            result = cursor.fetchone()
            conn.close()
            
            if result:
                return json.loads(result['data'])
            return None
    
    except Exception as e:
        print(f"[DB] Error getting record: {e}")
        return None


def get_record_by_id(tracking_id):
    """
    Alias for get_record_by_tracking_id - Lấy một bản ghi theo tracking_id
    Args:
        tracking_id: int
    Returns:
        dict hoặc None
    """
    return get_record_by_tracking_id(tracking_id)


def count_records():
    """
    Đếm tổng số bản ghi
    Returns:
        int
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) as count FROM projects')
        result = cursor.fetchone()
        
        conn.close()
        
        return result['count'] if result else 0
    
    except Exception as e:
        print(f"[DB] Error counting records: {e}")
        return 0


def vacuum():
    """
    Tối ưu hóa database (shrink file size)
    Returns:
        bool
    """
    try:
        conn = get_connection()
        conn.execute('VACUUM')
        conn.close()
        print(f"[DB] Database vacuumed")
        return True
    except Exception as e:
        print(f"[DB] Vacuum error: {e}")
        return False


if __name__ == "__main__":
    # Test khi chạy trực tiếp
    print("Testing DB Helper V2...")
    
    # Migrate to V2
    migrate_to_v2()
    
    # Initialize database
    init_db()
    init_db_v2()
    
    # Load data
    data = load_all()
    print(f"Loaded {len(data)} records")
    
    # Count records
    count = count_records()
    print(f"Total records: {count}")


# ==================== USER MANAGEMENT FUNCTIONS ====================

def add_user(user_data: Dict[str, Any]) -> Optional[int]:
    """
    Thêm user mới vào database
    Args:
        user_data: dict chứa username, passwords, role, full_name, employee_id, department
    Returns:
        user_id mới hoặc None nếu lỗi
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Lấy thời gian tạo user
        created_at = datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO users (username, passwords, role, full_name, employee_id, department, status, user_created_at)
            VALUES (?, ?, ?, ?, ?, ?, 'active', ?)
        ''', (
            user_data['username'],
            user_data['passwords'],
            user_data.get('role', 'sales'),
            user_data['full_name'],
            user_data.get('employee_id'),
            user_data.get('department', 'Sales'),
            created_at
        ))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"[DB] Added user {user_data['username']} with id={user_id}, created_at={created_at}")
        return user_id
    
    except Exception as e:
        print(f"[DB] Error adding user: {e}")
        return None


def get_user_by_username(username: str) -> Optional[Dict[str, Any]]:
    """
    Lấy thông tin user theo username
    Args:
        username: tên đăng nhập
    Returns:
        dict chứa thông tin user hoặc None
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Tìm user không phân biệt hoa thường bằng COLLATE NOCASE
        cursor.execute('SELECT * FROM users WHERE username = ? COLLATE NOCASE', (username,))
        result = cursor.fetchone()
        
        conn.close()
        
        if result:
            return dict(result)
        return None
    
    except Exception as e:
        print(f"[DB] Error getting user: {e}")
        return None


def get_all_users() -> List[Dict[str, Any]]:
    """
    Lấy danh sách tất cả users (bao gồm permissions)
    Returns:
        list of dict
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM users ORDER BY user_id DESC')
        results = cursor.fetchall()
        
        # Fetch all permissions first to avoid cursor issues
        cursor.execute('SELECT user_id, permission FROM user_permissions')
        all_permissions = cursor.fetchall()
        
        # Build permissions dict
        permissions_dict = {}
        for perm_row in all_permissions:
            uid = perm_row['user_id']
            perm = perm_row['permission']
            if uid not in permissions_dict:
                permissions_dict[uid] = []
            permissions_dict[uid].append(perm)
        
        users = []
        for row in results:
            user_dict = dict(row)
            user_id = user_dict.get('user_id')
            
            # Get permissions from dict
            permissions = permissions_dict.get(user_id, [])
            
            # Nếu không có permissions trong DB, lấy mặc định theo role
            if not permissions and user_dict.get('role'):
                permissions = get_default_permissions(user_dict['role'])
            
            user_dict['permissions'] = permissions
            users.append(user_dict)
        
        conn.close()
        
        return users
    
    except Exception as e:
        print(f"[DB] Error getting all users: {e}")
        return []


def update_user(user_id: int, user_data: Dict[str, Any]) -> bool:
    """
    Cập nhật thông tin user
    Args:
        user_id: ID của user
        user_data: dict chứa thông tin cần cập nhật
    Returns:
        True nếu thành công
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Build update query dynamically
        allowed_fields = ['passwords', 'role', 'full_name', 'employee_id', 'department', 'status', 'email', 'phone']
        updates = []
        values = []
        
        for field in allowed_fields:
            if field in user_data:
                updates.append(f"{field} = ?")
                values.append(user_data[field])
        
        if not updates:
            return False
        
        values.append(user_id)
        
        query = f"UPDATE users SET {', '.join(updates)} WHERE user_id = ?"
        cursor.execute(query, values)
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        
        print(f"[DB] Updated user {user_id}, success={success}")
        return success
    
    except Exception as e:
        print(f"[DB] Error updating user: {e}")
        return False


def delete_user(user_id: int) -> bool:
    """
    Xóa user
    Args:
        user_id: ID của user
    Returns:
        True nếu thành công
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM users WHERE user_id = ?', (user_id,))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        
        print(f"[DB] Deleted user {user_id}, success={success}")
        return success
    
    except Exception as e:
        print(f"[DB] Error deleting user: {e}")
        return False


def authenticate_user(username: str, password: str) -> Optional[Dict[str, Any]]:
    """
    Xác thực user đăng nhập
    Args:
        username: tên đăng nhập
        password: mật khẩu
    Returns:
        dict chứa thông tin user (không có password) hoặc None
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT user_id, username, role, full_name, employee_id, department, status, last_login
            FROM users 
            WHERE username = ? AND passwords = ? AND status = 'active'
        ''', (username.lower(), password))
        
        result = cursor.fetchone()
        
        # Update last_login
        if result:
            cursor.execute(
                'UPDATE users SET last_login = ? WHERE user_id = ?',
                (datetime.now().isoformat(), result['user_id'])
            )
            conn.commit()
        
        conn.close()
        
        if result:
            return dict(result)
        return None
    
    except Exception as e:
        print(f"[DB] Error authenticating user: {e}")
        return None


# ==================== PERMISSION MANAGEMENT FUNCTIONS ====================

# Default permissions cho mỗi role
DEFAULT_PERMISSIONS = {
    'sales': ['create_code', 'view_history', 'export', 'create_sales_record'],
    'engineer': ['create_code', 'view_history', 'job_accept'],
    'admin': ['create_code', 'view_history', 'delete_history', 'export', 'admin', 'job_accept'],
    'IT': ['create_code', 'view_history', 'delete_history', 'export', 'admin', 'job_accept'],
    'Pur': ['view_history', 'export']
}

# Tất cả permissions có thể có
ALL_PERMISSIONS = ['create_code', 'view_history', 'delete_history', 'export', 'admin', 'job_accept']


def get_default_permissions(role: str) -> List[str]:
    """
    Lấy danh sách permissions mặc định cho một role
    Args:
        role: tên role ('sales', 'engineer', 'admin', 'IT', 'Pur')
    Returns:
        list of permissions
    """
    return DEFAULT_PERMISSIONS.get(role, ['view_history'])


def add_user_permission(user_id: int, permission: str) -> bool:
    """
    Thêm một permission cho user
    Args:
        user_id: ID của user
        permission: tên permission
    Returns:
        True nếu thành công
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'INSERT OR IGNORE INTO user_permissions (user_id, permission) VALUES (?, ?)',
            (user_id, permission)
        )
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        
        print(f"[DB] Added permission '{permission}' for user {user_id}, success={success}")
        return success
    
    except Exception as e:
        print(f"[DB] Error adding user permission: {e}")
        return False


def remove_user_permission(user_id: int, permission: str) -> bool:
    """
    Xóa một permission của user
    Args:
        user_id: ID của user
        permission: tên permission
    Returns:
        True nếu thành công
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'DELETE FROM user_permissions WHERE user_id = ? AND permission = ?',
            (user_id, permission)
        )
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        
        print(f"[DB] Removed permission '{permission}' for user {user_id}, success={success}")
        return success
    
    except Exception as e:
        print(f"[DB] Error removing user permission: {e}")
        return False


def get_user_permissions(user_id: int) -> List[str]:
    """
    Lấy tất cả permissions của một user
    Args:
        user_id: ID của user
    Returns:
        list of permissions
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT permission FROM user_permissions WHERE user_id = ?',
            (user_id,)
        )
        
        results = cursor.fetchall()
        conn.close()
        
        permissions = [row['permission'] for row in results]
        print(f"[DB] Got {len(permissions)} permissions for user {user_id}")
        return permissions
    
    except Exception as e:
        print(f"[DB] Error getting user permissions: {e}")
        return []


def set_user_permissions(user_id: int, permissions: List[str]) -> bool:
    """
    Đặt tất cả permissions cho user (thay thế permissions cũ)
    Args:
        user_id: ID của user
        permissions: list of permissions
    Returns:
        True nếu thành công
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Xóa tất cả permissions cũ
        cursor.execute('DELETE FROM user_permissions WHERE user_id = ?', (user_id,))
        
        # Thêm permissions mới
        for permission in permissions:
            cursor.execute(
                'INSERT INTO user_permissions (user_id, permission) VALUES (?, ?)',
                (user_id, permission)
            )
        
        conn.commit()
        conn.close()
        
        print(f"[DB] Set {len(permissions)} permissions for user {user_id}")
        return True
    
    except Exception as e:
        print(f"[DB] Error setting user permissions: {e}")
        return False


def delete_user_permissions(user_id: int) -> bool:
    """
    Xóa tất cả permissions của một user
    Args:
        user_id: ID của user
    Returns:
        True nếu thành công
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('DELETE FROM user_permissions WHERE user_id = ?', (user_id,))
        
        conn.commit()
        conn.close()
        
        print(f"[DB] Deleted all permissions for user {user_id}")
        return True
    
    except Exception as e:
        print(f"[DB] Error deleting user permissions: {e}")
        return False


def has_user_permission(user_id: int, permission: str) -> bool:
    """
    Kiểm tra user có một permission cụ thể không
    Args:
        user_id: ID của user
        permission: tên permission
    Returns:
        True nếu có permission
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT 1 FROM user_permissions WHERE user_id = ? AND permission = ?',
            (user_id, permission)
        )
        
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
    
    except Exception as e:
        print(f"[DB] Error checking user permission: {e}")
        return False


def assign_default_permissions(user_id: int, role: str) -> bool:
    """
    Gán permissions mặc định cho user dựa trên role
    Args:
        user_id: ID của user
        role: role của user
    Returns:
        True nếu thành công
    """
    permissions = get_default_permissions(role)
    return set_user_permissions(user_id, permissions)


def get_user_with_permissions(username: str) -> Optional[Dict[str, Any]]:
    """
    Lấy thông tin user bao gồm permissions
    Args:
        username: tên đăng nhập
    Returns:
        dict chứa thông tin user và permissions, hoặc None
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Lấy thông tin user - tìm không phân biệt hoa thường
        cursor.execute('SELECT * FROM users WHERE username = ? COLLATE NOCASE', (username,))
        user = cursor.fetchone()
        
        if not user:
            conn.close()
            return None
        
        user_dict = dict(user)
        user_id = user_dict.get('user_id')
        
        # Lấy permissions
        cursor.execute('SELECT permission FROM user_permissions WHERE user_id = ?', (user_id,))
        permissions = [row['permission'] for row in cursor.fetchall()]
        
        # Nếu không có permissions trong DB, lấy mặc định theo role
        if not permissions and user_dict.get('role'):
            permissions = get_default_permissions(user_dict['role'])
        
        user_dict['permissions'] = permissions
        conn.close()
        
        return user_dict
    
    except Exception as e:
        print(f"[DB] Error getting user with permissions: {e}")
        return None


def ensure_default_users():
    """
    Đảm bảo các users mặc định tồn tại trong database.
    Hàm này được gọi khi server khởi động để tạo các users mặc định nếu chưa tồn tại.
    Users mặc định bao gồm: admin, ENG001-ENG006
    """
    # Danh sách users mặc định
    default_users = [
        {
            'username': 'admin',
            'passwords': '123',
            'role': 'admin',
            'full_name': 'Administrator',
            'employee_id': None,
            'department': 'Administration'
        },
        {
            'username': 'ENG001',
            'passwords': '123',
            'role': 'engineer',
            'full_name': 'Engineer 001',
            'employee_id': 'ENG001',
            'department': 'Engineering'
        },
        {
            'username': 'ENG002',
            'passwords': '123',
            'role': 'engineer',
            'full_name': 'Engineer 002',
            'employee_id': 'ENG002',
            'department': 'Engineering'
        },
        {
            'username': 'ENG003',
            'passwords': '123',
            'role': 'engineer',
            'full_name': 'Engineer 003',
            'employee_id': 'ENG003',
            'department': 'Engineering'
        },
        {
            'username': 'ENG004',
            'passwords': '123',
            'role': 'engineer',
            'full_name': 'Engineer 004',
            'employee_id': 'ENG004',
            'department': 'Engineering'
        },
        {
            'username': 'ENG005',
            'passwords': '123',
            'role': 'engineer',
            'full_name': 'Engineer 005',
            'employee_id': 'ENG005',
            'department': 'Engineering'
        },
        {
            'username': 'ENG006',
            'passwords': '123',
            'role': 'engineer',
            'full_name': 'Engineer 006',
            'employee_id': 'ENG006',
            'department': 'Engineering'
        }
    ]
    
    created_count = 0
    for user_data in default_users:
        # Kiểm tra xem user đã tồn tại chưa
        existing = get_user_by_username(user_data['username'])
        if not existing:
            # Tạo user mới
            user_id = add_user(user_data)
            if user_id:
                # Gán permissions mặc định theo role
                assign_default_permissions(user_id, user_data['role'])
                created_count += 1
                print(f"[DB] Created default user: {user_data['username']} with role: {user_data['role']}")
        else:
            print(f"[DB] Default user already exists: {user_data['username']}")
    
    if created_count > 0:
        print(f"[DB] Created {created_count} default users")
    else:
        print("[DB] All default users already exist")
    
    return created_count


# ==================== CUSTOMER MANAGEMENT FUNCTIONS (DEPRECATED) ====================
# Các hàm dưới đây đã bị loại bỏ khỏi chức năng chính.
# Chúng được giữ lại để tương thích nhưng không còn được sử dụng bởi client.

def add_customer(customer_data: Dict[str, Any]) -> Optional[int]:
    """
    DEPRECATED: Chức năng quản lý khách hàng đã bị loại bỏ.
    Các hàm này được giữ lại để tương thích nhưng không còn được sử dụng.
    
    Args:
        customer_data: dict chứa name, contact_person, phone, email, address
    Returns:
        customer id mới hoặc None nếu lỗi
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR IGNORE INTO customers (name, contact_person, phone, email, address)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            customer_data['name'],
            customer_data.get('contact_person'),
            customer_data.get('phone'),
            customer_data.get('email'),
            customer_data.get('address')
        ))
        
        customer_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        if customer_id and customer_id > 0:
            print(f"[DB] Added customer {customer_data['name']} with id={customer_id}")
            return customer_id
        else:
            # Customer already exists (due to UNIQUE constraint)
            print(f"[DB] Customer {customer_data['name']} already exists")
            return None
    
    except Exception as e:
        print(f"[DB] Error adding customer: {e}")
        return None


def get_all_customers() -> List[Dict[str, Any]]:
    """
    DEPRECATED: Lấy danh sách tất cả khách hàng
    
    Returns:
        list of dict
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT * FROM customers ORDER BY name')
        results = cursor.fetchall()
        
        conn.close()
        
        return [dict(row) for row in results]
    
    except Exception as e:
        print(f"[DB] Error getting customers: {e}")
        return []


def get_customer_names() -> List[str]:
    """
    DEPRECATED: Lấy danh sách tên khách hàng (cho ComboBox)
    
    Returns:
        list of strings
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('SELECT name FROM customers ORDER BY name')
        results = cursor.fetchall()
        
        conn.close()
        
        return [row['name'] for row in results]
    
    except Exception as e:
        print(f"[DB] Error getting customer names: {e}")
        return []


def search_customers(search_text: str) -> List[str]:
    """
    DEPRECATED: Tìm kiếm khách hàng theo tên
    
    Args:
        search_text: từ khóa tìm kiếm
    Returns:
        list of matching customer names
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute(
            'SELECT name FROM customers WHERE name LIKE ? ORDER BY name',
            (f'%{search_text}%',)
        )
        results = cursor.fetchall()
        
        conn.close()
        
        return [row['name'] for row in results]
    
    except Exception as e:
        print(f"[DB] Error searching customers: {e}")
        return []


# ==================== NOTICE/PENDING PROJECT FUNCTIONS ====================

def get_pending_notices(user_id: Union[int, None] = None) -> List[Dict[str, Any]]:
    """
    Lấy danh sách pending notices (is_pending = 'yes')
    Args:
        user_id: nếu specified, chỉ lấy notices của user đó
    Returns:
        list of pending projects
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Kiểm tra schema
        cursor.execute("PRAGMA table_info(projects)")
        columns = [col[1] for col in cursor.fetchall()]
        has_new_schema = "Created_Date" in columns
        
        if user_id:
            cursor.execute('''
                SELECT * FROM projects 
                WHERE is_pending = 'yes' AND user_id = ?
                ORDER BY tracking_id DESC
            ''', (user_id,))
        else:
            cursor.execute('''
                SELECT * FROM projects 
                WHERE is_pending = 'yes'
                ORDER BY tracking_id DESC
            ''')
        
        results = cursor.fetchall()
        conn.close()
        
        notices = []
        for row in results:
            record = dict(row)
            
            if has_new_schema:
                # Schema mới - convert to old format
                # Lấy giá trị sales_name hoặc fallback về nhan_vien_kinh_doanh
                sales_name_value = record.get("sales_name") or record.get("nhan_vien_kinh_doanh", "")
                
                old_format = {
                    "Tracking ID": record.get("tracking_id"),
                    "Ngày": record.get("Created_Date"),
                    "Ngày khởi tạo": record.get("Created_Date"),
                    "Khách hàng": record.get("khach_hang"),
                    "Nhân viên kinh doanh": sales_name_value,
                    "Tên sản phẩm": record.get("ten_san_pham"),
                    "Quy cách": record.get("quy_cach"),
                    "客户技术要求": record.get("khach_hang_yeu_cau_ky_thuat"),
                    "Yêu cầu kỹ thuật KH": record.get("khach_hang_yeu_cau_ky_thuat"),
                    "Người liên hệ\n(KH)": record.get("nguoi_lien_he_kh"),
                    "Người liên hệ (KH)": record.get("nguoi_lien_he_kh"),
                    "Số lượng": record.get("so_luong"),
                    "Mã PO": record.get("ma_po"),
                    "Mã bản vẽ": record.get("ma_ban_ve"),
                    "Mã bản vẽ phương án (mã trước khi đặt hàng)": record.get("ma_ban_ve"),
                    "Mã bản vẽ kỹ thuật (sau khi đặt hàng)": record.get("ma_ban_ve_ky_thuat"),
                    "Mã bản vẽ kỹ thuật (mã sau khi đặt hàng)": record.get("ma_ban_ve_ky_thuat"),
                    "Mã mẹ ": record.get("ma_me"),
                    "Mã thành phẩm (Mã mẹ)": record.get("ma_me"),
                    "Loại sản phẩm": record.get("loai_san_pham"),
                    "Hạng mục": record.get("loai_san_pham"),
                    "Nhân viên thiết kế": record.get("nhan_vien_thiet_ke"),
                    "Kỹ sư thiết kế": record.get("nhan_vien_thiet_ke"),
                    "Tình trạng hoàn thành dự án": record.get("tinh_trang_hoan_thanh"),
                    "Tính cấp bách": record.get("tinh_cap_bach"),
                    "Thời gian mong muốn có bản vẽ": record.get("thoi_gian_mong_muon_ban_ve"),
                    "Thời gian hoàn thành kế hoạch": record.get("thoi_gian_hoan_thanh_ke_hoach"),
                    "user_id": record.get("user_id"),
                    "User ID": record.get("user_id"),
                    "is_pending": record.get("is_pending"),
                    "Trạng thái chờ": record.get("is_pending"),
                    "accepted_by": record.get("accepted_by"),
                    "Người nhận": record.get("accepted_by"),
                    "accepted_at": record.get("accepted_at"),
                    "Thời gian nhận": record.get("accepted_at"),
                    "urgency_level": record.get("urgency_level"),
                    "Mức độ khẩn cấp": record.get("urgency_level"),
                    "desired_solution_time": record.get("desired_solution_time")
                }
                notices.append(old_format)
            else:
                # Schema cũ - parse JSON
                # Schema cũ - parse JSON
                if record.get('data'):
                    data_parsed = json.loads(record['data'])
                    notices.append(data_parsed)
                else:
                    notices.append(record)
        
        return notices
    
    except Exception as e:
        print(f"[DB] Error getting pending notices: {e}")
        return []


def get_pending_count(user_id: Union[int, None] = None) -> int:
    """
    Đếm số pending notices
    Args:
        user_id: nếu specified, chỉ đếm notices của user đó
    Returns:
        số lượng pending projects
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        if user_id:
            cursor.execute(
                'SELECT COUNT(*) FROM projects WHERE is_pending = \'yes\' AND user_id = ?',
                (user_id,)
            )
        else:
            cursor.execute(
                'SELECT COUNT(*) FROM projects WHERE is_pending = \'yes\''
            )
        
        count = cursor.fetchone()[0]
        conn.close()
        
        return count
    
    except Exception as e:
        print(f"[DB] Error getting pending count: {e}")
        return 0


def accept_job(tracking_id: int, engineer_name: str) -> bool:
    """
    Engineer nhận job từ pending notice
    Args:
        tracking_id: ID của project
        engineer_name: tên engineer nhận job
    Returns:
        True nếu thành công
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        accepted_at = datetime.now().strftime('%Y-%m-%d %H:%M')
        default_completion_status = '待出图 - Đang vẽ'

        # Update project - chuyển từ 'yes' (pending) sang 'no' (accepted)
        cursor.execute('''
            UPDATE projects 
            SET is_pending = 'no',
                accepted_by = ?,
                accepted_at = ?,
                tinh_trang_hoan_thanh = ?
            WHERE tracking_id = ? AND is_pending = 'yes'
        ''', (engineer_name, accepted_at, default_completion_status, tracking_id))
        
        conn.commit()
        success = cursor.rowcount > 0
        conn.close()
        if success:
            invalidate_cache()
        
        print(f"[DB] Accept job tracking_id={tracking_id} by {engineer_name}, success={success}")
        return success
    
    except Exception as e:
        print(f"[DB] Error accepting job: {e}")
        return False


def add_sales_record(record_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """
    Thêm bản ghi mới từ sales (với đầy đủ thông tin)
    Args:
        record_data: dict chứa tất cả thông tin project
    Returns:
        record với tracking_id mới hoặc None nếu lỗi
    """
    try:
        # LOG: Debug logging cho Created_Date (Ngày khởi tạo)
        # print(f"[DEBUG DB] ========== ADD SALES RECORD ==========")
        # print(f"[DEBUG DB] Input 'Ngày' (từ New_Sales): {record_data.get('Ngày')}")
        # print(f"[DEBUG DB] Input 'user_id': {record_data.get('user_id')}")
        # print(f"[DEBUG DB] Input 'Khách hàng': {record_data.get('Khách hàng')}")
        # print(f"[DEBUG DB] ======================================")
        
        conn = get_connection()
        cursor = conn.cursor()
        
        # Lấy tracking_id mới
        cursor.execute('SELECT MAX(tracking_id) as max_id FROM projects')
        result = cursor.fetchone()
        new_tracking_id = (result['max_id'] or 0) + 1
        
        # Map từ format cũ sang columns
        ngay_value = record_data.get('Ngày')
        values = [
            new_tracking_id,
            ngay_value,  # Created_Date
            record_data.get('Khách hàng'),
            record_data.get('Nhân viên kinh doanh'),
            record_data.get('Tên sản phẩm'),
            record_data.get('Quy cách'),
            record_data.get('客户技术要求') or record_data.get('Yêu cầu kỹ thuật KH'),
            record_data.get('Người liên hệ\n(KH)') or record_data.get('Người liên hệ (KH)'),
            record_data.get('Số lượng'),
            record_data.get('Mã PO'),
            record_data.get('Mã bản vẽ'),
            record_data.get('Mã bản vẽ kỹ thuật (sau khi đặt hàng)'),
            record_data.get('Mã mẹ ') or record_data.get('Mã mẹ') or record_data.get('Mã thành phẩm (Mã mẹ)', ''),
            record_data.get('Loại sản phẩm'),
            record_data.get('Nhân viên thiết kế'),
            record_data.get('Tình trạng hoàn thành dự án'),
            record_data.get('Tính cấp bách'),
            record_data.get('Thời gian mong muốn có bản vẽ'),
            record_data.get('Thời gian hoàn thành kế hoạch'),
            record_data.get('sales_name'),
            record_data.get('user_id'),
            'yes',  # is_pending = 'yes' for new sales records
            None,  # accepted_by
            None,  # accepted_at
            record_data.get('urgency_level'),
            record_data.get('desired_solution_time')
        ]
        
        placeholders = ', '.join(['?' for _ in PROJECT_COLUMNS])
        insert_cols = ', '.join(PROJECT_COLUMNS)
        
        cursor.execute(
            f"INSERT INTO projects ({insert_cols}) VALUES ({placeholders})",
            values
        )
        
        # LOG: Verify sau khi insert
        # print(f"[DEBUG DB] Inserted record with tracking_id={new_tracking_id}")
        # print(f"[DEBUG DB] Created_Date value in DB: {ngay_value}")
        
        record_data['Tracking ID'] = new_tracking_id
        
        conn.commit()
        conn.close()
        
        print(f"[DB] Added sales record with tracking_id={new_tracking_id}")
        return record_data
    
    except Exception as e:
        print(f"[DB] Error adding sales record: {e}")
        return None


def get_projects_by_user(user_id: int) -> List[Dict[str, Any]]:
    """
    Lấy tất cả projects của một user
    Args:
        user_id: ID của user
    Returns:
        list of projects
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM projects 
            WHERE user_id = ?
            ORDER BY tracking_id DESC
        ''', (user_id,))
        
        results = cursor.fetchall()
        conn.close()
        
        projects = []
        for row in results:
            record = dict(row)
            # Lấy giá trị sales_name hoặc fallback về nhan_vien_kinh_doanh
            sales_name_value = record.get("sales_name") or record.get("nhan_vien_kinh_doanh", "")
            
            # Chuyển về format cũ
            old_format = {
                "Tracking ID": record.get("tracking_id"),
                "Ngày": record.get("Created_Date"),
                "Ngày khởi tạo": record.get("Created_Date"),
                "Khách hàng": record.get("khach_hang"),
                "Nhân viên kinh doanh": sales_name_value,
                "Tên sản phẩm": record.get("ten_san_pham"),
                "Quy cách": record.get("quy_cach"),
                "客户技术要求": record.get("khach_hang_yeu_cau_ky_thuat"),
                "Yêu cầu kỹ thuật KH": record.get("khach_hang_yeu_cau_ky_thuat"),
                "Người liên hệ\n(KH)": record.get("nguoi_lien_he_kh"),
                "Người liên hệ (KH)": record.get("nguoi_lien_he_kh"),
                "Số lượng": record.get("so_luong"),
                "Mã PO": record.get("ma_po"),
                "Mã bản vẽ": record.get("ma_ban_ve"),
                "Mã bản vẽ phương án (mã trước khi đặt hàng)": record.get("ma_ban_ve"),
                "Mã bản vẽ kỹ thuật (sau khi đặt hàng)": record.get("ma_ban_ve_ky_thuat"),
                "Mã bản vẽ kỹ thuật (mã sau khi đặt hàng)": record.get("ma_ban_ve_ky_thuat"),
                "Mã mẹ ": record.get("ma_me"),
                "Mã thành phẩm (Mã mẹ)": record.get("ma_me"),
                "Loại sản phẩm": record.get("loai_san_pham"),
                "Hạng mục": record.get("loai_san_pham"),
                "Nhân viên thiết kế": record.get("nhan_vien_thiet_ke"),
                "Kỹ sư thiết kế": record.get("nhan_vien_thiet_ke"),
                "Tình trạng hoàn thành dự án": record.get("tinh_trang_hoan_thanh"),
                "Tính cấp bách": record.get("tinh_cap_bach"),
                "Thời gian mong muốn có bản vẽ": record.get("thoi_gian_mong_muon_ban_ve"),
                "Thời gian hoàn thành kế hoạch": record.get("thoi_gian_hoan_thanh_ke_hoach"),
                "user_id": record.get("user_id"),
                "User ID": record.get("user_id"),
                "is_pending": record.get("is_pending"),
                "Trạng thái chờ": record.get("is_pending"),
                "accepted_by": record.get("accepted_by"),
                "Người nhận": record.get("accepted_by"),
                "accepted_at": record.get("accepted_at"),
                "Thời gian nhận": record.get("accepted_at"),
                "urgency_level": record.get("urgency_level"),
                "Mức độ khẩn cấp": record.get("urgency_level"),
                "desired_solution_time": record.get("desired_solution_time")
            }
            projects.append(old_format)
        
        return projects
    
    except Exception as e:
        print(f"[DB] Error getting projects by sales: {e}")
        return []


def get_accepted_projects_by_engineer(engineer_name: str) -> List[Dict[str, Any]]:
    """
    Lấy các projects đã được engineer nhận
    Args:
        engineer_name: tên engineer
    Returns:
        list of accepted projects
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM projects 
            WHERE accepted_by = ?
            ORDER BY accepted_at DESC
        ''', (engineer_name,))
        
        results = cursor.fetchall()
        conn.close()
        
        projects = []
        for row in results:
            record = dict(row)
            # Lấy giá trị sales_name hoặc fallback về nhan_vien_kinh_doanh
            sales_name_value = record.get("sales_name") or record.get("nhan_vien_kinh_doanh", "")
            
            # Chuyển về format cũ
            old_format = {
                "Tracking ID": record.get("tracking_id"),
                "Ngày": record.get("Created_Date"),
                "Ngày khởi tạo": record.get("Created_Date"),
                "Khách hàng": record.get("khach_hang"),
                "Nhân viên kinh doanh": sales_name_value,
                "Tên sản phẩm": record.get("ten_san_pham"),
                "Quy cách": record.get("quy_cach"),
                "客户技术要求": record.get("khach_hang_yeu_cau_ky_thuat"),
                "Yêu cầu kỹ thuật KH": record.get("khach_hang_yeu_cau_ky_thuat"),
                "Người liên hệ\n(KH)": record.get("nguoi_lien_he_kh"),
                "Người liên hệ (KH)": record.get("nguoi_lien_he_kh"),
                "Số lượng": record.get("so_luong"),
                "Mã PO": record.get("ma_po"),
                "Mã bản vẽ": record.get("ma_ban_ve"),
                "Mã bản vẽ phương án (mã trước khi đặt hàng)": record.get("ma_ban_ve"),
                "Mã bản vẽ kỹ thuật (sau khi đặt hàng)": record.get("ma_ban_ve_ky_thuat"),
                "Mã bản vẽ kỹ thuật (mã sau khi đặt hàng)": record.get("ma_ban_ve_ky_thuat"),
                "Mã mẹ ": record.get("ma_me"),
                "Mã thành phẩm (Mã mẹ)": record.get("ma_me"),
                "Loại sản phẩm": record.get("loai_san_pham"),
                "Hạng mục": record.get("loai_san_pham"),
                "Nhân viên thiết kế": record.get("nhan_vien_thiet_ke"),
                "Kỹ sư thiết kế": record.get("nhan_vien_thiet_ke"),
                "Tình trạng hoàn thành dự án": record.get("tinh_trang_hoan_thanh"),
                "Tính cấp bách": record.get("tinh_cap_bach"),
                "Thời gian mong muốn có bản vẽ": record.get("thoi_gian_mong_muon_ban_ve"),
                "Thời gian hoàn thành kế hoạch": record.get("thoi_gian_hoan_thanh_ke_hoach"),
                "user_id": record.get("user_id"),
                "User ID": record.get("user_id"),
                "is_pending": record.get("is_pending"),
                "Trạng thái chờ": record.get("is_pending"),
                "accepted_by": record.get("accepted_by"),
                "Người nhận": record.get("accepted_by"),
                "accepted_at": record.get("accepted_at"),
                "Thời gian nhận": record.get("accepted_at"),
                "urgency_level": record.get("urgency_level"),
                "Mức độ khẩn cấp": record.get("urgency_level"),
                "desired_solution_time": record.get("desired_solution_time")
            }
            projects.append(old_format)
        
        return projects
    
    except Exception as e:
        print(f"[DB] Error getting accepted projects: {e}")
        return []


def get_all_notices_for_engineer(engineer_name: str) -> List[Dict[str, Any]]:
    """
    Lấy tất cả notices cho engineer (bao gồm cả pending và accepted)
    Args:
        engineer_name: tên engineer
    Returns:
        list of all notices (pending + accepted)
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # Kiểm tra schema
        cursor.execute("PRAGMA table_info(projects)")
        columns = [col[1] for col in cursor.fetchall()]
        has_new_schema = "Created_Date" in columns
        
        # Lấy cả job đang chờ VÀ job đã được engineer này nhận
        cursor.execute('''
            SELECT * FROM projects 
            WHERE is_pending = 'yes' OR accepted_by = ?
            ORDER BY tracking_id DESC
        ''', (engineer_name,))
        
        results = cursor.fetchall()
        conn.close()
        
        notices = []
        for row in results:
            record = dict(row)
            
            if has_new_schema:
                # Schema mới - convert to old format
                sales_name_value = record.get("sales_name") or record.get("nhan_vien_kinh_doanh", "")
                
                old_format = {
                    "Tracking ID": record.get("tracking_id"),
                    "Ngày": record.get("Created_Date"),
                    "Ngày khởi tạo": record.get("Created_Date"),
                    "Khách hàng": record.get("khach_hang"),
                    "Nhân viên kinh doanh": sales_name_value,
                    "Tên sản phẩm": record.get("ten_san_pham"),
                    "Quy cách": record.get("quy_cach"),
                    "客户技术要求": record.get("khach_hang_yeu_cau_ky_thuat"),
                    "Yêu cầu kỹ thuật KH": record.get("khach_hang_yeu_cau_ky_thuat"),
                    "Người liên hệ\n(KH)": record.get("nguoi_lien_he_kh"),
                    "Người liên hệ (KH)": record.get("nguoi_lien_he_kh"),
                    "Số lượng": record.get("so_luong"),
                    "Mã PO": record.get("ma_po"),
                    "Mã bản vẽ": record.get("ma_ban_ve"),
                    "Mã bản vẽ phương án (mã trước khi đặt hàng)": record.get("ma_ban_ve"),
                    "Mã bản vẽ kỹ thuật (sau khi đặt hàng)": record.get("ma_ban_ve_ky_thuat"),
                    "Mã bản vẽ kỹ thuật (mã sau khi đặt hàng)": record.get("ma_ban_ve_ky_thuat"),
                    "Mã mẹ ": record.get("ma_me"),
                    "Mã thành phẩm (Mã mẹ)": record.get("ma_me"),
                    "Loại sản phẩm": record.get("loai_san_pham"),
                    "Hạng mục": record.get("loai_san_pham"),
                    "Nhân viên thiết kế": record.get("nhan_vien_thiet_ke"),
                    "Kỹ sư thiết kế": record.get("nhan_vien_thiet_ke"),
                    "Tình trạng hoàn thành dự án": record.get("tinh_trang_hoan_thanh"),
                    "Tính cấp bách": record.get("tinh_cap_bach"),
                    "Thời gian mong muốn có bản vẽ": record.get("thoi_gian_mong_muon_ban_ve"),
                    "Thời gian hoàn thành kế hoạch": record.get("thoi_gian_hoan_thanh_ke_hoach"),
                    "user_id": record.get("user_id"),
                    "User ID": record.get("user_id"),
                    "is_pending": record.get("is_pending"),
                    "Trạng thái chờ": record.get("is_pending"),
                    "accepted_by": record.get("accepted_by"),
                    "Người nhận": record.get("accepted_by"),
                    "accepted_at": record.get("accepted_at"),
                    "Thời gian nhận": record.get("accepted_at"),
                    "urgency_level": record.get("urgency_level"),
                    "Mức độ khẩn cấp": record.get("urgency_level"),
                    "desired_solution_time": record.get("desired_solution_time")
                }
                notices.append(old_format)
            else:
                # Schema cũ - parse JSON
                if record.get('data'):
                    data_parsed = json.loads(record['data'])
                    notices.append(data_parsed)
                else:
                    notices.append(record)
        
        return notices
    
    except Exception as e:
        print(f"[DB] Error getting all notices for engineer: {e}")
        return []

