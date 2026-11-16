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
import secrets
import time
import queue
import uuid
import logging
import shutil
import mimetypes
import re
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, send_file, make_response, session, Response, stream_with_context
from flask_cors import CORS

# ========================================================================
# Utility Functions
# ========================================================================
def configure_logging():
    """Configure consistent terminal logging for the unified server."""
    log_level = os.getenv('SERVER_LOG_LEVEL', 'INFO').upper()
    level = getattr(logging, log_level, logging.INFO)

    formatter = logging.Formatter(
        fmt='%(asctime)s | %(levelname)-7s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root_logger.addHandler(handler)
    root_logger.setLevel(level)

    # Hide verbose development request logs from Flask/Werkzeug.
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)


configure_logging()
LOGGER = logging.getLogger('unified_server')


def safe_print(*args, **kwargs):
    """Thread-safe print wrapper"""
    try:
        sep = kwargs.get('sep', ' ')
        msg = sep.join(str(a) for a in args)
        LOGGER.info(msg)
    except Exception:
        pass  # Silently ignore print errors

# ========================================================================
# Flask App Configuration
# ========================================================================

app = Flask(__name__,
            template_folder='web/templates',
            static_folder='web/static')

REQUEST_LOG_ENABLED = os.getenv('SERVER_LOG_REQUESTS', '1') == '1'
STATIC_LOG_ENABLED = os.getenv('SERVER_LOG_STATIC', '0') == '1'


@app.before_request
def start_request_timer():
    request._start_time = time.perf_counter()


@app.after_request
def log_http_request(response):
    if not REQUEST_LOG_ENABLED:
        return response

    path = request.path or ''
    if not STATIC_LOG_ENABLED and (
        path.startswith('/js/') or
        path.startswith('/css/') or
        path.startswith('/static/') or
        path == '/favicon.ico'
    ):
        return response

    duration_ms = (time.perf_counter() - getattr(request, '_start_time', time.perf_counter())) * 1000
    client_ip = request.headers.get('X-Forwarded-For', request.remote_addr or '-')
    safe_print(f"[HTTP] {client_ip} | {request.method} {path} | {response.status_code} | {duration_ms:.1f} ms")
    return response

# Flask Session Configuration
app.secret_key = 'propack-vp-secret-key-2024'
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
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
from src.scanner_integration import register_scanner_routes
from src.db_helper import (
    init_db, migrate_to_v2,
    load_all, save_all, add_record, update_record, delete_records, restore_records,
    search_data as db_search_data,
    filter_data as db_filter_data,
    get_paged_data_sql,
    get_cursor_paged_data_sql,
    get_record_by_id,
    add_user, get_user_by_username, get_all_users, update_user, delete_user,
    get_user_with_permissions, update_user_last_login, ensure_default_users,
    assign_default_permissions, set_user_permissions,
    get_pending_notices, get_pending_count, accept_job, add_sales_record,
    get_projects_by_user, get_accepted_projects_by_engineer,
    get_all_notices_for_engineer, get_all_customers,
    add_customer, update_customer, delete_customer, get_customer_by_id,
    get_parent_code_cache, get_parent_code_cache_many, save_parent_code_cache,
    ensure_realtime_schema, lock_project_cell, unlock_project_cell,
    get_active_project_locks, update_project_with_version, get_project_change_logs, get_project_change_log,
    revert_project_change_log, get_project_comments, add_project_comment, delete_project_comment,
    normalize_project_field_name, get_user_preference, set_user_preference
)

# Import Tool Open core
current_file_dir = os.path.dirname(os.path.abspath(__file__))
project_root_dir = os.path.dirname(current_file_dir) if os.path.basename(current_file_dir) == "server_modules" else current_file_dir
tool_open_dir = os.path.join(project_root_dir, "tools", "open")
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
        LOGGER.info("[Unified] Tool Open core loaded successfully")
except Exception as e:
    LOGGER.info(f"[Unified] Tool Open core load failed: {e}")

# ========================================================================
# Global state
# ========================================================================
db_data = []
cached_sorted_history = None
history_version = 0

# Realtime notice stream state (SSE)
notice_subscribers = {}
notice_subscribers_lock = threading.Lock()
notice_event_seq = 0

# Realtime project collaboration stream state (SSE)
project_subscribers = {}
project_subscribers_lock = threading.Lock()
project_event_seq = 0

# Token tạm để browser tải/xem file vật liệu qua server thay vì mở UNC trực tiếp.
material_file_tokens = {}
material_file_tokens_lock = threading.Lock()
MATERIAL_FILE_TOKEN_TTL = 15 * 60

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
                        safe_print(f"[Storage] Load success with encoding: {encoding}")
                        return used, history
                except Exception as e:
                    continue
        return {}, []
    except Exception as e:
        safe_print(f"[Storage] Load file error: {e}")
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
        safe_print(f"[Storage] Loi khi save file: {e}")

