# -*- coding: utf-8 -*-
"""
Unified Server - Tích hợp Web Server + Tool Open + Socket API trên port 8001
- Static files: Web UI (từ web/)
- /api/*: Tool Open API
- /api/socket: Socket API (thay thế TCP socket)
"""
import sys
import os
import json
import importlib.util
import threading
import requests
import socket
import sqlite3

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
_print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    """Thread-safe print"""
    try:
        with _print_lock:
            print(*args, **kwargs)
    except (ValueError, OSError):
        pass

# Flask Session Configuration
app.secret_key = 'propack-vp-secret-key-2024'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'

# ========================================================================
# Flask App Setup
# ========================================================================
from flask import Flask, request, jsonify, send_from_directory, make_response, session
from flask_cors import CORS
import tempfile

app = Flask(__name__, 
            template_folder='web/templates',
            static_folder='web/static')
# CORS configuration - cho phép request từ localhost, duckdns và WAN
# Also allow HTTPS origins
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "http://localhost:8001",
            "http://localhost:8002",
            "http://localhost:12345",
            "http://127.0.0.1:8001",
            "http://127.0.0.1:8002",
            "http://127.0.0.1:12345",
            "http://propackvp.duckdns.org:8001",
            "http://propackvp.duckdns.org",
            "http://propackvp.duckdns.org:12345",
            "https://propackvp.duckdns.org:8001",
            "https://propackvp.duckdns.org",
            "https://propackvp.duckdns.org:12345",
            "http://vp.szsunqit.cn:8001",
            "http://vp.szsunqit.cn",
            "http://vp.szsunqit.cn:12345",
            "https://vp.szsunqit.cn:8001",
            "https://vp.szsunqit.cn",
            "https://vp.szsunqit.cn:12345",
            "http://vp.sunqit.cn:8001",
            "http://vp.sunqit.cn",
            "http://vp.sunqit.cn:12345",
            "https://vp.sunqit.cn:8001",
            "https://vp.sunqit.cn",
            "https://vp.sunqit.cn:12345",
            "*",  # Allow all origins for API requests
        ],
        "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "*"],
        "supports_credentials": False
    }
})

# ========================================================================
# Import server modules
# ========================================================================
# Import DB helper
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from src.db_helper import (
    init_db, init_db_v2, migrate_to_v2,
    load_all, save_all, add_record, update_record, delete_records,
    search_data as db_search_data, filter_data as db_filter_data, get_paged_data, get_paged_data_sql, reindex_tracking_id,
    get_record_by_id,
    add_user, get_user_by_username, get_all_users, update_user, delete_user, 
    authenticate_user, get_user_with_permissions, ensure_default_users,
    get_user_permissions, set_user_permissions, add_user_permission, remove_user_permission,
    delete_user_permissions, assign_default_permissions, get_default_permissions, has_user_permission,
    get_pending_notices, get_pending_count, accept_job, add_sales_record, 
    get_projects_by_user, get_accepted_projects_by_engineer, get_all_notices_for_engineer
)

# Import Tool Open core
tool_open_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Tool open")
sys.path.insert(0, tool_open_dir)
material_core = None
TOOL_OPEN_AVAILABLE = False
try:
    core_path = os.path.join(tool_open_dir, "Mở mã liệu 打开链接VP.py")
    spec = importlib.util.spec_from_file_location("material_core", core_path)
    if spec and spec.loader:
        material_core = importlib.util.module_from_spec(spec)
        sys.modules["material_core"] = material_core
        spec.loader.exec_module(material_core)
        TOOL_OPEN_AVAILABLE = True
        safe_print("[Unified] Tool Open core loaded successfully")
except Exception as e:
    safe_print(f"[Unified] Tool Open core load failed: {e}")

# ========================================================================
# Global state
# ========================================================================
db_data = []
cached_sorted_history = None
history_version = 0

# Load data on startup
STORAGE_PATH = 'used_codes.json'
deleted_codes = set()
used_codes = {}
history = []

def load_data():
    global used_codes, history, deleted_codes
    try:
        if os.path.exists(STORAGE_PATH):
            for encoding in ['utf-8', 'utf-8-sig', 'gbk', 'gb2312', 'latin-1']:
                try:
                    with open(STORAGE_PATH, 'r', encoding=encoding) as f:
                        raw_data = f.read()
                        clean_data = ''.join(c for c in raw_data if c.isprintable() or c in ['\n', '\r'])
                        data = json.loads(clean_data)
                        if isinstance(data, list):
                            used = {'LSX': set(data)}
                            history = []
                            deleted_codes = set()
                        else:
                            used = {cat: set(codes) for cat, codes in data.get('used', {}).items()}
                            history = data.get('history', [])
                            deleted_codes = set(data.get('deleted_codes', []))
                            for item in history:
                                if 'parent_code' not in item:
                                    item['parent_code'] = ''
                        print(f"Load success with encoding: {encoding}")
                        return used, history
                except Exception as e:
                    continue
        return {}, []
    except Exception as e:
        print(f"Load file error: {e}")
        return [], []