# Load initial data
used_codes, history = load_data()

# Excel configuration for parent code lookup
EXCEL_PATH = r"\\192.168.2.165\越南vp共享文件夹\09-工程图纸 Bản vẽ Kỹ Thuật Công Trình\存货档案库.xlsx"
SSHFS_EXCEL_PATH = os.getenv(
    'MATERIAL_EXCEL_SSHFS_PATH',
    r"Y:\越南vp共享文件夹\09-工程图纸 Bản vẽ Kỹ Thuật Công Trình\存货档案库.xlsx"
)
SSHFS_EXCEL_CACHE_PATH = os.getenv(
    'MATERIAL_EXCEL_SSHFS_CACHE_PATH',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'misc', 'fallback_excel', 'sshfs_inventory_cache.xlsx')
)
FALLBACK_EXCEL_URL = os.getenv(
    'MATERIAL_EXCEL_FALLBACK_URL',
    'https://gofile.me/7R631/ZDEPKMcgh'
)
FALLBACK_EXCEL_PATH = os.getenv(
    'MATERIAL_EXCEL_FALLBACK_PATH',
    os.path.join(os.path.dirname(os.path.abspath(__file__)), 'misc', 'fallback_excel', 'inventory_web_fallback.xlsx')
)

_EXCEL_COLUMN_ALIASES = {
    '工程图号': 'cEngineerFigNo',
    '存货编码': 'cInvCode',
}

def _normalize_excel_columns(df):
    df = df.copy()
    df.rename(columns={k: v for k, v in _EXCEL_COLUMN_ALIASES.items() if k in df.columns}, inplace=True)
    return df

# Cache for Excel data
CACHED_EXCEL_DATA = None
EXCEL_LOAD_SOURCE = None

def _format_parent_code_value(value):
    """Chuẩn hóa parent code đọc từ Excel."""
    if value is None:
        return None

    text = str(value).strip()
    if not text or text.lower() == 'nan':
        return None

    try:
        if '.' in text:
            return str(int(float(text)))
    except Exception:
        pass

    return text

def _download_fallback_excel():
    """Tải file Excel fallback từ web và lưu cục bộ nếu nội dung hợp lệ."""
    if not FALLBACK_EXCEL_URL:
        return None

    try:
        os.makedirs(os.path.dirname(FALLBACK_EXCEL_PATH), exist_ok=True)
        safe_print(f"[Excel] Downloading fallback Excel: {FALLBACK_EXCEL_URL}")

        content = None
        content_type = ''
        for attempt in range(1, 4):
            response = requests.get(FALLBACK_EXCEL_URL, allow_redirects=True, timeout=60)
            response.raise_for_status()
            content = response.content
            content_type = (response.headers.get('content-type') or '').lower()
            if content.startswith(b'PK'):
                break
            safe_print(f"[Excel] Fallback URL returned non-xlsx content on attempt {attempt} (content-type={content_type})")
            if attempt < 3:
                time.sleep(5)

        if not content or not content.startswith(b'PK'):
            safe_print(f"[Excel] Fallback URL did not return an .xlsx file (content-type={content_type})")
            return None

        tmp_path = FALLBACK_EXCEL_PATH + '.tmp'
        with open(tmp_path, 'wb') as f:
            f.write(content)
        os.replace(tmp_path, FALLBACK_EXCEL_PATH)

        safe_print(f"[Excel] Fallback Excel saved: {FALLBACK_EXCEL_PATH}")
        return FALLBACK_EXCEL_PATH
    except Exception as e:
        safe_print(f"[Excel] Error downloading fallback Excel: {e}")
        return None

def _sync_sshfs_excel_cache():
    """Copy SSHFS Excel to a local cache before pandas opens it."""
    source_path = SSHFS_EXCEL_PATH.replace('/', '\\')

    try:
        if os.path.exists(source_path):
            os.makedirs(os.path.dirname(SSHFS_EXCEL_CACHE_PATH), exist_ok=True)

            should_copy = not os.path.exists(SSHFS_EXCEL_CACHE_PATH)
            if not should_copy:
                source_stat = os.stat(source_path)
                cache_stat = os.stat(SSHFS_EXCEL_CACHE_PATH)
                should_copy = (
                    int(source_stat.st_mtime) > int(cache_stat.st_mtime)
                    or source_stat.st_size != cache_stat.st_size
                )

            if should_copy:
                safe_print(f"[Excel] Copying SSHFS Excel to local cache: {source_path}")
                tmp_path = SSHFS_EXCEL_CACHE_PATH + '.tmp'
                shutil.copy2(source_path, tmp_path)
                os.replace(tmp_path, SSHFS_EXCEL_CACHE_PATH)
                safe_print(f"[Excel] SSHFS Excel cache updated: {SSHFS_EXCEL_CACHE_PATH}")
            else:
                safe_print(f"[Excel] SSHFS Excel cache is up to date: {SSHFS_EXCEL_CACHE_PATH}")

            return SSHFS_EXCEL_CACHE_PATH

        if os.path.exists(SSHFS_EXCEL_CACHE_PATH):
            safe_print(f"[Excel] SSHFS source unavailable, using existing local cache: {SSHFS_EXCEL_CACHE_PATH}")
            return SSHFS_EXCEL_CACHE_PATH

        safe_print(f"[Excel] SSHFS Excel unavailable: {source_path}")
        return None
    except Exception as e:
        safe_print(f"[Excel] Error syncing SSHFS Excel cache: {e}")
        if os.path.exists(SSHFS_EXCEL_CACHE_PATH):
            safe_print(f"[Excel] Using existing SSHFS local cache after sync error: {SSHFS_EXCEL_CACHE_PATH}")
            return SSHFS_EXCEL_CACHE_PATH
        return None