def save_data_data(used_codes_param, history_param):
    global deleted_codes
    try:
        filtered_used = {cat: list(codes) for cat, codes in used_codes_param.items() if codes}
        data = {
            'used': filtered_used,
            'history': history_param,
            'deleted_codes': list(deleted_codes)
        }
        with open(STORAGE_PATH, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Loi khi save file: {e}")

# Load initial data
used_codes, history = load_data()

# Excel configuration for parent code lookup
EXCEL_PATH = r"\\192.168.2.165\越南vp共享文件夹\09-工程图纸 Bản vẽ Kỹ Thuật Công Trình\存货档案库.xlsx"

# Cache for Excel data
CACHED_EXCEL_DATA = None

def get_excel_data():
    """Đọc dữ liệu Excel vào memory (chỉ tải 1 lần)."""
    global CACHED_EXCEL_DATA
    
    if CACHED_EXCEL_DATA is not None:
        return CACHED_EXCEL_DATA
    
    try:
        import pandas as pd
        import os
        
        excel_path = EXCEL_PATH.replace('/', '\\')
        if not excel_path.startswith('\\\\'):
            excel_path = '\\\\' + excel_path.lstrip('\\')
        
        safe_print(f"[Excel] Loading Excel into memory: {excel_path}")
        
        xls = pd.ExcelFile(excel_path)
        data = []
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            if 'cEngineerFigNo' in df.columns and 'cInvCode' in df.columns:
                # Pre-process: convert to string and uppercase for faster lookup
                df['cEngineerFigNo'] = df['cEngineerFigNo'].astype(str).str.upper().str.strip()
                df['cInvCode'] = df['cInvCode'].astype(str).str.strip()
                data.append((sheet_name, df))
        
        safe_print(f"[Excel] Loaded {len(data)} sheets with data")
        CACHED_EXCEL_DATA = data
        return CACHED_EXCEL_DATA
    except Exception as e:
        safe_print(f"[Excel] Error loading Excel: {e}")
        return None

def find_cinvcode_from_excel(engineer_fig_no: str):
    """Tìm cInvCode tương ứng với cEngineerFigNo trong file Excel."""
    excel_data = get_excel_data()
    if not excel_data:
        return None
    
    search_code = str(engineer_fig_no).upper().strip()
    
    # Try exact match first
    for sheet_name, df in excel_data:
        try:
            mask = df['cEngineerFigNo'] == search_code
            if mask.any():
                matches = df.loc[mask, 'cInvCode']
                for m in matches:
                    if m and m != 'nan' and m.strip():
                        return str(int(float(m))) if '.' in m else m
        except Exception as e:
            continue
    
    # Try partial match (startswith)
    for sheet_name, df in excel_data:
        try:
            mask = df['cEngineerFigNo'].str.startswith(search_code)
            if mask.any():
                matches = df.loc[mask, 'cInvCode']
                for m in matches:
                    if m and m != 'nan' and m.strip():
                        return str(int(float(m))) if '.' in m else m
        except Exception as e:
            continue
    
    return None

def find_parent_codes_batch(codes: list):
    """Tìm parent codes cho nhiều mã cùng lúc.
    
    Args:
        codes: List of codes cần tìm parent
        
    Returns:
        Dict mapping {code: parent_code}
    """
    results = {}
    
    # Pre-load Excel if not already loaded
    excel_data = get_excel_data()
    if not excel_data:
        return results
    
    for code in codes:
        parent_code = find_cinvcode_from_excel(code)
        if parent_code:
            results[code] = parent_code
    
    return results

# Initialize database
init_db()
migrate_to_v2()
ensure_default_users()

# ========================================================================
# Session Management
# ========================================================================
import secrets
import time

sessions = {}
sessions_lock = threading.Lock()
SESSION_TIMEOUT = 3600 * 24  # 24 hours

# Rate limiting for login
LOGIN_RATE_LIMIT = 5
LOGIN_RATE_WINDOW = 300
login_attempts = {}
login_attempts_lock = threading.Lock()

def generate_token():
    """Tạo token ngẫu nhiên"""
    return secrets.token_hex(32)

def check_rate_limit(ip):
    """Kiểm tra rate limit cho IP"""
    current_time = time.time()
    with login_attempts_lock:
        if ip in login_attempts:
            login_attempts[ip] = [
                (t, s) for t, s in login_attempts[ip]
                if current_time - t < LOGIN_RATE_WINDOW
            ]
            if len(login_attempts[ip]) >= LOGIN_RATE_LIMIT:
                return False, 0
            return True, LOGIN_RATE_LIMIT - len(login_attempts[ip])
        return True, LOGIN_RATE_LIMIT

def record_login_attempt(ip, success):
    """Ghi nhận attempt đăng nhập"""
    with login_attempts_lock:
        if ip not in login_attempts:
            login_attempts[ip] = []
        login_attempts[ip].append((time.time(), success))

# ========================================================================
# Helper Functions (copied from server.py)
# ========================================================================

CATEGORY_PREFIXES = {
    "WLJ": "PWLJ", "ZZC": "PZZC", "GZT": "PGZT", "WCP": "PWCP",
    "LSX": "PLSX", "ZWJ": "PZWJ", "GZL": "PGZL", "SJT": "PSJT",
    "BSX": "PBSX", "WLL": "PWLL", "GTX": "PGTX", "ZHT": "PZHT", "LHX": "PLHX"
}

def generate_code(used_codes_param, category, employee=None):
    global deleted_codes
    if category not in CATEGORY_PREFIXES:
        return None
    prefix = CATEGORY_PREFIXES[category]
    if category == "SJT":
        if not employee:
            return None
        key = f"SJT_{employee}"
        seri_used = used_codes_param.get(key, set())
        
        deleted_for_employee = [dc for dc in deleted_codes if dc.startswith(f"PSJT{employee}-") and dc.endswith("-00-A0")]
        deleted_for_employee.sort(key=lambda dc: int(dc.split('-')[1]))
        
        for deleted_code in deleted_for_employee:
            try:
                parts = deleted_code.split('-')
                if len(parts) >= 4:
                    seri_part = parts[-3]
                    if len(seri_part) == 4 and seri_part.isdigit():
                        new_code = f"PSJT{employee}-{seri_part}-00-A0"
                        if new_code not in seri_used:
                            if key not in used_codes_param:
                                used_codes_param[key] = set()
                            used_codes_param[key].add(new_code)
                            deleted_codes.remove(deleted_code)
                            return new_code
            except:
                continue
        
        for i in range(1, 10000):
            code = f"PSJT{employee}-{i:04d}-00-A0"
            if code not in seri_used:
                if key not in used_codes_param:
                    used_codes_param[key] = set()
                used_codes_param[key].add(code)
                return code
        return None
    else:
        suffix = "-0000-00-A0"
        category_used = used_codes_param.get(category, set())
        for i in range(1, 1000):
            code = f"{prefix}{i:03d}{suffix}"
            if code not in category_used:
                return code
        return None

# ========================================================================
# Socket API - HTTP endpoints that replace TCP socket
# ========================================================================

@app.route('/api/socket', methods=['POST'])
def socket_api():
    """HTTP endpoint thay thế cho TCP socket"""
    global db_data, cached_sorted_history, history_version, used_codes, history
    
    try:
        req_data = request.get_json()
        if not req_data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        request_type = req_data.get('request', 'unknown')
        safe_print(f"[SocketAPI] Request: {request_type}")
        
        response_data = None
        
        # ==================== DB Operations ====================
        if request_type == "GET_DB_ALL":
            db_data = load_all()
            response_data = db_data
            
        elif request_type == "GET_DB_PROJECT":
            tracking_id = req_data.get('tracking_id')
            project = get_record_by_id(tracking_id)
            response_data = project
            
        elif request_type == "GET_DB_PAGED":
            page = req_data.get('page', 1)
            limit = req_data.get('limit', 50)
            sort_by = req_data.get('sort_by', 'Tracking ID')
            sort_order = req_data.get('sort_order', 'desc')
            result = get_paged_data_sql(page, limit, sort_by, sort_order)
            response_data = result
            
        elif request_type == "ADD_DB_RECORD":
            record = req_data.get('record', {})
            tracking_id = max([r.get("Tracking ID", 0) for r in db_data] + [0]) + 1
            record["Tracking ID"] = tracking_id
            db_data.append(record)
            save_all(db_data)
            response_data = {"success": True, "record": record}
            
        elif request_type == "UPDATE_DB_RECORD":
            tracking_id = req_data.get('tracking_id')
            new_data = req_data.get('data', {})
            success = update_record(tracking_id, new_data)
            response_data = {"success": success}
            
        elif request_type == "DELETE_DB_RECORDS":
            user_role = req_data.get('user_role')
            tracking_ids = req_data.get('tracking_ids', [])
            
            if user_role != 'admin':
                response_data = {"success": False, "error": "Bạn không có quyền xóa"}
            else:
                deleted_count = delete_records(tracking_ids)
                response_data = {"success": True, "deleted_count": deleted_count}
                
        elif request_type == "SEARCH_DB_DATA":
            search_text = req_data.get('search_text', '')
            columns = req_data.get('columns', [])
            results = db_search_data(db_data, search_text, columns)
            response_data = results
            
        elif request_type == "FILTER_DB_DATA":
            column_filters = req_data.get('filters', {})
            results = db_filter_data(db_data, column_filters)
            response_data = results
            
        # ==================== User Operations ====================
        elif request_type == "DB_LOGIN":
            username = req_data.get('username', '').strip()
            password = req_data.get('password', '')
            
            user_info = get_user_with_permissions(username)
            if user_info:
                if user_info.get('status') == 'locked':
                    response_data = {"success": False, "error": "Tài khoản đã bị khóa"}
                elif user_info.get('passwords') != password:
                    response_data = {"success": False, "error": "Invalid credentials"}
                else:
                    user_info_clean = user_info.copy()
                    if 'passwords' in user_info_clean:
                        del user_info_clean['passwords']
                    response_data = {"success": True, "user_info": user_info_clean}
            else:
                response_data = {"success": False, "error": "Invalid credentials"}
                
        elif request_type == "GET_USERS":
            users = get_all_users()
            response_data = users
            
        elif request_type == "ADD_USER":
            user_data = req_data.get('user_data', {})
            user_id = add_user(user_data)
            if user_id:
                assign_default_permissions(user_id, user_data.get('role', 'sales'))
                response_data = {"success": True, "user_id": user_id}
            else:
                response_data = {"success": False, "error": "Username already exists"}
                
        elif request_type == "UPDATE_USER":
            user_id = req_data.get('user_id')
            user_data = req_data.get('user_data', {})
            success = update_user(user_id, user_data)
            if 'permissions' in user_data:
                set_user_permissions(user_id, user_data['permissions'])
            response_data = {"success": success}
            
        elif request_type == "DELETE_USER":
            user_id = req_data.get('user_id')
            success = delete_user(user_id)
            response_data = {"success": success}
            
        # ==================== Notice/Pending Operations ====================
        elif request_type == "GET_PENDING_NOTICES":
            user_id = req_data.get('user_id')
            notices = get_pending_notices(user_id)
            response_data = notices
            
        elif request_type == "GET_PENDING_COUNT":
            user_id = req_data.get('user_id')
            count = get_pending_count(user_id)
            response_data = {"count": count}
            
        elif request_type == "ACCEPT_JOB":
            tracking_id = req_data.get('tracking_id')
            engineer_name = req_data.get('engineer_name')
            success = accept_job(tracking_id, engineer_name)
            response_data = {"success": success}
            
        elif request_type == "ADD_SALES_RECORD":
            user_role = req_data.get('user_role')
            user_permissions = req_data.get('user_permissions', [])
            
            has_permission = False
            if user_role in ['admin', 'IT']:
                has_permission = True
            elif user_role == 'sales' and 'create_sales_record' in user_permissions:
                has_permission = True
            
            if not has_permission:
                response_data = {"success": False, "error": "Bạn không có quyền tạo tracking mới"}
            else:
                record_data = req_data.get('record', {})
                new_record = add_sales_record(record_data)
                if new_record:
                    response_data = {"success": True, "record": new_record}
                else:
                    response_data = {"success": False, "error": "Failed to add record"}
                    
        elif request_type == "GET_SALES_PROJECTS":
            user_id = req_data.get('user_id')
            projects = get_projects_by_user(user_id)
            response_data = projects
            
        elif request_type == "GET_ENGINEER_JOBS":
            engineer_name = req_data.get('engineer_name')
            projects = get_accepted_projects_by_engineer(engineer_name)
            response_data = projects
            
        elif request_type == "GET_ALL_NOTICES_FOR_ENGINEER":
            engineer_name = req_data.get('engineer_name')
            notices = get_all_notices_for_engineer(engineer_name)
            response_data = notices
            
        # ==================== Code Generation ====================
        elif request_type == "REQUEST_CODE":
            name = req_data.get('name', '').strip()
            category = req_data.get('category', '')
            employee = req_data.get('employee', '').strip()
            
            if not name or not category or not employee:
                response_data = "INVALID_REQUEST"
            else:
                code = generate_code(used_codes, category, employee)
                if code:
                    if category != "SJT":
                        if category not in used_codes:
                            used_codes[category] = set()
                        used_codes[category].add(code)
                    history.append({
                        'name': name,
                        'employee': employee,
                        'category': category,
                        'code': code,
                        'time': __import__('datetime').datetime.now().isoformat(),
                        'parent_code': ''
                    })
                    save_data_data(used_codes, history)
                    response_data = code
                else:
                    response_data = "NO_MORE_CODES"
                    
        elif request_type == "GET_HISTORY":
            global history_version, cached_sorted_history
            current_version = len(history)
            if cached_sorted_history is None or history_version != current_version:
                cached_sorted_history = sorted(history, key=lambda x: x.get('time', ''), reverse=True)
                history_version = current_version
            
            limit = req_data.get('limit', 100)
            offset = req_data.get('offset', 0)
            if 'page' in req_data:
                page = req_data['page']
                offset = (page - 1) * limit
            
            if limit is not None and limit > 0:
                limited_history = cached_sorted_history[offset:offset + limit]
                response_data = limited_history
            else:
                response_data = cached_sorted_history
                
        elif request_type == "DELETE_HISTORY":
            pwd = req_data.get('password')
            code = req_data.get('code')
            
            if pwd != "kelly" or not code:
                response_data = "ERROR"
            else:
                to_remove = None
                for item in history:
                    if item.get('code') == code:
                        to_remove = item
                        break
                
                if to_remove:
                    category = to_remove['category']
                    employee = to_remove.get('employee', '')
                    key = f"SJT_{employee}" if category == "SJT" else category
                    
                    if key in used_codes and code in used_codes.get(key, set()):
                        used_codes.get(key, set()).remove(code)
                        deleted_codes.add(code)
                        history.remove(to_remove)
                        save_data_data(used_codes, history)
                        response_data = "DELETED"
                    else:
                        response_data = "ERROR"
                else:
                    response_data = "ERROR"
                    
        elif request_type == "SEARCH_HISTORY":
            # cached_sorted_history is already declared global in socket_api() function
            search_text = req_data.get('search_text', '').lower().strip()
            columns = req_data.get('columns', ['name', 'employee', 'category', 'code', 'time'])
            
            if cached_sorted_history is None:
                cached_sorted_history = sorted(history, key=lambda x: x.get('time', ''), reverse=True)
            
            if not search_text:
                results = cached_sorted_history
            else:
                results = []
                for item in cached_sorted_history:
                    for col in columns:
                        value = item.get(col, '')
                        if value and search_text in str(value).lower():
                            results.append(item)
                            break
            response_data = results
            
        # ==================== Authentication ====================
        elif request_type == "LOGIN":
            username = req_data.get('username', '').strip()
            password = req_data.get('password', '')
            
            user_info = get_user_with_permissions(username)
            if user_info:
                if user_info.get('status') == 'locked':
                    response_data = {"success": False, "error": "Tài khoản đã bị khóa"}
                elif user_info.get('passwords') != password:
                    response_data = {"success": False, "error": "Invalid credentials"}
                else:
                    user_info_clean = user_info.copy()
                    if 'passwords' in user_info_clean:
                        del user_info_clean['passwords']
                    response_data = {"success": True, "user_info": user_info_clean}
            else:
                response_data = {"success": False, "error": "Invalid credentials"}
                
        elif request_type == "PING":
            response_data = "PONG"
            
        else:
            response_data = {"success": False, "error": f"Unknown request type: {request_type}"}
        
        # Return response
        if response_data is None:
            return jsonify({"success": False, "error": "No response"}), 500
        
        if isinstance(response_data, str):
            return response_data, 200
        
        return jsonify(response_data), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({"success": False, "error": str(e)}), 500


# ========================================================================
# Tool Open API Endpoints
# ========================================================================

@app.route('/api/tool-status', methods=['GET'])
def tool_status():
    """Kiểm tra trạng thái Tool Open"""
    if not TOOL_OPEN_AVAILABLE:
        return jsonify({"status": "unavailable", "message": "Tool Open not loaded"})
    
    try:
        excel_path = material_core.normalize_unc_path(material_core.EXCEL_PATH)
        excel_exists = os.path.exists(excel_path)
        
        return jsonify({
            "status": "ready" if excel_exists else "error",
            "message": "Sẵn sàng" if excel_exists else "Không thể kết nối Excel",
            "excel_path": excel_path,
            "excel_exists": excel_exists
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)})


@app.route('/api/tool-search', methods=['POST'])
def tool_search():
    """Tìm kiếm mã liệu"""
    if not TOOL_OPEN_AVAILABLE:
        return jsonify({"type": "error", "message": "Tool Open not available"})
    
    data = request.get_json()
    code = data.get('code', '').strip().strip('"').strip("'")
    
    if not code:
        return jsonify({"type": "error", "message": "Mã không được để trống!"})
    
    try:
        if material_core.is_engineer_fig_no(code):
            all_matches = material_core.find_cinvcode_from_excel(code, return_all=True)
            
            if not all_matches:
                return jsonify({"type": "error", "message": f"Không tìm thấy cInvCode cho: {code}"})
            
            if len(all_matches) == 1:
                cinv_code = all_matches[0]['cInvCode']
                material_core.copy_to_clipboard(cinv_code)
                urls = material_core.query_material(cinv_code)
                
                if urls:
                    return jsonify({
                        "type": "success",
                        "urls": urls,
                        "folder_count": len(set(os.path.dirname(u) for u in urls)),
                        "copied_code": cinv_code,
                        "message": f"Tìm thấy {len(urls)} files"
                    })
            
            return jsonify({
                "type": "multiple",
                "matches": all_matches,
                "original_code": code,
                "message": f"Tìm thấy {len(all_matches)} kết quả"
            })
        
        urls = material_core.query_material(code)
        
        if urls:
            urls_text = "\n".join(urls)
            material_core.copy_to_clipboard(urls_text)
            
            return jsonify({
                "type": "success",
                "urls": urls,
                "folder_count": len(set(os.path.dirname(u) for u in urls)),
                "message": f"Tìm thấy {len(urls)} files"
            })
        
        return jsonify({"type": "error", "message": f"Không tìm thấy dữ liệu cho mã: {code}"})
        
    except Exception as e:
        return jsonify({"type": "error", "message": str(e)})


# ========================================================================
# Static Files & Web UI
# ========================================================================

@app.route('/favicon.ico')
def favicon():
    """Phục vụ file favicon.ico"""
    try:
        # Thử các vị trí khác nhau của favicon
        possible_paths = [
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'favicon.ico'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web', 'favicon.ico'),
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'Tool open', 'favicon.ico'),
        ]
        
        for favicon_path in possible_paths:
            if os.path.exists(favicon_path):
                return send_from_directory(os.path.dirname(favicon_path), 'favicon.ico', mimetype='image/x-icon')
        
        # Nếu không tìm thấy, trả về 204 No Content
        return '', 204
    except Exception as e:
        return '', 204

@app.route('/')
def index():
    """Trang chủ - Web Project Tracking"""
    try:
        return send_from_directory('web', 'index.html')
    except:
        return "Web not found", 404

@app.route('/<path:filename>')
def serve_static(filename):
    """Phục vụ static files"""
    try:
        # Check if file exists in web directory
        file_path = os.path.join('web', filename)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return send_from_directory('web', filename)
        return "File not found", 404
    except Exception as e:
        return str(e), 404

# ========================================================================
# Health Check
# ========================================================================

@app.route('/api/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "ok",
        "service": "server",
        "port": 8001,
        "features": {
            "socket_api": True,
            "tool_open": TOOL_OPEN_AVAILABLE,
            "web_ui": True
        }
    })

# ========================================================================
# REST API Endpoints for Web Client
# ========================================================================

@app.route('/api/login', methods=['POST'])
def api_login():
    """Đăng nhập với session management"""
    # Get client IP for rate limiting
    client_ip = request.remote_addr
    
    # Check rate limit
    allowed, remaining = check_rate_limit(client_ip)
    if not allowed:
        return jsonify({
            "success": False, 
            "error": "Quá nhiều lần thử đăng nhập. Vui lòng thử lại sau 5 phút.",
            "code": "RATE_LIMITED"
        }), 429
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Dữ liệu không hợp lệ"}), 400
    
    username = data.get('username', '').strip()
    password = data.get('password', '')
    
    if not username or not password:
        record_login_attempt(client_ip, False)
        return jsonify({"success": False, "error": "Vui lòng nhập tên đăng nhập và mật khẩu"}), 400
    
    # Authenticate with database
    user_info = get_user_with_permissions(username)
    
    if user_info:
        if user_info.get('status') == 'locked':
            record_login_attempt(client_ip, False)
            return jsonify({"success": False, "error": "Tài khoản đã bị khóa. Vui lòng liên hệ Admin."}), 401
        elif user_info.get('passwords') != password:
            record_login_attempt(client_ip, False)
            return jsonify({"success": False, "error": "Tên đăng nhập hoặc mật khẩu không đúng"}), 401
        else:
            # Record successful login
            record_login_attempt(client_ip, True)
            
            # Create session token
            token = generate_token()
            with sessions_lock:
                sessions[token] = {
                    'user': user_info,
                    'created_at': time.time(),
                    'ip': client_ip
                }
            
            # Remove password from response
            user_info_copy = user_info.copy()
            if 'passwords' in user_info_copy:
                del user_info_copy['passwords']
            
            return jsonify({
                "success": True,
                "token": token,
                "user": user_info_copy,
                "expires_in": SESSION_TIMEOUT
            })
    else:
        record_login_attempt(client_ip, False)
        return jsonify({"success": False, "error": "Tên đăng nhập hoặc mật khẩu không đúng"}), 401


@app.route('/api/logout', methods=['POST'])
def api_logout():
    """Đăng xuất"""
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        with sessions_lock:
            if token in sessions:
                del sessions[token]
    
    return jsonify({"success": True, "message": "Đăng xuất thành công"})


@app.route('/api/me', methods=['GET'])
def api_me():
    """Lấy thông tin user hiện tại"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"authenticated": False, "user": None, "reason": "no_token"})
    
    token = auth_header[7:]
    with sessions_lock:
        session_data = sessions.get(token)
        if not session_data:
            return jsonify({"authenticated": False, "user": None, "reason": "invalid_token"})
        
        # Check expiration
        created_at = session_data.get('created_at', 0)
        elapsed = time.time() - created_at
        remaining = SESSION_TIMEOUT - elapsed
        
        if remaining <= 0:
            del sessions[token]
            return jsonify({"authenticated": False, "user": None, "reason": "expired"})
        
        # Check if close to expiration (< 5 minutes)
        is_expiring_soon = remaining < 300
        
        return jsonify({
            "authenticated": True,
            "user": session_data.get('user'),
            "expires_in": int(remaining),
            "expiring_soon": is_expiring_soon
        })


@app.route('/api/profile', methods=['PUT'])
def api_profile_update():
    """Cập nhật thông tin profile của user hiện tại"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"success": False, "error": "Chưa đăng nhập"}), 401
    
    token = auth_header[7:]
    with sessions_lock:
        session_data = sessions.get(token)
        if not session_data:
            return jsonify({"success": False, "error": "Token không hợp lệ"}), 401
    
    # Get user from session
    current_user = session_data.get('user', {})
    user_id = current_user.get('user_id')
    
    if not user_id:
        return jsonify({"success": False, "error": "Không tìm thấy user"}), 400
    
    # Get data from request
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Dữ liệu không hợp lệ"}), 400
    
    # Map data fields - chỉ cho phép các field được phép thay đổi
    profile_data = {}
    allowed_fields = ['full_name', 'employee_id', 'department', 'email', 'phone']
    for field in allowed_fields:
        if field in data:
            profile_data[field] = data[field]
    
    if not profile_data:
        return jsonify({"success": False, "error": "Không có thông tin để cập nhật"}), 400
    
    # Update user in database
    success = update_user(user_id, profile_data)
    
    if success:
        # Update session data if full_name changed
        if 'full_name' in profile_data:
            current_user['full_name'] = profile_data['full_name']
        if 'employee_id' in profile_data:
            current_user['employee_id'] = profile_data['employee_id']
        if 'department' in profile_data:
            current_user['department'] = profile_data['department']
        if 'email' in profile_data:
            current_user['email'] = profile_data['email']
        if 'phone' in profile_data:
            current_user['phone'] = profile_data['phone']
        with sessions_lock:
            sessions[token]['user'] = current_user
        
        return jsonify({
            "success": True,
            "message": "Cập nhật hồ sơ thành công",
            "user": current_user
        })
    else:
        return jsonify({"success": False, "error": "Lỗi khi cập nhật hồ sơ"}), 500


@app.route('/api/profile/password', methods=['PUT'])
def api_profile_change_password():
    """Đổi mật khẩu của user hiện tại"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"success": False, "error": "Chưa đăng nhập"}), 401
    
    token = auth_header[7:]
    with sessions_lock:
        session_data = sessions.get(token)
        if not session_data:
            return jsonify({"success": False, "error": "Token không hợp lệ"}), 401
    
    # Get user from session
    current_user = session_data.get('user', {})
    user_id = current_user.get('user_id')
    
    if not user_id:
        return jsonify({"success": False, "error": "Không tìm thấy user"}), 400
    
    # Get data from request
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Dữ liệu không hợp lệ"}), 400
    
    current_password = data.get('current_password', '')
    new_password = data.get('new_password', '')
    confirm_password = data.get('confirm_password', '')
    
    # Validate
    if not current_password or not new_password or not confirm_password:
        return jsonify({"success": False, "error": "Vui lòng nhập đầy đủ thông tin"}), 400
    
    if new_password != confirm_password:
        return jsonify({"success": False, "error": "Mật khẩu mới không khớp"}), 400
    
    if len(new_password) < 6:
        return jsonify({"success": False, "error": "Mật khẩu mới phải có ít nhất 6 ký tự"}), 400
    
    # Get current user data to verify password
    user_info = get_user_by_username(current_user.get('username'))
    if not user_info:
        return jsonify({"success": False, "error": "Không tìm thấy thông tin user"}), 400
    
    # Verify current password
    if user_info.get('passwords') != current_password:
        return jsonify({"success": False, "error": "Mật khẩu hiện tại không đúng"}), 400
    
    # Update password
    success = update_user(user_id, {'passwords': new_password})
    
    if success:
        return jsonify({
            "success": True,
            "message": "Đổi mật khẩu thành công"
        })
    else:
        return jsonify({"success": False, "error": "Lỗi khi đổi mật khẩu"}), 500


@app.route('/api/projects', methods=['GET', 'POST'])
def api_projects():
    """Lấy danh sách dự án hoặc thêm mới"""
    if request.method == 'GET':
        # Get projects with pagination
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        sort_by = request.args.get('sort_by', 'Tracking ID')
        sort_order = request.args.get('sort_order', 'desc')
        
        result = get_paged_data_sql(page, limit, sort_by, sort_order)
        return jsonify(result)
    
    elif request.method == 'POST':
        # Add new project
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Dữ liệu không hợp lệ"}), 400
        
        # Auto-set is_pending = 'yes' for new projects
        data['is_pending'] = 'yes'
        
        new_record = add_record(data)
        if new_record:
            return jsonify({"success": True, "record": new_record}), 201
        else:
            return jsonify({"success": False, "error": "Lỗi khi thêm dự án"}), 400


@app.route('/api/projects/<int:tracking_id>', methods=['GET', 'PUT', 'DELETE'])
def api_project_detail(tracking_id):
    """Chi tiết, cập nhật hoặc xóa dự án"""
    if request.method == 'GET':
        project = get_record_by_id(tracking_id)
        if project:
            return jsonify(project)
        else:
            return jsonify({"error": "Không tìm thấy dự án"}), 404
    
    elif request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Dữ liệu không hợp lệ"}), 400
        
        success = update_record(tracking_id, data)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Lỗi khi cập nhật dự án"}), 400
    
    elif request.method == 'DELETE':
        # Check admin role
        auth_header = request.headers.get('Authorization', '')
        role = request.args.get('role', 'admin')
        
        if role != 'admin':
            return jsonify({
                "success": False,
                "error": "Bạn không có quyền xóa dự án. Chỉ Admin mới được phép thực hiện thao tác này."
            }), 403
        
        deleted_count = delete_records([tracking_id])
        return jsonify({"success": True, "deleted_count": deleted_count})


@app.route('/api/projects/search', methods=['POST'])
def api_projects_search():
    """Tìm kiếm dự án"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Dữ liệu không hợp lệ"}), 400
    
    search_text = data.get('search', '')
    page = data.get('page', 1)
    limit = data.get('limit', 50)
    sort_by = data.get('sort_by', 'Tracking ID')
    sort_order = data.get('sort_order', 'desc')
    
    from src.db_helper import search_data_sql
    result = search_data_sql(search_text, page, limit, sort_by, sort_order)
    return jsonify(result)


@app.route('/api/projects/filter', methods=['POST'])
def api_projects_filter():
    """Lọc dự án"""
    data = request.get_json()
    if not data:
        return jsonify({"error": "Dữ liệu không hợp lệ"}), 400
    
    page = data.get('page', 1)
    limit = data.get('limit', 50)
    sort_by = data.get('sort_by', 'Tracking ID')
    sort_order = data.get('sort_order', 'desc')
    
    # Remove pagination keys from filters
    filters = {k: v for k, v in data.items() if k not in ['page', 'limit', 'sort_by', 'sort_order']}
    
    from src.db_helper import filter_data_sql
    result = filter_data_sql(filters, page, limit, sort_by, sort_order)
    return jsonify(result)


@app.route('/api/codes/create', methods=['POST'])
def api_codes_create():
    """Tạo mã bản vẽ mới"""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Dữ liệu không hợp lệ"}), 400
    
    name = data.get('name', '').strip()
    category = data.get('category', '').strip()
    employee = data.get('employee', '').strip()
    
    if not name or not category or not employee:
        return jsonify({"success": False, "error": "Vui lòng nhập đầy đủ thông tin"}), 400
    
    if not (len(employee) == 3 and employee.isdigit() and employee != '000'):
        return jsonify({"success": False, "error": "Mã nhân viên phải là 3 chữ số và không phải 000"}), 400
    
    code = generate_code(used_codes, category, employee)
    if code:
        if category != "SJT":
            if category not in used_codes:
                used_codes[category] = set()
            used_codes[category].add(code)
        history.append({
            'name': name,
            'employee': employee,
            'category': category,
            'code': code,
            'time': __import__('datetime').datetime.now().isoformat(),
            'parent_code': ''
        })
        save_data_data(used_codes, history)
        return jsonify({"success": True, "code": code})
    else:
        return jsonify({"success": False, "error": "Không còn mã available cho hạng mục này"}), 400


@app.route('/api/codes/history', methods=['GET'])
def api_codes_history():
    """Lấy lịch sử tạo mã"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 100))
    
    global history_version, cached_sorted_history
    current_version = len(history)
    if cached_sorted_history is None or history_version != current_version:
        cached_sorted_history = sorted(history, key=lambda x: x.get('time', ''), reverse=True)
        history_version = current_version
    
    offset = (page - 1) * limit
    limited_history = cached_sorted_history[offset:offset + limit]
    
    return jsonify({
        "data": limited_history,
        "total": len(cached_sorted_history),
        "total_pages": (len(cached_sorted_history) + limit - 1) // limit,
        "page": page
    })


@app.route('/api/codes/export', methods=['GET'])
def api_codes_export():
    """Xuất lịch sử tạo mã"""
    global cached_sorted_history
    if cached_sorted_history is None:
        cached_sorted_history = sorted(history, key=lambda x: x.get('time', ''), reverse=True)
    
    return jsonify({
        "success": True,
        "data": cached_sorted_history,
        "total": len(cached_sorted_history)
    })


@app.route('/api/codes/history/<path:code>', methods=['DELETE'])
def api_codes_history_delete(code):
    """Xóa bản ghi lịch sử"""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Vui lòng cung cấp mật khẩu"}), 400
    
    password = data.get('password', '')
    
    if not password:
        return jsonify({"success": False, "error": "Vui lòng cung cấp mật khẩu"}), 400
    
    if password != "kelly":
        return jsonify({"success": False, "error": "Mật khẩu không đúng"}), 400
    
    # Find and delete the code
    to_remove = None
    for item in history:
        if item.get('code') == code:
            to_remove = item
            break
    
    if not to_remove:
        return jsonify({"success": False, "error": "Mã không tồn tại trong lịch sử"}), 404
    
    category = to_remove['category']
    employee = to_remove.get('employee', '')
    key = f"SJT_{employee}" if category == "SJT" else category
    
    if key in used_codes and code in used_codes.get(key, set()):
        used_codes.get(key, set()).remove(code)
        deleted_codes.add(code)
    
    history.remove(to_remove)
    save_data_data(used_codes, history)
    
    return jsonify({"success": True, "message": "Đã xóa thành công"})


@app.route('/api/logs', methods=['POST'])
def api_logs():
    """Gửi log từ web client"""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Dữ liệu không hợp lệ"}), 400
    
    log_content = data.get('content', '')
    log_type = data.get('type', 'general')
    
    if not log_content:
        return jsonify({"success": False, "error": "Nội dung log trống"}), 400
    
    # Get username if authenticated
    username = "anonymous"
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        with sessions_lock:
            session_data = sessions.get(token)
            if session_data:
                username = session_data.get('user', {}).get('username', 'anonymous')
    
    # Create log file
    import datetime
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    log_filename = f"web_log_{timestamp}.txt"
    
    log_entry = f"""=== Web Log Submission ===
Thời gian: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Người dùng: {username}
Loại log: {log_type}
=== Nội dung ===
{log_content}