def _get_excel_candidates():
    """Trả về danh sách nguồn Excel theo thứ tự ưu tiên."""
    candidates = []

    sshfs_cache_path = _sync_sshfs_excel_cache()
    if sshfs_cache_path:
        candidates.append(('sshfs-cache', sshfs_cache_path))

    excel_path = EXCEL_PATH.replace('/', '\\')
    if not excel_path.startswith('\\\\'):
        excel_path = '\\\\' + excel_path.lstrip('\\')
    candidates.append(('internal', excel_path))

    if os.path.exists(FALLBACK_EXCEL_PATH):
        candidates.append(('fallback-cache', FALLBACK_EXCEL_PATH))
    else:
        downloaded_path = _download_fallback_excel()
        if downloaded_path:
            candidates.append(('fallback-web', downloaded_path))

    return candidates

def get_excel_data():
    """Đọc dữ liệu Excel vào memory (chỉ tải 1 lần)."""
    global CACHED_EXCEL_DATA, EXCEL_LOAD_SOURCE
    
    if CACHED_EXCEL_DATA is not None:
        return CACHED_EXCEL_DATA
    
    try:
        import pandas as pd
    except Exception as e:
        safe_print(f"[Excel] pandas not available: {e}")
        return None

    for source, excel_path in _get_excel_candidates():
        try:
            if source == 'internal' and not os.path.exists(excel_path):
                safe_print(f"[Excel] Internal Excel unavailable: {excel_path}")
                continue

            safe_print(f"[Excel] Loading Excel into memory ({source}): {excel_path}")

            xls = pd.ExcelFile(excel_path)
            data = []
            exact_index = {}
            for sheet_name in xls.sheet_names:
                df = pd.read_excel(excel_path, sheet_name=sheet_name)
                df = _normalize_excel_columns(df)
                if 'cEngineerFigNo' in df.columns and 'cInvCode' in df.columns:
                    df['cEngineerFigNo'] = df['cEngineerFigNo'].astype(str).str.upper().str.strip()
                    df['cInvCode'] = df['cInvCode'].astype(str).str.strip()
                    data.append((sheet_name, df))

                    for _, row in df[['cEngineerFigNo', 'cInvCode']].dropna().iterrows():
                        engineer_code = str(row['cEngineerFigNo']).strip()
                        parent_code = _format_parent_code_value(row['cInvCode'])
                        if engineer_code and engineer_code.lower() != 'nan' and parent_code and engineer_code not in exact_index:
                            exact_index[engineer_code] = parent_code

            if data:
                safe_print(f"[Excel] Loaded {len(data)} sheets with data from {source}")
                CACHED_EXCEL_DATA = {
                    'source': source,
                    'path': excel_path,
                    'sheets': data,
                    'exact_index': exact_index
                }
                EXCEL_LOAD_SOURCE = source
                return CACHED_EXCEL_DATA

            safe_print(f"[Excel] No valid sheets found in {source}: {excel_path}")
        except Exception as e:
            safe_print(f"[Excel] Error loading {source} Excel: {e}")

    return None

def _find_cinvcode_from_excel_source(engineer_fig_no: str):
    """Tìm cInvCode trong dữ liệu Excel đã tải."""
    excel_data = get_excel_data()
    if not excel_data:
        return None
    
    search_code = str(engineer_fig_no).upper().strip()
    exact_index = excel_data.get('exact_index', {})
    if search_code in exact_index:
        return exact_index[search_code]
    
    # Try partial match (startswith)
    for sheet_name, df in excel_data.get('sheets', []):
        try:
            mask = df['cEngineerFigNo'].str.startswith(search_code)
            if mask.any():
                matches = df.loc[mask, 'cInvCode']
                for m in matches:
                    parent_code = _format_parent_code_value(m)
                    if parent_code:
                        return parent_code
        except Exception as e:
            continue
    
    return None