"""
    
    try:
        with open(log_filename, 'w', encoding='utf-8') as f:
            f.write(log_entry)
        
        return jsonify({
            "success": True, 
            "message": "Log đã được lưu thành công",
            "filename": log_filename
        })
    except Exception as e:
        return jsonify({"success": False, "error": f"Lỗi khi lưu log: {str(e)}"}), 500

# ========================================================================
# Parent Code Search Endpoints (for taomabanve.html)
# ========================================================================

@app.route('/api/codes/search-parent', methods=['GET'])
def api_codes_search_parent():
    """Tìm parent code cho một mã"""
    code = request.args.get('code', '').strip()
    
    if not code:
        return jsonify({"success": False, "error": "Mã không được để trống"}), 400
    
    try:
        parent_code = find_cinvcode_from_excel(code)
        
        if parent_code:
            return jsonify({
                "success": True,
                "parent_code": parent_code
            })
        else:
            return jsonify({
                "success": False,
                "parent_code": None,
                "message": "Không tìm thấy mã mẹ"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Lỗi khi tìm kiếm Mã mẹ: {str(e)}"
        }), 500


@app.route('/api/codes/search-parent-batch', methods=['GET'])
def api_codes_search_parent_batch():
    """Tìm parent codes cho nhiều mã (GET)"""
    codes_param = request.args.get('codes', '')
    codes = [c.strip() for c in codes_param.split(',') if c.strip()]
    
    if not codes:
        return jsonify({"success": False, "error": "Danh sách mã trống"}), 400
    
    try:
        import time
        start_time = time.time()
        
        results = find_parent_codes_batch(codes)
        
        elapsed = time.time() - start_time
        
        return jsonify({
            "success": True,
            "results": results,
            "count": len(results),
            "total_requested": len(codes),
            "elapsed_seconds": round(elapsed, 3)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Lỗi khi tìm kiếm batch: {str(e)}"
        }), 500


@app.route('/api/codes/search-parent-batch-post', methods=['POST'])
def api_codes_search_parent_batch_post():
    """Tìm parent codes cho nhiều mã (POST)"""
    data = request.get_json()
    codes = data.get('codes', [])
    
    if not codes or not isinstance(codes, list):
        return jsonify({"success": False, "error": "Danh sách mã trống"}), 400
    
    try:
        import time
        start_time = time.time()
        
        results = find_parent_codes_batch(codes)
        
        elapsed = time.time() - start_time
        
        return jsonify({
            "success": True,
            "results": results,
            "count": len(results),
            "total_requested": len(codes),
            "elapsed_seconds": round(elapsed, 3)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Lỗi khi tìm kiếm batch: {str(e)}"
        }), 500


# ========================================================================
# Customer API Endpoints
# ========================================================================

@app.route('/api/customers', methods=['GET'])
def api_customers():
    """Lấy danh sách khách hàng cho dropdown"""
    try:
        conn = sqlite3.connect('DB.db')
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Lấy tất cả customers với các trường cần thiết
        cursor.execute('''
            SELECT code, name, phonetic, english_name 
            FROM customers 
            WHERE code IS NOT NULL AND code != ''
            ORDER BY code
        ''')
        results = cursor.fetchall()
        conn.close()
        
        customers = []
        for row in results:
            customers.append({
                'code': row['code'] or '',
                'name': row['name'] or '',
                'phonetic': row['phonetic'] or '',
                'english_name': row['english_name'] or ''
            })
        
        return jsonify({
            "success": True,
            "data": customers,
            "total": len(customers)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ========================================================================
# Notice/Pending Tab API Endpoints (for web client)
# ========================================================================

@app.route('/api/notices/pending', methods=['GET'])
def api_notices_pending():
    """Lấy danh sách thông báo chờ xử lý"""
    user_id_str = request.args.get('user_id')
    user_id = int(user_id_str) if user_id_str and user_id_str.isdigit() else None
    
    try:
        notices = get_pending_notices(user_id)
        return jsonify({
            "success": True,
            "data": notices,
            "total": len(notices)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/notices/count', methods=['GET'])
def api_notices_count():
    """Lấy số lượng thông báo chờ"""
    user_id_str = request.args.get('user_id')
    user_id = int(user_id_str) if user_id_str and user_id_str.isdigit() else None
    
    try:
        count = get_pending_count(user_id)
        return jsonify({
            "success": True,
            "count": count
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/notices/engineer', methods=['GET'])
def api_notices_engineer():
    """Lấy tất cả thông báo cho kỹ sư (pending + accepted)"""
    engineer_name = request.args.get('engineer_name')
    
    if not engineer_name:
        return jsonify({
            "success": False,
            "error": "Thiếu tên kỹ sư"
        }), 400
    
    try:
        notices = get_all_notices_for_engineer(engineer_name)
        return jsonify({
            "success": True,
            "data": notices,
            "total": len(notices)
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/api/notices/accept', methods=['POST'])
def api_notices_accept():
    """Kỹ sư nhận job"""
    data = request.get_json()
    if not data:
        return jsonify({
            "success": False,
            "error": "Dữ liệu không hợp lệ"
        }), 400
    
    tracking_id = data.get('tracking_id')
    engineer_name = data.get('engineer_name')
    
    if not tracking_id or not engineer_name:
        return jsonify({
            "success": False,
            "error": "Thiếu tracking_id hoặc engineer_name"
        }), 400
    
    try:
        success = accept_job(tracking_id, engineer_name)
        if success:
            return jsonify({
                "success": True,
                "message": f"Đã nhận job {tracking_id}"
            })
        else:
            return jsonify({
                "success": False,
                "error": "Không thể nhận job"
            }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# ========================================================================
# Ollama API Proxy (for WAN access)
# ========================================================================

# Gemini API Configuration
GEMINI_API_KEY = None
GEMINI_MODEL = 'gemini-3-flash-preview'

# OpenRouter Retry Configuration
OPENROUTER_RETRY_CONFIG = {
    'max_retries': 3,
    'initial_delay_ms': 1000,
    'max_delay_ms': 10000,
    'timeout_seconds': 60
}

# System Prompt - AI để hiểu hệ thống
SYSTEM_PROMPT = """Bạn là trợ lý AI của Propack VP - hệ thống quản lý dự án và mã bản vẽ.

## HỆ THỐNG PROPACK VP

### 1. WORKFLOW SALES → ENGINEER
- Sales tạo Project mới → Lưu vào DB với is_pending='yes'
- Job mới hiển thị trong tab Notice (thông báo chờ)
- Engineer nhấn nút "Nhận Job" → Cập nhật is_pending='no', accepted_by=tên Engineer, accepted_at=thời gian
- Job biến khỏi danh sách chờ, được chuyển cho Engineer

### 2. DANH MỤC SẢN PHẨM (Loại sản phẩm)
- SJT:散件图 - Bản vẽ tách chi tiết
- WLJ:物料架 - Giá đựng vật liệu
- ZZC:周转车 - Xe trung chuyển
- GZT:工作台 - Bàn thao tác
- WCP:无尘棚 - Phòng sạch
- LSX:流水线 - Băng tải
- ZWJ:转弯机 - Băng tải chuyển hướng 90/180 độ
- GZL:改造类 - Cải tạo
- BSX:倍速线 - Băng chuyền xích
- WLL:围栏类 - Hàng rào
- GTX:滚筒线 - Băng chuyền con lăn
- ZHT:展会图 - Bản vẽ mặt bằng
- LHX:老化线 - Băng chuyền lão hóa

### 3. QUY TẮC MÃ BẢN VẼ
- SJT (散件图): PSJT{employee}-{serial}-00-A0 (vd: PSJT001-0001-00-A0)
  - employee: 3 chữ số (001, 002, ...)
  - serial: 0001-9999
- Các loại khác: P{prefix}{number}-0000-00-A0
  - WLJ → PWLJ001-0000-00-A0
  - ZZC → PZZC001-0000-00-A0
  - LSX → PLSX001-0000-00-A0
  - ...

### 4. DATABASE SCHEMA (bảng projects)
- tracking_id: INTEGER PRIMARY KEY
- Created_Date: DATE
- khach_hang: VARCHAR(200) - Tên khách hàng
- nhan_vien_kinh_doanh: VARCHAR(100) - Nhân viên kinh doanh
- ten_san_pham: VARCHAR(200) - Tên sản phẩm
- quy_cach: TEXT - Quy cách
- nguoi_lien_he_kh: VARCHAR(100) - Người liên hệ khách hàng
- so_luong: INTEGER - Số lượng
- ma_po: VARCHAR(50) - Mã PO
- ma_ban_ve: VARCHAR(50) - Mã bản vẽ phương án
- ma_me: VARCHAR(50) - Mã mẹ (parent code)
- loai_san_pham: VARCHAR(100) - Loại sản phẩm (SJT, WLJ, LSX...)
- user_id: INTEGER - ID người tạo
- is_pending: VARCHAR(10) - 'yes' = chờ nhận, 'no' = đã nhận
- accepted_by: VARCHAR(100) - Người nhận job
- accepted_at: TEXT - Thời gian nhận (ISO format)
- urgency_level: VARCHAR(20) - Mức độ khẩn cấp (normal/urgent/very_urgent)

### 5. API ENDPOINTS
- POST /api/socket - Socket API (ADD_SALES_RECORD, ACCEPT_JOB, ...)
- GET /api/notices/pending - Lấy danh sách job chờ (is_pending='yes')
- POST /api/notices/accept - Engineer nhận job
- POST /api/projects - Thêm project mới
- GET /api/projects - Lấy danh sách projects (phân trang)
- POST /api/codes/create - Tạo mã bản vẽ mới
- GET /api/codes/search-parent?code=xxx - Tìm mã mẹ

### 6. USER ROLES
- Sales: Tạo project, xem lịch sử
- Engineer: Nhận job, xem job đã nhận
- Admin: Tất cả quyền

Khi trả lời, hãy:
1. Hiểu context của hệ thống này
2. Trả lời bằng tiếng Việt
3. Nếu user hỏi về workflow, mã bản vẽ, hoặc dự án, hãy dựa vào kiến thức trên
4. Nếu cần thông tin về database, có thể truy vấn qua API

CURRENT_USER_INFO: Chưa đăng nhập (guest)"""

def get_user_session_info():
    """Lấy thông tin user từ session để bổ sung vào system prompt"""
    try:
        user_info = session.get('user', {})
        if user_info:
            username = user_info.get('username', 'unknown')
            role = user_info.get('role', 'unknown')
            full_name = user_info.get('full_name', '')
            user_id = user_info.get('user_id', '')
            employee_id = user_info.get('employee_id', '')
            
            return f"""
## THÔNG TIN USER HIỆN TẠI
- Username: {username}
- Role: {role}
- Full Name: {full_name}
- User ID: {user_id}
- Employee ID: {employee_id}

Lưu ý: Đây là user đang sử dụng AI. Nếu họ hỏi về dự án của họ, hãy:
- Nếu là Sales: Xem projects với user_id = {user_id}
- Nếu là Engineer: Xem projects với accepted_by = '{username}'
"""
        return ""
    except:
        return ""

def get_full_system_prompt():
    """Lấy full system prompt bao gồm thông tin user"""
    return SYSTEM_PROMPT + get_user_session_info()

# Fallback models for rate limiting
OPENROUTER_FALLBACK_MODELS = [
    'google/gemini-2.0-flash-exp:free',
    'google/gemini-1.5-flash-8b:free',
    'meta-llama/llama-3.1-8b-instruct'
]

def load_gemini_config():
    """Load Gemini API key from credentials.json"""
    global GEMINI_API_KEY
    try:
        cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
        if os.path.exists(cred_path):
            with open(cred_path, 'r', encoding='utf-8') as f:
                creds = json.load(f)
                GEMINI_API_KEY = creds.get('gemini_api_key', '')
                if GEMINI_API_KEY:
                    safe_print(f"[Gemini] API Key loaded successfully")
                else:
                    safe_print("[Gemini] No API key found in credentials.json")
        else:
            safe_print("[Gemini] credentials.json not found")
    except Exception as e:
        safe_print(f"[Gemini] Error loading config: {e}")

def load_credentials():
    """Load all credentials from credentials.json"""
    try:
        cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
        if os.path.exists(cred_path):
            with open(cred_path, 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception as e:
        safe_print(f"[Credentials] Error loading: {e}")
    return {}

def load_ai_retry_config():
    """Load AI retry configuration from credentials.json"""
    global OPENROUTER_RETRY_CONFIG, OPENROUTER_FALLBACK_MODELS
    try:
        creds = load_credentials()
        retry_config = creds.get('ai_retry', {})
        if retry_config:
            OPENROUTER_RETRY_CONFIG.update(retry_config)
            safe_print(f"[AI Retry] Config loaded: {OPENROUTER_RETRY_CONFIG}")
        
        fallback = creds.get('fallback_models', [])
        if fallback:
            OPENROUTER_FALLBACK_MODELS = fallback
            safe_print(f"[AI Retry] Fallback models: {OPENROUTER_FALLBACK_MODELS}")
    except Exception as e:
        safe_print(f"[AI Retry] Error loading config: {e}")

def is_rate_limit_error(response):
    """Check if response indicates rate limiting (429)"""
    try:
        data = response.json() if hasattr(response, 'json') else json.loads(response)
        if isinstance(data, dict):
            error = data.get('error', {})
            if isinstance(error, dict):
                code = error.get('code', 0)
                if code == 429:
                    return True
                # Also check for rate limit in message
                msg = str(error.get('message', '')).lower()
                if 'rate' in msg and 'limit' in msg:
                    return True
    except:
        pass
    return False

def exponential_backoff(attempt, initial_delay_ms, max_delay_ms):
    """Calculate delay with exponential backoff"""
    delay = min(initial_delay_ms * (2 ** attempt), max_delay_ms)
    # Add some jitter
    import random
    jitter = random.randint(0, 1000)
    return (delay + jitter) / 1000  # Convert to seconds

def call_openrouter_with_retry(api_key, model, messages, timeout=60):
    """
    Call OpenRouter API with retry logic and fallback models.
    Returns: (response_text, model_used, error_message)
    """
    import time
    
    # Get config
    max_retries = OPENROUTER_RETRY_CONFIG.get('max_retries', 3)
    initial_delay = OPENROUTER_RETRY_CONFIG.get('initial_delay_ms', 1000)
    max_delay = OPENROUTER_RETRY_CONFIG.get('max_delay_ms', 10000)
    
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
        'Accept': 'application/json'
    }
    
    payload = {
        'model': model,
        'messages': messages,
        'stream': False
    }
    
    # Track which models we tried
    models_tried = [model]
    current_model = model
    
    # Try original model first with retries
    for attempt in range(max_retries):
        try:
            safe_print(f"[OpenRouter Retry] Attempt {attempt + 1}/{max_retries} with model: {current_model}")
            
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=timeout
            )
            
            # Check for rate limit
            if response.status_code == 429:
                safe_print(f"[OpenRouter Retry] Rate limited (429) on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    delay = exponential_backoff(attempt, initial_delay, max_delay)
                    safe_print(f"[OpenRouter Retry] Waiting {delay:.2f}s before retry...")
                    time.sleep(delay)
                    continue
                else:
                    # All retries exhausted, try fallback
                    break
            
            if response.status_code >= 400:
                safe_print(f"[OpenRouter Retry] Error {response.status_code}: {response.text[:200]}")
                # Check if it's a rate limit error in the response body
                try:
                    error_data = response.json()
                    if is_rate_limit_error(response):
                        if attempt < max_retries - 1:
                            delay = exponential_backoff(attempt, initial_delay, max_delay)
                            safe_print(f"[OpenRouter Retry] Rate limit detected, waiting {delay:.2f}s...")
                            time.sleep(delay)
                            continue
                except:
                    pass
                
                if attempt < max_retries - 1:
                    delay = exponential_backoff(attempt, initial_delay, max_delay)
                    time.sleep(delay)
                    continue
                else:
                    break
            
            # Success
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0].get('message', {}).get('content', '')
                return content, current_model, None
            
            return '', current_model, 'No content in response'
            
        except requests.exceptions.Timeout:
            safe_print(f"[OpenRouter Retry] Timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                delay = exponential_backoff(attempt, initial_delay, max_delay)
                time.sleep(delay)
                continue
        except Exception as e:
            safe_print(f"[OpenRouter Retry] Exception: {e}")
            if attempt < max_retries - 1:
                delay = exponential_backoff(attempt, initial_delay, max_delay)
                time.sleep(delay)
                continue
            break
    
    # All retries failed, try fallback models
    safe_print("[OpenRouter Retry] All retries exhausted, trying fallback models...")
    
    # Filter out already tried models
    available_fallbacks = [m for m in OPENROUTER_FALLBACK_MODELS if m not in models_tried]
    
    for fallback_model in available_fallbacks:
        try:
            safe_print(f"[OpenRouter Retry] Trying fallback model: {fallback_model}")
            models_tried.append(fallback_model)
            
            # Update payload with new model
            fallback_payload = payload.copy()
            fallback_payload['model'] = fallback_model
            
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json=fallback_payload,
                timeout=timeout
            )
            
            if response.status_code == 429:
                safe_print(f"[OpenRouter Retry] Fallback model also rate limited")
                continue
            
            if response.status_code >= 400:
                safe_print(f"[OpenRouter Retry] Fallback error: {response.status_code}")
                continue
            
            result = response.json()
            if 'choices' in result and len(result['choices']) > 0:
                content = result['choices'][0].get('message', {}).get('content', '')
                safe_print(f"[OpenRouter Retry] Fallback model {fallback_model} succeeded!")
                return content, fallback_model, None
            
        except Exception as e:
            safe_print(f"[OpenRouter Retry] Fallback exception: {e}")
            continue
    
    return None, model, "All retry attempts and fallback models failed"

# Load AI config on startup
load_ai_retry_config()

# Default Ollama URLs (always include port)
DEFAULT_OLLAMA_URLS = [
    'http://localhost:11434',
    'http://127.0.0.1:11434',
    'http://0.0.0.0:11434',
]

# Store the actual resolved URL for debugging
OLLAMA_RESOLVED_URL = None

# Get OLLAMA_URL from environment or try to discover
def get_ollama_url():
    """Try to get working Ollama URL with improved auto-discovery"""
    # First check OLLAMA_HOST environment variable (higher priority)
    ollama_host = os.environ.get('OLLAMA_HOST')
    if ollama_host:
        # Ensure it has http:// prefix and port
        if not ollama_host.startswith('http'):
            ollama_host = f'http://{ollama_host}'
        # Ensure port is included (default to 11434 if missing)
        if ':' not in ollama_host.split('//')[-1]:
            ollama_host = f"{ollama_host}:11434"
        safe_print(f"[Ollama] Using OLLAMA_HOST: {ollama_host}")
        return ollama_host
    
    # Also check OLLAMA_URL for backwards compatibility
    env_url = os.environ.get('OLLAMA_URL')
    if env_url:
        # Ensure port is included
        if not env_url.startswith('http'):
            env_url = f'http://{env_url}'
        if ':' not in env_url.split('//')[-1]:
            env_url = f"{env_url}:11434"
        return env_url
    
    # Try each URL in order (with port)
    for url in DEFAULT_OLLAMA_URLS:
        try:
            resp = requests.get(f"{url}/api/tags", timeout=3)
            if resp.ok:
                safe_print(f"[Ollama] Auto-discovered working URL: {url}")
                return url
        except:
            continue
    
    # Default to localhost with port
    return 'http://localhost:11434'

OLLAMA_URL = get_ollama_url()
OLLAMA_ENABLED = True

@app.route('/api/debug-ip', methods=['GET'])
def debug_ip():
    """Debug endpoint to see request details"""
    return jsonify({
        "remote_addr": request.remote_addr,
        "host": request.host,
        "url": request.url,
        "headers": dict(request.headers)
    })


@app.route('/api/ollama-test', methods=['POST', 'OPTIONS'])
def ollama_test():
    """Test endpoint to diagnose Ollama issues"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    data = request.get_json() or {}
    prompt = data.get('prompt', 'Hello')
    model = data.get('model', 'qwen3:8b')
    
    safe_print(f"[Ollama Test] Received request - model: {model}, prompt: {prompt}")
    safe_print(f"[Ollama Test] OLLAMA_URL: {OLLAMA_URL}")
    safe_print(f"[Ollama Test] Request from IP: {request.remote_addr}")
    
    # Try to call Ollama directly
    try:
        target_url = f"{OLLAMA_URL}/api/generate"
        safe_print(f"[Ollama Test] Calling: {target_url}")
        
        resp = requests.post(
            target_url,
            json={
                "model": model,
                "prompt": prompt,
                "stream": False
            },
            timeout=60
        )
        
        safe_print(f"[Ollama Test] Response status: {resp.status_code}")
        safe_print(f"[Ollama Test] Response body: {resp.text[:200]}")
        
        if resp.ok:
            return jsonify({
                "success": True,
                "status_code": resp.status_code,
                "response": resp.json()
            })
        else:
            return jsonify({
                "success": False,
                "status_code": resp.status_code,
                "error": resp.text,
                "ollama_url": OLLAMA_URL
            }), resp.status_code
            
    except Exception as e:
        safe_print(f"[Ollama Test] Exception: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "ollama_url": OLLAMA_URL
        }), 500


@app.route('/api/ollama/<path:ollama_path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
def ollama_proxy(ollama_path):
    """Proxy requests to Ollama server with improved error handling"""
    # Handle OPTIONS preflight
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    if not OLLAMA_ENABLED:
        return jsonify({
            "error": "Ollama đang tắt. Vui lòng bật Ollama server.",
            "hint": "Chạy 'ollama serve' để khởi động Ollama"
        }), 503
    
    # Log ALL requests for debugging
    safe_print(f"="*50)
    safe_print(f"[Ollama Proxy] NEW REQUEST:")
    safe_print(f"  Path: {ollama_path}")
    safe_print(f"  Method: {request.method}")
    safe_print(f"  Remote IP: {request.remote_addr}")
    safe_print(f"  Host: {request.host}")
    safe_print(f"  Origin: {request.headers.get('Origin', 'N/A')}")
    safe_print(f"  User-Agent: {request.headers.get('User-Agent', 'N/A')[:50]}")
    
    try:
        # Build the target URL
        target_url = f"{OLLAMA_URL}/{ollama_path}"
        safe_print(f"[Ollama Proxy] Forwarding to: {target_url}")
        
        # Get headers from original request (except host)
        headers = {key: value for key, value in request.headers if key.lower() != 'host'}
        safe_print(f"[Ollama Proxy] Headers: {headers}")
        
        # Get request body for logging
        request_body = request.get_data()
        safe_print(f"[Ollama Proxy] Body length: {len(request_body)} bytes")
        
        # Handle different methods
        if request.method == 'GET':
            resp = requests.get(target_url, headers=headers, timeout=30)
        elif request.method == 'POST':
            resp = requests.post(
                target_url, 
                headers=headers, 
                json=request.get_json(), 
                timeout=120
            )
        elif request.method == 'PUT':
            resp = requests.put(
                target_url, 
                headers=headers, 
                json=request.get_json(), 
                timeout=120
            )
        elif request.method == 'DELETE':
            resp = requests.delete(target_url, headers=headers, timeout=30)
        else:
            return jsonify({"error": "Method not allowed"}), 405
        
        # Log the response status
        safe_print(f"[Ollama Proxy] Response status: {resp.status_code}")
        safe_print(f"[Ollama Proxy] Response headers: {dict(resp.headers)}")
        
        # Debug: Log full request and response for troubleshooting
        if resp.status_code >= 400:
            safe_print(f"[Ollama Proxy] FULL REQUEST DEBUG:")
            safe_print(f"  Target URL: {target_url}")
            safe_print(f"  Request method: {request.method}")
            safe_print(f"  Request headers: {dict(request.headers)}")
            safe_print(f"  Request body: {request.get_json()}")
            safe_print(f"  Response status: {resp.status_code}")
            safe_print(f"  Response body: {resp.text[:500]}")
        
        # Debug: Log response content for 403 errors
        if resp.status_code == 403:
            try:
                error_data = resp.json()
                safe_print(f"[Ollama Proxy] 403 Error response JSON: {error_data}")
            except:
                safe_print(f"[Ollama Proxy] 403 Error response text: {resp.text[:500]}")
        
        # If Ollama returns error status, provide helpful message
        if resp.status_code >= 400:
            error_msg = f"Ollama server trả về lỗi {resp.status_code}"
            error_details = {}
            
            try:
                error_data = resp.json()
                if 'error' in error_data:
                    error_msg = f"Ollama: {error_data['error']}"
                    error_details['ollama_error'] = error_data['error']
            except:
                pass
            
            # Provide specific guidance for 403 Forbidden
            if resp.status_code == 403:
                safe_print(f"[Ollama Proxy] 403 Forbidden - Access denied to Ollama at {OLLAMA_URL}")
                
                # Try to get more details from response
                try:
                    error_data = resp.json()
                    ollama_error = error_data.get('error', '')
                except:
                    ollama_error = ''
                
                return jsonify({
                    "error": "Ollama server từ chối truy cập (403 Forbidden)",
                    "ollama_url": OLLAMA_URL,
                    "ollama_error": ollama_error,
                    "hint": "Có thể do: (1) Ollama chưa được cấu hình cho phép remote access, (2) IP bị chặn, (3) Cần thiết lập OLLAMA_HOST=0.0.0.0:11434 khi chạy Ollama",
                    "fix_instructions": "Để cho phép remote access, hãy chạy:\n• Windows: set OLLAMA_HOST=0.0.0.0:11434 && ollama serve\n• Linux/Mac: export OLLAMA_HOST=0.0.0.0:11434 && ollama serve\n\nHoặc thêm vào config: { \"host\": \"0.0.0.0:11434\" }",
                    "debug_info": {
                        "target_url": target_url,
                        "response_status": resp.status_code,
                        "ollama_host_env": os.environ.get('OLLAMA_HOST', 'not set'),
                        "ollama_url_env": os.environ.get('OLLAMA_URL', 'not set')
                    },
                    "details": error_details
                }), 403
            
            # Provide specific guidance for connection issues
            if resp.status_code == 503:
                safe_print(f"[Ollama Proxy] 503 Service Unavailable - Ollama may not be running")
                return jsonify({
                    "error": "Ollama server không khả dụng (503)",
                    "ollama_url": OLLAMA_URL,
                    "hint": "Vui lòng khởi động Ollama bằng lệnh 'ollama serve' trong terminal",
                    "details": error_details
                }), 503
            
            return jsonify({
                "error": error_msg,
                "ollama_url": OLLAMA_URL,
                "hint": "Vui lòng kiểm tra Ollama server có đang chạy không",
                "details": error_details
            }), resp.status_code
        
        # Return the response from Ollama
        response = make_response(resp.content, resp.status_code)
        response.headers['Content-Type'] = resp.headers.get('Content-Type', 'application/json')
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except requests.exceptions.ConnectionError as e:
        safe_print(f"[Ollama Proxy] Connection error: {e}")
        
        # Get environment info for debugging
        ollama_host_env = os.environ.get('OLLAMA_HOST', 'not set')
        ollama_url_env = os.environ.get('OLLAMA_URL', 'not set')
        
        return jsonify({
            "error": "Không thể kết nối đến Ollama server",
            "ollama_url": OLLAMA_URL,
            "details": str(e),
            "hint": "Vui lòng đảm bảo Ollama đang chạy (thường là localhost:11434). \n\nĐể khởi động Ollama, hãy chạy lệnh 'ollama serve' trong terminal.\n\nĐể cho phép remote access, hãy thiết lập:\n• Windows: set OLLAMA_HOST=0.0.0.0:11434\n• Linux/Mac: export OLLAMA_HOST=0.0.0.0:11434",
            "debug_info": {
                "target_url": target_url,
                "ollama_host_env": ollama_host_env,
                "ollama_url_env": ollama_url_env,
                "troubleshooting": "Kiểm tra: (1) Ollama đang chạy, (2) Firewall không chặn, (3) Đúng port 11434"
            }
        }), 503
    except requests.exceptions.Timeout:
        safe_print(f"[Ollama Proxy] Timeout")
        return jsonify({
            "error": "Yêu cầu Ollama hết thời gian chờ",
            "hint": "Model có thể đang tải, vui lòng thử lại sau. Nếu vẫn lỗi, hãy thử model nhẹ hơn."
        }), 504
    except Exception as e:
        safe_print(f"[Ollama Proxy] Error: {e}")
        return jsonify({
            "error": f"Lỗi proxy Ollama: {str(e)}",
            "hint": "Liên hệ admin nếu lỗi tiếp tục"
        }), 500


@app.route('/api/ollama-models', methods=['GET', 'OPTIONS'])
def ollama_models():
    """Get available Ollama models"""
    # Handle OPTIONS preflight
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    if not OLLAMA_ENABLED:
        return jsonify({
            "error": "Ollama đang tắt",
            "models": [],
            "hint": "Bật Ollama server để sử dụng tính năng AI"
        }), 200
    
    try:
        safe_print(f"[Ollama] Checking models at {OLLAMA_URL}")
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
        
        if resp.status_code >= 400:
            safe_print(f"[Ollama] Error getting models: {resp.status_code}")
            return jsonify({
                "error": f"Ollama server lỗi: {resp.status_code}",
                "models": [],
                "hint": "Kiểm tra Ollama đang chạy"
            }), 200
        
        response = make_response(resp.content, resp.status_code)
        response.headers['Content-Type'] = resp.headers.get('Content-Type', 'application/json')
        response.headers['Access-Control-Allow-Origin'] = '*'
        return response
    except requests.exceptions.ConnectionError as e:
        safe_print(f"[Ollama] Connection failed: {e}")
        return jsonify({
            "error": "Không thể kết nối Ollama server",
            "models": [],
            "ollama_url": OLLAMA_URL,
            "hint": "Vui lòng chạy 'ollama serve' để khởi động Ollama"
        }), 200
    except Exception as e:
        safe_print(f"[Ollama] Error: {e}")
        return jsonify({
            "error": str(e),
            "models": []
        }), 200


@app.route('/api/ollama-status', methods=['GET', 'POST', 'OPTIONS'])
def ollama_status():
    """Get or set Ollama configuration with detailed status"""
    # Handle OPTIONS preflight
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
        return response
    
    global OLLAMA_URL, OLLAMA_ENABLED
    
    if request.method == 'POST':
        data = request.get_json()
        if data:
            if 'url' in data:
                # Validate URL format
                url = data['url']
                if not url.startswith('http'):
                    url = f'http://{url}'
                OLLAMA_URL = url
                safe_print(f"[Ollama] URL updated to: {OLLAMA_URL}")
            if 'enabled' in data:
                OLLAMA_ENABLED = data['enabled']
                safe_print(f"[Ollama] Enabled: {OLLAMA_ENABLED}")
        
        return jsonify({
            "success": True,
            "url": OLLAMA_URL,
            "enabled": OLLAMA_ENABLED
        })
    
    # GET - check status with detailed information
    # Try to connect to Ollama and collect info
    can_connect = False
    error_msg = None
    tried_urls = []
    
    # Try current URL first
    try:
        resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=5)
        can_connect = resp.ok
        tried_urls.append({
            "url": OLLAMA_URL,
            "status": "success" if resp.ok else f"error_{resp.status_code}",
            "status_code": resp.status_code
        })
    except Exception as e:
        error_msg = str(e)
        tried_urls.append({
            "url": OLLAMA_URL,
            "status": "connection_failed",
            "error": str(e)
        })
    
    # If current URL fails, try others for discovery
    if not can_connect:
        for url in DEFAULT_OLLAMA_URLS:
            if url == OLLAMA_URL:
                continue
            try:
                resp = requests.get(f"{url}/api/tags", timeout=3)
                tried_urls.append({
                    "url": url,
                    "status": "success" if resp.ok else f"error_{resp.status_code}",
                    "status_code": resp.status_code
                })
                if resp.ok and not can_connect:
                    # Optionally suggest this URL works
                    safe_print(f"[Ollama] Found working URL: {url}")
            except Exception as e:
                tried_urls.append({
                    "url": url,
                    "status": "connection_failed",
                    "error": str(e)
                })
    
    return jsonify({
        "url": OLLAMA_URL,
        "enabled": OLLAMA_ENABLED,
        "connected": can_connect,
        "error": error_msg,
        "tried_urls": tried_urls,
        "environment": {
            "OLLAMA_HOST": os.environ.get('OLLAMA_HOST', 'not set'),
            "OLLAMA_URL": os.environ.get('OLLAMA_URL', 'not set')
        },
        "fix_instructions": "Để cho phép remote access, hãy chạy:\n• Windows: set OLLAMA_HOST=0.0.0.0:11434 && ollama serve\n• Linux/Mac: export OLLAMA_HOST=0.0.0.0:11434 && ollama serve"
    })