def _normalize_parent_lookup_code_local(code: str) -> str:
    """Chuẩn hóa mã bản vẽ để tra parent_code trong used_codes history."""
    return str(code or '').upper().strip()

def _get_parent_codes_from_history(codes: list):
    """Lấy parent_code đã lưu trong used_codes.json/history."""
    normalized_to_original = {}
    for code in codes:
        lookup_code = _normalize_parent_lookup_code_local(code)
        if lookup_code:
            normalized_to_original[lookup_code] = code

    if not normalized_to_original:
        return {}

    results = {}
    for item in history:
        lookup_code = _normalize_parent_lookup_code_local(item.get('code', ''))
        if lookup_code in normalized_to_original:
            parent_code = str(item.get('parent_code') or '').strip()
            if parent_code:
                results[normalized_to_original[lookup_code]] = parent_code

    return results

def _save_parent_codes_to_history(parent_codes: dict):
    """Ghi parent_code tìm được vào used_codes.json để lần sau không cần check Excel."""
    if not parent_codes:
        return False

    normalized_parent_codes = {
        _normalize_parent_lookup_code_local(code): str(parent_code).strip()
        for code, parent_code in parent_codes.items()
        if _normalize_parent_lookup_code_local(code) and str(parent_code or '').strip()
    }
    if not normalized_parent_codes:
        return False

    changed = False
    for item in history:
        lookup_code = _normalize_parent_lookup_code_local(item.get('code', ''))
        parent_code = normalized_parent_codes.get(lookup_code)
        if parent_code and item.get('parent_code') != parent_code:
            item['parent_code'] = parent_code
            changed = True

    if changed:
        save_data_data(used_codes, history)
    return changed

def find_cinvcode_from_excel(engineer_fig_no: str):
    """Tìm cInvCode tương ứng với cEngineerFigNo, ưu tiên used_codes.json rồi cache."""
    search_code = str(engineer_fig_no or '').upper().strip()
    if not search_code:
        return None

    history_parent_codes = _get_parent_codes_from_history([search_code])
    if search_code in history_parent_codes:
        return history_parent_codes[search_code]

    cached_parent_code = get_parent_code_cache(search_code)
    if cached_parent_code:
        _save_parent_codes_to_history({search_code: cached_parent_code})
        return cached_parent_code

    parent_code = _find_cinvcode_from_excel_source(search_code)
    if parent_code:
        save_parent_code_cache(search_code, parent_code, EXCEL_LOAD_SOURCE or 'excel')
        _save_parent_codes_to_history({search_code: parent_code})
    return parent_code

def find_parent_codes_batch(codes: list):
    """Tìm parent codes cho nhiều mã cùng lúc.
    
    Args:
        codes: List of codes cần tìm parent
        
    Returns:
        Dict mapping {code: parent_code}
    """
    results = {}

    clean_codes = [str(code).strip() for code in codes if str(code).strip()]
    history_results = _get_parent_codes_from_history(clean_codes)
    results.update(history_results)

    missing_codes = [code for code in clean_codes if code not in history_results]
    if not missing_codes:
        return results

    cached_results = get_parent_code_cache_many(missing_codes)
    results.update(cached_results)
    _save_parent_codes_to_history(cached_results)

    missing_codes = [code for code in missing_codes if code not in cached_results]
    if not missing_codes:
        return results
    
    # Pre-load Excel only when DB cache does not already have every code.
    if not get_excel_data():
        return results

    for code in missing_codes:
        parent_code = _find_cinvcode_from_excel_source(code)
        if parent_code:
            results[code] = parent_code
            save_parent_code_cache(code, parent_code, EXCEL_LOAD_SOURCE or 'excel')

    excel_results = {code: results[code] for code in missing_codes if code in results}
    _save_parent_codes_to_history(excel_results)
    
    return results

# Initialize database
init_db()
migrate_to_v2()
ensure_realtime_schema()
ensure_default_users()

# ========================================================================
# Session Management
# ========================================================================
import secrets
import time

sessions_lock = threading.Lock()
SESSION_TIMEOUT = None  # None = web login sessions never expire automatically
SESSION_STORAGE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'web_sessions.json')


def _sanitize_session_user(user_info):
    """Return a copy of user data that is safe to keep in session storage."""
    user = (user_info or {}).copy()
    user.pop('passwords', None)
    user.pop('password', None)
    return user


def _prune_expired_sessions_unlocked():
    now = time.time()
    expired_tokens = [
        token
        for token, session_data in sessions.items()
        if SESSION_TIMEOUT is not None
        and now - float(session_data.get('created_at', 0) or 0) > SESSION_TIMEOUT
    ]
    for token in expired_tokens:
        sessions.pop(token, None)
    return bool(expired_tokens)


def _save_sessions_unlocked():
    try:
        _prune_expired_sessions_unlocked()
        tmp_path = SESSION_STORAGE_PATH + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(sessions, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, SESSION_STORAGE_PATH)
    except Exception as e:
        safe_print(f"[Session] Failed to save sessions: {e}")