# ========================================================================
# Gemini AI API Endpoints (Streaming Support)
# ========================================================================

@app.route('/api/gemini/chat', methods=['POST', 'OPTIONS'])
def gemini_chat():
    """Chat với Gemini AI"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    if not GEMINI_API_KEY:
        return jsonify({
            "success": False,
            "error": "Chưa cấu hình Gemini API Key"
        }), 500
    
    data = request.get_json() or {}
    message = data.get('message', '')
    model = data.get('model', GEMINI_MODEL)
    history = data.get('history', [])
    
    # Get user info from token (Authorization header)
    auth_header = request.headers.get('Authorization', '')
    user_info_str = ''
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        with sessions_lock:
            session_data = sessions.get(token)
            if session_data:
                user = session_data.get('user', {})
                user_info_str = f"""
## THÔNG TIN USER HIỆN TẠI
- Username: {user.get('username', 'unknown')}
- Role: {user.get('role', 'unknown')}
- Full Name: {user.get('full_name', '')}
- User ID: {user.get('user_id', '')}

Lưu ý: Đây là user đang sử dụng AI. Nếu họ hỏi về dự án của họ, hãy:
- Nếu là Sales: Xem projects với user_id = {user.get('user_id', '')}
- Nếu là Engineer: Xem projects với accepted_by = '{user.get('username', '')}'"
"""
    
    if not message:
        return jsonify({
            "success": False,
            "error": "Tin nhắn không được để trống"
        }), 400
    
    try:
        # Build messages for Gemini API
        # Add system prompt as first message
        system_instruction = {
            "role": "user",
            "parts": [{"text": SYSTEM_PROMPT + user_info_str}]
        }
        contents = [system_instruction]
        
        # Add history messages
        for msg in history:
            role = msg.get('role', 'user')
            if role == 'user':
                contents.append({
                    "role": "user",
                    "parts": [{"text": msg.get('content', '')}]
                })
            else:  # model
                contents.append({
                    "role": "model",
                    "parts": [{"text": msg.get('content', '')}]
                })
        
        # Add current message
        contents.append({
            "role": "user",
            "parts": [{"text": message}]
        })
        
        # Call Gemini API
        import urllib.parse
        safe_print(f"[Gemini] Calling model: {model}")
        
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
        
        headers = {
            'Content-Type': 'application/json'
        }
        
        payload = {
            "contents": contents,
            "generationConfig": {
                "temperature": 0.9,
                "maxOutputTokens": 2048,
                "topP": 0.95,
                "topK": 40
            }
        }
        
        resp = requests.post(gemini_url, headers=headers, json=payload, timeout=60)
        
        if resp.status_code >= 400:
            safe_print(f"[Gemini] Error: {resp.status_code} - {resp.text}")
            return jsonify({
                "success": False,
                "error": f"Lỗi API: {resp.status_code}",
                "details": resp.text
            }), resp.status_code
        
        result = resp.json()
        
        # Extract response text
        response_text = ""
        if 'candidates' in result and len(result['candidates']) > 0:
            candidate = result['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                parts = candidate['content']['parts']
                response_text = "\n".join([p.get('text', '') for p in parts])
        
        if not response_text:
            response_text = "Không có phản hồi từ AI"
        
        return jsonify({
            "success": True,
            "response": response_text,
            "model": model
        })
        
    except Exception as e:
        safe_print(f"[Gemini] Exception: {e}")
        return jsonify({
            "success": False,
            "error": f"Lỗi: {str(e)}"
        }), 500


@app.route('/api/gemini/chat/stream', methods=['POST', 'OPTIONS'])
def gemini_chat_stream():
    """Chat với Gemini AI với Streaming (SSE)"""
    from flask import Response
    
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    if not GEMINI_API_KEY:
        return Response(
            f"data: {json.dumps({'error': 'Chưa cấu hình Gemini API Key'})}\n\n",
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*'
            }
        )
    
    data = request.get_json() or {}
    message = data.get('message', '')
    model = data.get('model', GEMINI_MODEL)
    history = data.get('history', [])
    
    # Get user info from token (Authorization header)
    auth_header = request.headers.get('Authorization', '')
    user_info_str = ''
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        with sessions_lock:
            session_data = sessions.get(token)
            if session_data:
                user = session_data.get('user', {})
                user_info_str = f"""
## THÔNG TIN USER HIỆN TẠI
- Username: {user.get('username', 'unknown')}
- Role: {user.get('role', 'unknown')}
- Full Name: {user.get('full_name', '')}
- User ID: {user.get('user_id', '')}

Lưu ý: Đây là user đang sử dụng AI. Nếu họ hỏi về dự án của họ, hãy:
- Nếu là Sales: Xem projects với user_id = {user.get('user_id', '')}
- Nếu là Engineer: Xem projects với accepted_by = '{user.get('username', '')}'"
"""
    
    if not message:
        return Response(
            f"data: {json.dumps({'error': 'Tin nhắn không được để trống'})}\n\n",
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*'
            }
        )
    
    def generate_stream():
        try:
            # Build messages for Gemini API
            # Add system prompt as first message
            system_instruction = {
                "role": "user",
                "parts": [{"text": SYSTEM_PROMPT + user_info_str}]
            }
            contents = [system_instruction]
            
            # Add history messages
            for msg in history:
                role = msg.get('role', 'user')
                if role == 'user':
                    contents.append({
                        "role": "user",
                        "parts": [{"text": msg.get('content', '')}]
                    })
                else:  # model
                    contents.append({
                        "role": "model",
                        "parts": [{"text": msg.get('content', '')}]
                    })
            
            # Add current message
            contents.append({
                "role": "user",
                "parts": [{"text": message}]
            })
            
            safe_print(f"[Gemini Stream] Calling model: {model}")
            
            # For streaming, we use the same API but accumulate the response
            # Note: Google Gemini API v1beta doesn't support true streaming in all cases
            # We'll simulate streaming by sending chunks of the response
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.9,
                    "maxOutputTokens": 2048,
                    "topP": 0.95,
                    "topK": 40
                }
            }
            
            # Send initial ping
            yield f"data: {json.dumps({'type': 'start'})}\n\n"
            
            resp = requests.post(gemini_url, headers=headers, json=payload, timeout=120)
            
            if resp.status_code >= 400:
                safe_print(f"[Gemini Stream] Error: {resp.status_code} - {resp.text}")
                yield f"data: {json.dumps({'error': f'Lỗi API: {resp.status_code}', 'details': resp.text[:500]})}\n\n"
                return
            
            result = resp.json()
            
            # Extract response text
            response_text = ""
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    response_text = "\n".join([p.get('text', '') for p in parts])
            
            if not response_text:
                response_text = "Không có phản hồi từ AI"
            
            # Simulate streaming by sending in chunks
            # Chunk size: 20 characters for visible streaming effect
            chunk_size = 20
            for i in range(0, len(response_text), chunk_size):
                chunk = response_text[i:i + chunk_size]
                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk, 'full': response_text})}\n\n"
                
            # Send completion
            yield f"data: {json.dumps({'type': 'done', 'full': response_text})}\n\n"
            
        except Exception as e:
            safe_print(f"[Gemini Stream] Exception: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(
        generate_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    )


# ========================================================================
# Ollama AI API Endpoints (Streaming Support)
# ========================================================================

@app.route('/api/ollama/chat/stream', methods=['POST', 'OPTIONS'])
def ollama_chat_stream():
    """Chat với Ollama với Streaming (SSE)"""
    from flask import Response
    
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    if not OLLAMA_ENABLED:
        return Response(
            f"data: {json.dumps({'error': 'Ollama đang tắt. Vui lòng bật Ollama server.'})}\n\n",
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*'
            }
        )
    
    data = request.get_json() or {}
    message = data.get('message', '')
    model = data.get('model', 'llama3.2:latest')
    history = data.get('history', [])
    stream_option = data.get('stream', True)
    
    # Get user info from token (Authorization header)
    auth_header = request.headers.get('Authorization', '')
    user_info_str = ''
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        with sessions_lock:
            session_data = sessions.get(token)
            if session_data:
                user = session_data.get('user', {})
                user_info_str = f"""
## THÔNG TIN USER HIỆN TẠI
- Username: {user.get('username', 'unknown')}
- Role: {user.get('role', 'unknown')}
- Full Name: {user.get('full_name', '')}
- User ID: {user.get('user_id', '')}