def _load_sessions():
    try:
        if not os.path.exists(SESSION_STORAGE_PATH):
            return {}
        with open(SESSION_STORAGE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}

        now = time.time()
        loaded_sessions = {}
        for token, session_data in data.items():
            if not isinstance(token, str) or not isinstance(session_data, dict):
                continue
            try:
                created_at = float(session_data.get('created_at', 0) or 0)
            except (TypeError, ValueError):
                continue
            if SESSION_TIMEOUT is not None and now - created_at > SESSION_TIMEOUT:
                continue
            user = _sanitize_session_user(session_data.get('user', {}))
            if not user:
                continue
            loaded_sessions[token] = {
                'user': user,
                'created_at': created_at,
                'ip': session_data.get('ip', '')
            }
        return loaded_sessions
    except Exception as e:
        safe_print(f"[Session] Failed to load sessions: {e}")
        return {}


sessions = _load_sessions()
if sessions:
    safe_print(f"[Session] Loaded {len(sessions)} persisted web session(s)")

# Rate limiting for login
LOGIN_RATE_LIMIT = 5
LOGIN_RATE_WINDOW = 300
login_attempts = {}
login_attempts_lock = threading.Lock()

def generate_token():
    """Tạo token ngẫu nhiên"""
    return secrets.token_hex(32)


def create_web_session(token, user_info, client_ip):
    login_time = datetime.now().isoformat()
    if user_info and user_info.get('user_id'):
        update_user_last_login(user_info.get('user_id'), login_time)
        user_info['last_login'] = login_time
    with sessions_lock:
        sessions[token] = {
            'user': _sanitize_session_user(user_info),
            'created_at': time.time(),
            'ip': client_ip
        }
        _save_sessions_unlocked()


def get_web_session(token):
    with sessions_lock:
        session_data = sessions.get(token)
        if not session_data:
            return None, "invalid_token"

        created_at = float(session_data.get('created_at', 0) or 0)
        if SESSION_TIMEOUT is not None and (time.time() - created_at) > SESSION_TIMEOUT:
            sessions.pop(token, None)
            _save_sessions_unlocked()
            return None, "expired"

        return session_data, None


def remove_web_session(token):
    with sessions_lock:
        if token in sessions:
            sessions.pop(token, None)
            _save_sessions_unlocked()

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

def get_user_from_bearer_token():
    """Lấy user từ Authorization Bearer token."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return None, "no_token"

    token = auth_header[7:]
    session_data, error = get_web_session(token)
    if error:
        return None, error

    return session_data.get('user', {}), None

def is_admin_user(user):
    """Kiểm tra user có quyền admin không."""
    if not user:
        return False
    role = str(user.get('role', '')).strip().lower()
    username = str(user.get('username', '')).strip().lower()
    return role == 'admin' or username == 'administrator'


def normalize_project_role(role_value):
    role = str(role_value or '').strip().lower()
    aliases = {
        'it': 'admin',
        'administrator': 'admin',
        'eng': 'engineer',
        'ky thuat': 'engineer',
        'kỹ thuật': 'engineer',
        'san xuat': 'production',
        'sản xuất': 'production',
        'ke hoach': 'planner',
        'kế hoạch': 'planner'
    }
    return aliases.get(role, role)


def get_project_user_from_request():
    """Trả user nếu có bearer token; None nghĩa là request legacy chưa xác thực."""
    user, error = get_user_from_bearer_token()
    if error == "no_token":
        return None
    return user or {}


def get_project_update_fields(payload):
    fields = []
    for key in (payload or {}).keys():
        if key in {'version', 'expected_version', 'changed_by', 'changed_by_name'}:
            continue
        field_name = normalize_project_field_name(key)
        if field_name:
            fields.append(field_name)
    return fields


PROJECT_COLUMN_EDIT_LOCKS_USER_ID = '__global__'
PROJECT_COLUMN_EDIT_LOCKS_KEY = 'projects_column_edit_locks'
PROJECT_COLUMN_LOCK_FIELD_MAP = {
    'tracking_id': 'tracking_id',
    'ngay': 'Created_Date',
    'khachhang': 'khach_hang',
    'nhanvienkd': 'nhan_vien_kinh_doanh',
    'tensanpham': 'ten_san_pham',
    'quycach': 'quy_cach',
    'yeucaukythuat': 'khach_hang_yeu_cau_ky_thuat',
    'lienhe': 'nguoi_lien_he_kh',
    'soluong': 'so_luong',
    'mapo': 'ma_po',
    'dokhan': 'urgency_level',
    'tg_mongmuon': 'thoi_gian_mong_muon_ban_ve',
    'trangthai': 'is_pending',
    'nguoinhan': 'accepted_by',
    'tg_tiepnhan': 'accepted_at',
    'mabave': 'ma_ban_ve',
    'mabavkythuat': 'ma_ban_ve_ky_thuat',
    'mame': 'ma_me',
    'loaisanpham': 'loai_san_pham',
    'nhanvienthietke': 'nhan_vien_thiet_ke',
    'tinhtrang': 'tinh_trang_hoan_thanh',
    'tg_hoanthanh': 'thoi_gian_hoan_thanh_ke_hoach',
}
PROJECT_COLUMN_LOCK_EDITABLE_KEYS = set(PROJECT_COLUMN_LOCK_FIELD_MAP.keys()) - {'tracking_id'}


def normalize_project_column_edit_locks(value):
    if isinstance(value, dict):
        raw_items = value.get('locked_columns', [])
    else:
        raw_items = value
    if not isinstance(raw_items, list):
        return []
    locked = []
    for item in raw_items:
        key = str(item or '').strip()
        if key in PROJECT_COLUMN_LOCK_EDITABLE_KEYS and key not in locked:
            locked.append(key)
    return locked


def get_project_column_edit_locks():
    return normalize_project_column_edit_locks(
        get_user_preference(PROJECT_COLUMN_EDIT_LOCKS_USER_ID, PROJECT_COLUMN_EDIT_LOCKS_KEY)
    )


def set_project_column_edit_locks(locked_columns):
    return set_user_preference(
        PROJECT_COLUMN_EDIT_LOCKS_USER_ID,
        PROJECT_COLUMN_EDIT_LOCKS_KEY,
        normalize_project_column_edit_locks(locked_columns)
    )


def get_locked_project_update_fields():
    locked_fields = set()
    for column_key in get_project_column_edit_locks():
        field_name = normalize_project_field_name(PROJECT_COLUMN_LOCK_FIELD_MAP.get(column_key))
        if field_name:
            locked_fields.add(field_name)
    return locked_fields


def can_user_update_project(user, payload):
    """Policy Projects theo plan: admin/planner full, production chỉ cập nhật trạng thái sản xuất, viewer chỉ xem."""
    requested_fields = set(get_project_update_fields(payload))
    locked_fields = get_locked_project_update_fields()
    blocked_fields = requested_fields & locked_fields
    if blocked_fields:
        return False, "Cột này đã bị admin khóa chỉnh sửa."

    if user is None:
        return True, None

    role = normalize_project_role(user.get('role'))
    username = str(user.get('username', '')).strip().lower()
    if role == 'admin' or username == 'administrator':
        return True, None
    if role in {'planner', 'sales', 'engineer'}:
        return True, None
    if role == 'production':
        allowed_fields = {'tinh_trang_hoan_thanh'}
        requested = requested_fields
        if requested and requested.issubset(allowed_fields):
            return True, None
        return False, "Production chỉ được cập nhật trạng thái sản xuất."
    if role == 'viewer':
        return False, "Viewer chỉ có quyền xem dữ liệu."
    return False, "Bạn không có quyền chỉnh sửa dự án."


def can_user_create_project(user):
    return True, None


def can_user_delete_project(user, fallback_role=''):
    if user is None:
        return normalize_project_role(fallback_role) == 'admin'
    return is_admin_user(user)


def normalize_notice_role(role_value):
    """Chuẩn hóa role để lọc đúng subscriber nhận realtime notice."""
    role = str(role_value or '').strip().lower()
    if role == 'eng':
        return 'engineer'
    return role


def build_notice_record_payload(record, fallback_tracking_id=None):
    """Build payload thống nhất cho notice realtime."""
    record = record or {}
    tracking_id = record.get('Tracking ID') or record.get('tracking_id') or fallback_tracking_id
    return {
        "tracking_id": tracking_id,
        "customer": record.get('Khách hàng') or record.get('khach_hang') or '',
        "product": record.get('Tên sản phẩm') or record.get('ten_san_pham') or '',
        "salesperson": record.get('Nhân viên KD') or record.get('Nhân viên kinh doanh') or record.get('nhan_vien_kinh_doanh') or '',
        "engineer": record.get('Người nhận') or record.get('accepted_by') or record.get('Nhân viên thiết kế') or record.get('nhan_vien_thiet_ke') or '',
        "urgency_level": record.get('Độ khẩn') or record.get('Tính cấp bách') or record.get('urgency_level') or 'normal',
        "is_pending": record.get('is_pending') or record.get('Trạng thái chờ') or 'yes',
        "created_date": record.get('Ngày') or record.get('Created_Date') or '',
    }


def publish_notice_event(event_type, message='', target_roles=None, record=None, tracking_id=None, extra=None):
    """Phát event realtime cho tất cả client đang subscribe tab notices."""
    global notice_event_seq

    normalized_targets = sorted({
        normalize_notice_role(role) for role in (target_roles or []) if str(role).strip()
    })

    with notice_subscribers_lock:
        notice_event_seq += 1
        event_id = notice_event_seq
        subscribers_snapshot = list(notice_subscribers.items())

    payload = {
        "event_id": event_id,
        "type": event_type,
        "message": message or '',
        "tracking_id": tracking_id or (record or {}).get('Tracking ID') or (record or {}).get('tracking_id'),
        "targets": normalized_targets,
        "timestamp": int(time.time())
    }

    if record:
        payload["record"] = build_notice_record_payload(record, fallback_tracking_id=payload["tracking_id"])
    if extra and isinstance(extra, dict):
        payload.update(extra)

    stale_subscribers = []
    for client_id, client in subscribers_snapshot:
        subscriber_role = normalize_notice_role(client.get('role'))
        if normalized_targets and subscriber_role not in normalized_targets:
            continue
        try:
            client['queue'].put_nowait(payload)
        except Exception:
            stale_subscribers.append(client_id)

    if stale_subscribers:
        with notice_subscribers_lock:
            for client_id in stale_subscribers:
                notice_subscribers.pop(client_id, None)


def format_sse(event_name, payload):
    """Serialize SSE event."""
    return f"event: {event_name}\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"


def publish_project_event(event_type, message='', tracking_id=None, field_name=None, record=None, lock=None, extra=None):
    """Phát event realtime cho các client đang mở bảng projects."""
    global project_event_seq

    with project_subscribers_lock:
        project_event_seq += 1
        event_id = project_event_seq
        subscribers_snapshot = list(project_subscribers.items())

    payload = {
        "event_id": event_id,
        "type": event_type,
        "message": message or '',
        "tracking_id": tracking_id,
        "field_name": field_name,
        "timestamp": int(time.time())
    }
    if record:
        payload["record"] = record
    if lock:
        payload["lock"] = lock
    if extra and isinstance(extra, dict):
        payload.update(extra)

    stale_subscribers = []
    for client_id, client in subscribers_snapshot:
        try:
            client['queue'].put_nowait(payload)
        except Exception:
            stale_subscribers.append(client_id)

    if stale_subscribers:
        with project_subscribers_lock:
            for client_id in stale_subscribers:
                project_subscribers.pop(client_id, None)


def get_project_online_users():
    """Danh sách user đang mở bảng projects, gộp trùng theo user_id/username."""
    with project_subscribers_lock:
        users = {}
        for client in project_subscribers.values():
            key = str(client.get('user_id') or client.get('username') or '').strip() or 'anonymous'
            user_name = client.get('user_name') or client.get('full_name') or client.get('username') or key
            users[key] = {
                "user_id": client.get('user_id') or key,
                "username": client.get('username') or key,
                "user_name": user_name,
                "full_name": user_name,
                "connected_at": client.get('connected_at')
            }
        return list(users.values())


def classify_material_file(path):
    """Phân loại file vật liệu để UI biết nên hiển thị/mở thế nào."""
    ext = os.path.splitext(str(path or ''))[1].lower()
    if ext == '.pdf':
        return 'pdf'
    if ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp'}:
        return 'drawing'
    if ext in {'.xls', '.xlsx', '.xlsm', '.csv'}:
        return 'bom'
    if ext in {'.dwg', '.dxf'}:
        return 'cad'
    return 'file'


def create_material_file_token(path, token_type='file'):
    """Tạo token tạm cho file/folder để không lộ UNC path trong URL browser."""
    token = secrets.token_urlsafe(24)
    with material_file_tokens_lock:
        now = time.time()
        expired = [
            item_token for item_token, item in material_file_tokens.items()
            if now - float(item.get('created_at', 0) or 0) > MATERIAL_FILE_TOKEN_TTL
        ]
        for item_token in expired:
            material_file_tokens.pop(item_token, None)
        material_file_tokens[token] = {
            "path": path,
            "type": token_type,
            "created_at": now
        }
    return token


def get_material_path_from_token(token, expected_type='file'):
    with material_file_tokens_lock:
        item = material_file_tokens.get(token)
        if not item:
            return None
        if time.time() - float(item.get('created_at', 0) or 0) > MATERIAL_FILE_TOKEN_TTL:
            material_file_tokens.pop(token, None)
            return None
        if expected_type and item.get('type', 'file') != expected_type:
            return None
        return item.get('path')


def get_material_file_path_from_token(token):
    return get_material_path_from_token(token, expected_type='file')


def sanitize_material_value(value):
    """Chuẩn hóa giá trị từ Excel để JSON không chứa NaN/NaT."""
    if value is None:
        return ''
    try:
        import pandas as pd
        if pd.isna(value):
            return ''
    except Exception:
        pass
    text = str(value).strip()
    return '' if text.lower() in {'nan', 'nat'} else text


def get_material_erp_info(code, resolved_code=None, matches=None):
    """Lấy metadata ERP/inventory từ file Excel cache nếu khả dụng."""
    info = {
        "available": False,
        "source": "",
        "code": code,
        "resolved_code": resolved_code or code,
        "rows": []
    }
    try:
        excel_data = get_excel_data()
        if not excel_data:
            info["message"] = "Chưa tải được dữ liệu ERP/Excel"
            return info

        info["source"] = excel_data.get('source', '')
        search_values = {
            str(code or '').upper().strip(),
            str(resolved_code or code or '').upper().strip()
        }
        for match in matches or []:
            search_values.add(str(match.get('cEngineerFigNo') or '').upper().strip())
            search_values.add(str(match.get('cInvCode') or '').upper().strip())
        search_values = {value for value in search_values if value}

        preferred_columns = [
            'cInvCode', 'cInvName', 'cInvStd', 'cEngineerFigNo', 'cInvCCode',
            'cComUnitName', 'cInvDefine1', 'cInvDefine2', 'cInvDefine3',
            'cInvDefine4', 'cInvDefine5', 'cInvDefine6', 'cInvDefine7',
            'cInvDefine8', 'cInvDefine9', 'cInvDefine10'
        ]
        rows = []
        seen = set()
        for sheet_name, df in excel_data.get('sheets', []):
            if not {'cInvCode', 'cEngineerFigNo'}.intersection(df.columns):
                continue
            mask = None
            for column in ('cInvCode', 'cEngineerFigNo'):
                if column not in df.columns:
                    continue
                column_mask = df[column].astype(str).str.upper().str.strip().isin(search_values)
                mask = column_mask if mask is None else (mask | column_mask)
            if mask is None or not mask.any():
                continue

            for _, row in df.loc[mask].head(20).iterrows():
                row_key = (
                    sheet_name,
                    sanitize_material_value(row.get('cEngineerFigNo')),
                    sanitize_material_value(row.get('cInvCode'))
                )
                if row_key in seen:
                    continue
                seen.add(row_key)
                values = {}
                for column in preferred_columns:
                    if column in df.columns:
                        cell_value = sanitize_material_value(row.get(column))
                        if cell_value:
                            values[column] = cell_value
                if values:
                    rows.append({"sheet": sheet_name, "values": values})

        info["rows"] = rows
        info["available"] = bool(rows)
        if not rows:
            info["message"] = "Không tìm thấy dòng ERP/Excel tương ứng"
        return info
    except Exception as e:
        info["message"] = str(e)
        return info


def build_material_documents_payload(code, urls, resolved_code=None, matches=None, include_erp=True):
    """Build payload tài liệu với URL xem/tải qua API server."""
    documents = []
    folders_map = {}
    for raw_path in urls or []:
        normalized_path = material_core.normalize_unc_path(raw_path) if TOOL_OPEN_AVAILABLE else str(raw_path)
        token = create_material_file_token(normalized_path)
        exists = os.path.exists(normalized_path)
        folder = os.path.dirname(normalized_path)
        filename = os.path.basename(normalized_path)
        doc_type = classify_material_file(normalized_path)
        documents.append({
            "name": filename,
            "type": doc_type,
            "exists": exists,
            "size": os.path.getsize(normalized_path) if exists and os.path.isfile(normalized_path) else 0,
            "folder_name": os.path.basename(folder),
            "view_url": f"/api/materials/file/{token}",
            "download_url": f"/api/materials/file/{token}?download=1"
        })
        if folder and folder not in folders_map:
            folder_token = create_material_file_token(folder, token_type='folder')
            folders_map[folder] = {
                "name": os.path.basename(folder),
                "exists": os.path.isdir(folder),
                "file_count": 0,
                "list_url": f"/api/materials/folder/{folder_token}",
                "open_url": f"/api/materials/folder/{folder_token}/open"
            }
        if folder:
            folders_map[folder]["file_count"] += 1

    folders = sorted(folders_map.values(), key=lambda item: item.get("name", ""))
    parent_open_url = ""
    folder_paths = list(folders_map.keys())
    if folder_paths:
        try:
            parent_path = os.path.commonpath(folder_paths) if len(folder_paths) > 1 else os.path.dirname(folder_paths[0])
            if parent_path and os.path.isdir(parent_path):
                parent_token = create_material_file_token(parent_path, token_type='folder')
                parent_open_url = f"/api/materials/folder/{parent_token}/open"
        except ValueError:
            parent_open_url = ""

    return {
        "success": bool(documents),
        "code": code,
        "resolved_code": resolved_code or code,
        "documents": documents,
        "folders": folders,
        "open_url": parent_open_url,
        "erp_info": get_material_erp_info(code, resolved_code=resolved_code, matches=matches) if include_erp else None,
        "matches": matches or [],
        "message": f"Tìm thấy {len(documents)} tài liệu" if documents else f"Không tìm thấy tài liệu cho mã: {code}"
    }

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