Lưu ý: Đây là user đang sử dụng AI. Nếu họ hỏi về dự án của họ, hãy:
- Nếu là Sales: Xem projects với user_id = {user.get('user_id', '')}
- Nếu là Engineer: Xem projects với accepted_by = '{user.get('username', '')}'"
"""
    
    if not message:
        return Response(
            f"data: {json.dumps({'error': 'Tin nhắn không được để trống'})}\n\n",
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*'
            }
        )
    
    def generate_stream():
        try:
            # Build prompt from history + current message
            # Add system prompt first
            prompt_parts = [f"System: {SYSTEM_PROMPT + user_info_str}"]
            for msg in history:
                role = msg.get('role', 'user')
                content = msg.get('content', '')
                if role == 'user':
                    prompt_parts.append(f"User: {content}")
                else:
                    prompt_parts.append(f"Assistant: {content}")
            
            prompt_parts.append(f"User: {message}")
            full_prompt = "\n".join(prompt_parts)
            
            safe_print(f"[Ollama Stream] Model: {model}")
            
            # Use the streaming API endpoint of Ollama
            target_url = f"{OLLAMA_URL}/api/generate"
            
            # Send initial ping
            yield f"data: {json.dumps({'type': 'start'})}\n\n"
            
            # Call Ollama with streaming
            resp = requests.post(
                target_url,
                json={
                    "model": model,
                    "prompt": full_prompt,
                    "stream": True
                },
                stream=True,
                timeout=120
            )
            
            if resp.status_code >= 400:
                safe_print(f"[Ollama Stream] Error: {resp.status_code} - {resp.text}")
                yield f"data: {json.dumps({'error': f'Lỗi API: {resp.status_code}', 'details': resp.text[:500]})}\n\n"
                return
            
            # Process streaming response from Ollama
            full_response = ""
            
            for line in resp.iter_lines():
                if line:
                    try:
                        data_json = json.loads(line.decode('utf-8'))
                        
                        if 'response' in data_json:
                            chunk = data_json['response']
                            full_response += chunk
                            
                            # Send chunk to client
                            yield f"data: {json.dumps({'type': 'chunk', 'content': chunk, 'full': full_response})}\n\n"
                        
                        # Check if done
                        if data_json.get('done', False):
                            break
                            
                    except json.JSONDecodeError:
                        continue
            
            # Send completion
            yield f"data: {json.dumps({'type': 'done', 'full': full_response})}\n\n"
            
        except requests.exceptions.ConnectionError as e:
            safe_print(f"[Ollama Stream] Connection error: {e}")
            yield f"data: {json.dumps({'error': f'Không thể kết nối đến Ollama: {str(e)}'})}\n\n"
        except Exception as e:
            safe_print(f"[Ollama Stream] Exception: {e}")
            yield f"data: {json.dumps({'error': str(e)})}\n\n"
    
    return Response(
        generate_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    )


@app.route('/api/gemini/models', methods=['GET', 'OPTIONS'])
def gemini_models():
    """Lấy danh sách models Gemini"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    if not GEMINI_API_KEY:
        return jsonify({
            "success": False,
            "error": "Chưa cấu hình Gemini API Key",
            "models": []
        }), 200
    
    # Return available Gemini models
    models = [
        {"name": "gemini-3-flash-preview", "display": "Gemini 3.0 Flash Preview (Nhanh nhất)"},
        {"name": "gemini-2.0-flash", "display": "Gemini 2.0 Flash"},
        {"name": "gemini-1.5-flash", "display": "Gemini 1.5 Flash"},
        {"name": "gemini-1.5-pro", "display": "Gemini 1.5 Pro"}
    ]
    
    return jsonify({
        "success": True,
        "models": models,
        "current_model": GEMINI_MODEL
    })


@app.route('/api/openrouter/chat/stream', methods=['POST', 'OPTIONS'])
def openrouter_chat_stream():
    """Chat với OpenRouter AI với Streaming (SSE) với retry và fallback logic"""
    from flask import Response
    
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    # Load OpenRouter API key từ credentials
    credentials = load_credentials()
    api_key = credentials.get('openrouter_api_key', '')
    
    if not api_key:
        return Response(
            f"data: {json.dumps({'error': 'OpenRouter API key chưa được cấu hình'})}\n\n",
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*'
            }
        )
    
    data = request.get_json() or {}
    message = data.get('message', '')
    model = data.get('model', 'google/gemini-2.0-flash-exp:free')
    history = data.get('history', [])
    
    # Get user info from token (Authorization header)
    auth_header = request.headers.get('Authorization', '')
    user_info_str = ''
    if auth_header.startswith('Bearer '):
        token = auth_header[7:]
        with sessions_lock:
            session_data = sessions.get(token)
            if session_data:
                user = session_data.get('user', {})
                user_info_str = f"""
## THÔNG TIN USER HIỆN TẠI
- Username: {user.get('username', 'unknown')}
- Role: {user.get('role', 'unknown')}
- Full Name: {user.get('full_name', '')}
- User ID: {user.get('user_id', '')}

Lưu ý: Đây là user đang sử dụng AI. Nếu họ hỏi về dự án của họ, hãy:
- Nếu là Sales: Xem projects với user_id = {user.get('user_id', '')}
- Nếu là Engineer: Xem projects với accepted_by = '{user.get('username', '')}'"
"""
    
    if not message:
        return Response(
            f"data: {json.dumps({'error': 'Tin nhắn không được để trống'})}\n\n",
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*'
            }
        )
    
    def generate_stream():
        import time
        
        # Get retry config
        max_retries = OPENROUTER_RETRY_CONFIG.get('max_retries', 3)
        initial_delay = OPENROUTER_RETRY_CONFIG.get('initial_delay_ms', 1000)
        max_delay = OPENROUTER_RETRY_CONFIG.get('max_delay_ms', 10000)
        
        # Track models tried
        models_tried = [model]
        current_model = model
        
        # Build messages for OpenRouter API
        # Add system prompt as first message
        messages = [{"role": "system", "content": SYSTEM_PROMPT + user_info_str}]
        for msg in history:
            role = msg.get('role', 'user')
            if role == 'user':
                messages.append({"role": "user", "content": msg.get('content', '')})
            else:
                messages.append({"role": "assistant", "content": msg.get('content', '')})
        messages.append({"role": "user", "content": message})
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json',
            'Accept': 'text/event-stream'
        }
        
        payload = {
            'model': current_model,
            'messages': messages,
            'stream': True
        }
        
        # Try original model with retries first
        for attempt in range(max_retries):
            try:
                safe_print(f"[OpenRouter Stream] Attempt {attempt + 1}/{max_retries} with model: {current_model}")
                
                # Send start signal
                yield f"data: {json.dumps({'type': 'start'})}\n\n"
                
                response = requests.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers=headers,
                    json=payload,
                    stream=True,
                    timeout=120
                )
                
                # Check for rate limit
                if response.status_code == 429:
                    safe_print(f"[OpenRouter Stream] Rate limited (429) on attempt {attempt + 1}")
                    if attempt < max_retries - 1:
                        delay = exponential_backoff(attempt, initial_delay, max_delay)
                        safe_print(f"[OpenRouter Stream] Waiting {delay:.2f}s before retry...")
                        time.sleep(delay)
                        continue
                    else:
                        # All retries exhausted, try fallback
                        break
                
                if response.status_code >= 400:
                    safe_print(f"[OpenRouter Stream] Error: {response.status_code} - {response.text[:500]}")
                    # Check if it's a rate limit in response body
                    try:
                        error_data = response.json()
                        if is_rate_limit_error(response):
                            if attempt < max_retries - 1:
                                delay = exponential_backoff(attempt, initial_delay, max_delay)
                                safe_print(f"[OpenRouter Stream] Rate limit detected, waiting {delay:.2f}s...")
                                time.sleep(delay)
                                continue
                    except:
                        pass
                    
                    if attempt < max_retries - 1:
                        delay = exponential_backoff(attempt, initial_delay, max_delay)
                        time.sleep(delay)
                        continue
                    else:
                        break
                
                # Process streaming response
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            try:
                                chunk_data = json.loads(line[6:])
                                
                                if chunk_data == '[DONE]':
                                    break
                                
                                if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                    delta = chunk_data['choices'][0].get('delta', {})
                                    if 'content' in delta and delta['content']:
                                        content = delta['content']
                                        full_response += content
                                        yield f"data: {json.dumps({'type': 'chunk', 'content': content, 'full': full_response})}\n\n"
                            except json.JSONDecodeError:
                                continue
                
                # Send completion
                yield f"data: {json.dumps({'type': 'done', 'full': full_response})}\n\n"
                return
                
            except requests.exceptions.Timeout:
                safe_print(f"[OpenRouter Stream] Timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    delay = exponential_backoff(attempt, initial_delay, max_delay)
                    time.sleep(delay)
                    continue
            except Exception as e:
                safe_print(f"[OpenRouter Stream] Exception: {e}")
                if attempt < max_retries - 1:
                    delay = exponential_backoff(attempt, initial_delay, max_delay)
                    time.sleep(delay)
                    continue
                break
        
        # All retries failed, try fallback models
        safe_print("[OpenRouter Stream] All retries exhausted, trying fallback models...")
        
        available_fallbacks = [m for m in OPENROUTER_FALLBACK_MODELS if m not in models_tried]
        
        for fallback_model in available_fallbacks:
            try:
                safe_print(f"[OpenRouter Stream] Trying fallback model: {fallback_model}")
                models_tried.append(fallback_model)
                
                # Update payload with new model
                fallback_payload = payload.copy()
                fallback_payload['model'] = fallback_model
                
                # Send start signal
                yield f"data: {json.dumps({'type': 'start', 'model_switched': fallback_model})}\n\n"
                
                response = requests.post(
                    'https://openrouter.ai/api/v1/chat/completions',
                    headers=headers,
                    json=fallback_payload,
                    stream=True,
                    timeout=120
                )
                
                if response.status_code == 429:
                    safe_print(f"[OpenRouter Stream] Fallback model also rate limited")
                    continue
                
                if response.status_code >= 400:
                    safe_print(f"[OpenRouter Stream] Fallback error: {response.status_code}")
                    continue
                
                # Process streaming response
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith('data: '):
                            try:
                                chunk_data = json.loads(line[6:])
                                
                                if chunk_data == '[DONE]':
                                    break
                                
                                if 'choices' in chunk_data and len(chunk_data['choices']) > 0:
                                    delta = chunk_data['choices'][0].get('delta', {})
                                    if 'content' in delta and delta['content']:
                                        content = delta['content']
                                        full_response += content
                                        yield f"data: {json.dumps({'type': 'chunk', 'content': content, 'full': full_response})}\n\n"
                            except json.JSONDecodeError:
                                continue
                
                # Send completion
                yield f"data: {json.dumps({'type': 'done', 'full': full_response, 'model_used': fallback_model})}\n\n"
                safe_print(f"[OpenRouter Stream] Fallback model {fallback_model} succeeded!")
                return
                
            except Exception as e:
                safe_print(f"[OpenRouter Stream] Fallback exception: {e}")
                continue
        
        # All failed
        yield f"data: {json.dumps({'error': 'Tất cả model đều thất bại. Vui lòng thử lại sau hoặc chọn model khác.', 'code': 'ALL_MODELS_FAILED'})}\n\n"
    
    return Response(
        generate_stream(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
    )


@app.route('/api/openrouter/models', methods=['GET', 'OPTIONS'])
def openrouter_models():
    """Lấy danh sách models OpenRouter"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    credentials = load_credentials()
    api_key = credentials.get('openrouter_api_key', '')
    
    if not api_key:
        return jsonify({
            "success": False,
            "error": "Chưa cấu hình OpenRouter API Key",
            "models": []
        }), 200
    
    # Return available OpenRouter models
    models = [
        {"name": "stepfun/step-3.5-flash:free", "display": "StepFun Step 3.5 Flash (Miễn phí)"},
        {"name": "google/gemini-2.0-flash-exp:free", "display": "Gemini 2.0 Flash (Miễn phí)"},
        {"name": "google/gemini-1.5-flash-8b:free", "display": "Gemini 1.5 Flash 8B (Miễn phí)"},
        {"name": "openai/gpt-4o-mini", "display": "GPT-4o Mini"},
        {"name": "anthropic/claude-3-haiku", "display": "Claude 3 Haiku"},
        {"name": "meta-llama/llama-3.1-8b-instruct", "display": "Llama 3.1 8B"}
    ]
    
    return jsonify({
        "success": True,
        "models": models
    })


@app.route('/api/openrouter/status', methods=['GET', 'OPTIONS'])
def openrouter_status():
    """Kiểm tra trạng thái OpenRouter API"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    credentials = load_credentials()
    api_key = credentials.get('openrouter_api_key', '')
    
    has_key = bool(api_key)
    
    # Test connection if API key exists
    connected = False
    error_msg = None
    
    if has_key:
        try:
            headers = {
                'Authorization': f'Bearer {api_key}',
                'Content-Type': 'application/json'
            }
            resp = requests.get(
                'https://openrouter.ai/api/v1/models',
                headers=headers,
                timeout=10
            )
            connected = resp.status_code < 400
            if not connected:
                error_msg = f"HTTP {resp.status_code}"
        except Exception as e:
            error_msg = str(e)
    
    return jsonify({
        "success": True,
        "configured": has_key,
        "connected": connected,
        "error": error_msg
    })


@app.route('/api/gemini/status', methods=['GET', 'OPTIONS'])
def gemini_status():
    """Kiểm tra trạng thái Gemini API"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    has_key = bool(GEMINI_API_KEY)
    
    # Test connection if API key exists
    connected = False
    error_msg = None
    
    if has_key:
        try:
            # Quick test with a minimal request
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
            resp = requests.post(
                gemini_url,
                headers={'Content-Type': 'application/json'},
                json={"contents": [{"role": "user", "parts": [{"text": "test"}]}]},
                timeout=10
            )
            connected = resp.status_code < 400
            if not connected:
                error_msg = f"HTTP {resp.status_code}"
        except Exception as e:
            error_msg = str(e)
    
    return jsonify({
        "success": True,
        "configured": has_key,
        "connected": connected,
        "model": GEMINI_MODEL,
        "error": error_msg
    })


@app.route('/api/gemini/config', methods=['POST', 'OPTIONS'])
def gemini_config():
    """Cấu hình Gemini API (update API key or model)"""
    if request.method == 'OPTIONS':
        response = make_response()
        response.headers['Access-Control-Allow-Origin'] = '*'
        response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    global GEMINI_API_KEY, GEMINI_MODEL
    
    data = request.get_json() or {}
    
    if 'api_key' in data:
        GEMINI_API_KEY = data['api_key']
        # Save to credentials.json
        try:
            cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
            if os.path.exists(cred_path):
                with open(cred_path, 'r', encoding='utf-8') as f:
                    creds = json.load(f)
                creds['gemini_api_key'] = GEMINI_API_KEY
                with open(cred_path, 'w', encoding='utf-8') as f:
                    json.dump(creds, f, ensure_ascii=False, indent=4)
                safe_print("[Gemini] API Key saved to credentials.json")
        except Exception as e:
            safe_print(f"[Gemini] Error saving config: {e}")
    
    if 'model' in data:
        GEMINI_MODEL = data['model']
    
    return jsonify({
        "success": True,
        "api_key_configured": bool(GEMINI_API_KEY),
        "model": GEMINI_MODEL
    })


# ========================================================================
# TCP Socket Server for Legacy Client V7
# ========================================================================

def handle_tcp_client(client_socket, client_address):
    """Handle a single TCP client connection (legacy V7 client)"""
    try:
        # Receive request data
        data = b''
        while True:
            chunk = client_socket.recv(65536)
            if not chunk:
                break
            data += chunk
            # Try to parse and check if we have complete JSON
            try:
                json.loads(data.decode('utf-8'))
                break  # Complete JSON received
            except:
                continue
        
        if not data:
            client_socket.close()
            return
        
        request_str = data.decode('utf-8')
        safe_print(f"[TCP] Received from {client_address}: {request_str[:100]}...")
        
        # Parse request
        try:
            request = json.loads(request_str)
        except json.JSONDecodeError:
            client_socket.send(b"ERROR: Invalid JSON")
            client_socket.close()
            return
        
        request_type = request.get('request', 'unknown')
        
        # Process request using the same logic as HTTP /api/socket
        # Import the global variables needed
        global db_data, cached_sorted_history, history_version, used_codes, history
        
        response_data = None
        
        # ==================== DB Operations ====================
        if request_type == "GET_DB_ALL":
            db_data = load_all()
            response_data = db_data
            
        elif request_type == "GET_DB_PROJECT":
            tracking_id = request.get('tracking_id')
            project = get_record_by_id(tracking_id)
            response_data = project
            
        elif request_type == "GET_DB_PAGED":
            page = request.get('page', 1)
            limit = request.get('limit', 50)
            sort_by = request.get('sort_by', 'Tracking ID')
            sort_order = request.get('sort_order', 'desc')
            result = get_paged_data_sql(page, limit, sort_by, sort_order)
            response_data = result
            
        elif request_type == "ADD_DB_RECORD":
            record = request.get('record', {})
            tracking_id = max([r.get("Tracking ID", 0) for r in db_data] + [0]) + 1
            record["Tracking ID"] = tracking_id
            db_data.append(record)
            save_all(db_data)
            response_data = {"success": True, "record": record}
            
        elif request_type == "UPDATE_DB_RECORD":
            tracking_id = request.get('tracking_id')
            new_data = request.get('data', {})
            success = update_record(tracking_id, new_data)
            response_data = {"success": success}
            
        elif request_type == "DELETE_DB_RECORDS":
            user_role = request.get('user_role')
            tracking_ids = request.get('tracking_ids', [])
            
            if user_role != 'admin':
                response_data = {"success": False, "error": "Bạn không có quyền xóa"}
            else:
                deleted_count = delete_records(tracking_ids)
                response_data = {"success": True, "deleted_count": deleted_count}
                
        elif request_type == "SEARCH_DB_DATA":
            search_text = request.get('search_text', '')
            columns = request.get('columns', [])
            results = db_search_data(db_data, search_text, columns)
            response_data = results
            
        elif request_type == "FILTER_DB_DATA":
            column_filters = request.get('filters', {})
            results = db_filter_data(db_data, column_filters)
            response_data = results
            
        # ==================== User Operations ====================
        elif request_type == "DB_LOGIN":
            username = request.get('username', '').strip()
            password = request.get('password', '')
            
            user_info = get_user_with_permissions(username)
            if user_info:
                if user_info.get('status') == 'locked':
                    response_data = {"success": False, "error": "Tài khoản đã bị khóa"}
                elif user_info.get('passwords') != password:
                    response_data = {"success": False, "error": "Invalid credentials"}
                else:
                    user_info_clean = user_info.copy()
                    if 'passwords' in user_info_clean:
                        del user_info_clean['passwords']
                    response_data = {"success": True, "user_info": user_info_clean}
            else:
                response_data = {"success": False, "error": "Invalid credentials"}
                
        elif request_type == "GET_USERS":
            users = get_all_users()
            response_data = users
            
        elif request_type == "ADD_USER":
            user_data = request.get('user_data', {})
            user_id = add_user(user_data)
            if user_id:
                assign_default_permissions(user_id, user_data.get('role', 'sales'))
                response_data = {"success": True, "user_id": user_id}
            else:
                response_data = {"success": False, "error": "Username already exists"}
                
        elif request_type == "UPDATE_USER":
            user_id = request.get('user_id')
            user_data = request.get('user_data', {})
            success = update_user(user_id, user_data)
            if 'permissions' in user_data:
                set_user_permissions(user_id, user_data['permissions'])
            response_data = {"success": success}
            
        elif request_type == "DELETE_USER":
            user_id = request.get('user_id')
            success = delete_user(user_id)
            response_data = {"success": success}
            
        # ==================== Notice/Pending Operations ====================
        elif request_type == "GET_PENDING_NOTICES":
            user_id = request.get('user_id')
            notices = get_pending_notices(user_id)
            response_data = notices
            
        elif request_type == "GET_PENDING_COUNT":
            user_id = request.get('user_id')
            count = get_pending_count(user_id)
            response_data = {"count": count}
            
        elif request_type == "ACCEPT_JOB":
            tracking_id = request.get('tracking_id')
            engineer_name = request.get('engineer_name')
            success = accept_job(tracking_id, engineer_name)
            response_data = {"success": success}
            
        elif request_type == "ADD_SALES_RECORD":
            user_role = request.get('user_role')
            user_permissions = request.get('user_permissions', [])
            
            has_permission = False
            if user_role in ['admin', 'IT']:
                has_permission = True
            elif user_role == 'sales' and 'create_sales_record' in user_permissions:
                has_permission = True
            
            if not has_permission:
                response_data = {"success": False, "error": "Bạn không có quyền tạo tracking mới"}
            else:
                record_data = request.get('record', {})
                new_record = add_sales_record(record_data)
                if new_record:
                    response_data = {"success": True, "record": new_record}
                else:
                    response_data = {"success": False, "error": "Failed to add record"}
                    
        elif request_type == "GET_SALES_PROJECTS":
            user_id = request.get('user_id')
            projects = get_projects_by_user(user_id)
            response_data = projects
            
        elif request_type == "GET_ENGINEER_JOBS":
            engineer_name = request.get('engineer_name')
            projects = get_accepted_projects_by_engineer(engineer_name)
            response_data = projects
            
        elif request_type == "GET_ALL_NOTICES_FOR_ENGINEER":
            engineer_name = request.get('engineer_name')
            notices = get_all_notices_for_engineer(engineer_name)
            response_data = notices
            
        # ==================== Code Generation ====================
        elif request_type == "REQUEST_CODE":
            name = request.get('name', '').strip()
            category = request.get('category', '')
            employee = request.get('employee', '').strip()
            
            if not name or not category or not employee:
                response_data = "INVALID_REQUEST"
            else:
                code = generate_code(used_codes, category, employee)
                if code:
                    if category != "SJT":
                        if category not in used_codes:
                            used_codes[category] = set()
                        used_codes[category].add(code)
                    history.append({
                        'name': name,
                        'employee': employee,
                        'category': category,
                        'code': code,
                        'time': __import__('datetime').datetime.now().isoformat(),
                        'parent_code': ''
                    })
                    save_data_data(used_codes, history)
                    response_data = code
                else:
                    response_data = "NO_MORE_CODES"
                    
        elif request_type == "GET_HISTORY":
            global history_version, cached_sorted_history
            current_version = len(history)
            if cached_sorted_history is None or history_version != current_version:
                cached_sorted_history = sorted(history, key=lambda x: x.get('time', ''), reverse=True)
                history_version = current_version
            
            limit = request.get('limit', 100)
            offset = request.get('offset', 0)
            if 'page' in request:
                page = request['page']
                offset = (page - 1) * limit
            
            if limit is not None and limit > 0:
                limited_history = cached_sorted_history[offset:offset + limit]
                response_data = limited_history
            else:
                response_data = cached_sorted_history
                
        elif request_type == "DELETE_HISTORY":
            pwd = request.get('password')
            code = request.get('code')
            
            if pwd != "kelly" or not code:
                response_data = "ERROR"
            else:
                to_remove = None
                for item in history:
                    if item.get('code') == code:
                        to_remove = item
                        break
                
                if to_remove:
                    category = to_remove['category']
                    employee = to_remove.get('employee', '')
                    key = f"SJT_{employee}" if category == "SJT" else category
                    
                    if key in used_codes and code in used_codes.get(key, set()):
                        used_codes.get(key, set()).remove(code)
                        deleted_codes.add(code)
                        history.remove(to_remove)
                        save_data_data(used_codes, history)
                        response_data = "DELETED"
                    else:
                        response_data = "ERROR"
                else:
                    response_data = "ERROR"
                    
        elif request_type == "SEARCH_HISTORY":
            search_text = request.get('search_text', '').lower().strip()
            columns = request.get('columns', ['name', 'employee', 'category', 'code', 'time'])
            
            if cached_sorted_history is None:
                cached_sorted_history = sorted(history, key=lambda x: x.get('time', ''), reverse=True)
            
            if not search_text:
                results = cached_sorted_history
            else:
                results = []
                for item in cached_sorted_history:
                    for col in columns:
                        value = item.get(col, '')
                        if value and search_text in str(value).lower():
                            results.append(item)
                            break
            response_data = results
            
        # ==================== Authentication ====================
        elif request_type == "LOGIN":
            username = request.get('username', '').strip()
            password = request.get('password', '')
            
            user_info = get_user_with_permissions(username)
            if user_info:
                if user_info.get('status') == 'locked':
                    response_data = {"success": False, "error": "Tài khoản đã bị khóa"}
                elif user_info.get('passwords') != password:
                    response_data = {"success": False, "error": "Invalid credentials"}
                else:
                    user_info_clean = user_info.copy()
                    if 'passwords' in user_info_clean:
                        del user_info_clean['passwords']
                    response_data = {"success": True, "user_info": user_info_clean}
            else:
                response_data = {"success": False, "error": "Invalid credentials"}
                
        elif request_type == "PING":
            response_data = "PONG"
            
        else:
            response_data = {"success": False, "error": f"Unknown request type: {request_type}"}
        
        # Send response
        if response_data is None:
            response_str = json.dumps({"success": False, "error": "No response"})
        elif isinstance(response_data, str):
            response_str = response_data
        else:
            response_str = json.dumps(response_data)
        
        client_socket.send(response_str.encode('utf-8'))
        
    except Exception as e:
        safe_print(f"[TCP] Error handling client {client_address}: {e}")
        try:
            client_socket.send(json.dumps({"success": False, "error": str(e)}).encode('utf-8'))
        except:
            pass
    finally:
        client_socket.close()


def run_tcp_server(port):
    """Run TCP socket server on specified port for legacy V7 client"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen(5)
    safe_print(f"[TCP] Server listening on port {port}")
    
    while True:
        try:
            client_socket, client_address = server_socket.accept()
            safe_print(f"[TCP] Client connected from {client_address}")
            # Handle each client in a separate thread
            client_thread = threading.Thread(target=handle_tcp_client, args=(client_socket, client_address), daemon=True)
            client_thread.start()
        except Exception as e:
            safe_print(f"[TCP] Error accepting connection: {e}")
            break


# ========================================================================
# Run Server on Multiple Ports (8001 and 12345)
# ========================================================================

if __name__ == '__main__':
    import threading
    import time
    
    print("=" * 60)
    print("Unified Server - Running on Ports 8001 & 12345")
    print("=" * 60)
    print("Web UI: http://localhost:8001")
    print("Web UI (Legacy): http://localhost:12345")
    print("REST API: http://localhost:8001/api/projects")
    print("Login: http://localhost:8001/api/login")
    print("Tool Open: http://localhost:8001/api/tool-search")
    print("=" * 60)
    print("Server is listening on BOTH ports for backward compatibility")
    print("Port 12345: TCP Socket Server (for old client V7)")
    print("Port 8001: HTTP Server (for new client V8)")
    print("=" * 60)
    
    # Run Flask HTTP server on port 8001
    def run_http_server(port):
        """Run Flask server on specified port"""
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True, use_reloader=False)
    
    # Start HTTP server on port 8001
    http_thread = threading.Thread(target=run_http_server, args=(8001,), daemon=True)
    http_thread.start()
    time.sleep(0.5)
    
    # Start TCP socket server on port 12345 (for legacy V7 client)
    tcp_thread = threading.Thread(target=run_tcp_server, args=(12345,), daemon=True)
    tcp_thread.start()
    
    print("Servers started:")
    print("  - HTTP Server: http://localhost:8001")
    print("  - TCP Socket Server: localhost:12345")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
