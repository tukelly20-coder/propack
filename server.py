# -*- coding: utf-8 -*-
"""
Unified Server - Tích hợp Web Server + Tool Open + Socket API trên port 8001
- Static files: Web UI (từ web/)
- /api/*: Tool Open API
- /api/socket: Socket API (thay thế TCP socket)

CLEANED VERSION - Routes đã được tách vào các module riêng
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

# ========================================================================
# Flask App Setup
# ========================================================================
from flask import Flask, request, jsonify, send_from_directory, make_response, session
from flask_cors import CORS
import tempfile

app = Flask(__name__, 
            template_folder='web/templates',
            static_folder='web/static')

# Flask Session Configuration (must be after app is defined)
# FIX #1: Add error handling + environment variable fallback for secret_key
import json as _json
import os as _os
try:
    with open('credentials.json', 'r', encoding='utf-8') as _f:
        _creds = _json.load(_f)
except FileNotFoundError:
    _creds = {}
except _json.JSONDecodeError as e:
    raise ValueError(f"credentials.json is not valid JSON: {e}")

# Support environment variable fallback for secret_key ( Issue #4 )
_secret_key = _os.environ.get('FLASK_SECRET_KEY') or _creds.get('secret_key')
if not _secret_key:
    # Check if running in production mode
    if _os.environ.get('FLASK_ENV') == 'production' or _os.environ.get('PRODUCTION') == 'true':
        raise ValueError("[FATAL] secret_key is required in production mode. Set FLASK_SECRET_KEY env variable or add 'secret_key' to credentials.json")
    print("[WARNING] secret_key not found in credentials.json or FLASK_SECRET_KEY env")
    print("[WARNING] Using auto-generated temporary key (sessions will not persist across restart)")
    # Use auto-generated key as fallback (not recommended for production)
    import secrets
    app.secret_key = f"temp-{secrets.token_hex(16)}"
else:
    app.secret_key = _secret_key
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
# Import chat modules
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

# Import Chat modules for AI long-term memory
from src import chat_db
from src.chat_service import get_context_for_ai, init_user_ai_session, get_system_state, search_for_ai_context, detect_search_intent
from src.chat_routes import register_chat_routes

# Import AI Agent modules (for proactive AI)
from src.intent_detector import detect_intent
from src.agent_planner import AgentPlanner
from src.agent_triggers import get_trigger_manager
from src.agent_tools import get_extended_tool_definitions

# Initialize chat database on startup
def init_chat():
    """Initialize all chat modules"""
    try:
        chat_db.init_chat_db()
        register_chat_routes(app)
        print("[Chat] Chat modules initialized successfully")
    except Exception as e:
        print(f"[Chat] Error initializing chat modules: {e}")

# Run initialization
init_chat()

# Import Auth routes (extracted from this file)
from routes.auth_routes import register_auth_routes

# Import AI routes (extracted from this file)
from src.ai.gemini_routes import register_routes as register_gemini_routes
from src.ai.ollama_routes import register_routes as register_ollama_routes
from src.ai.openrouter_routes import register_routes as register_openrouter_routes
from src.ai.agent_routes import register_routes as register_agent_routes

# Import route modules (extracted from this file)
from routes.project_routes import register_routes as register_project_routes
from routes.code_routes import register_routes as register_code_routes
from routes.notice_routes import register_routes as register_notice_routes
from routes.customer_routes import register_routes as register_customer_routes
from routes.log_routes import register_routes as register_log_routes

# ========================================================================
# Tool Open Module
# ========================================================================
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

# Import Excel helper module
from src.excel_helper import (
    EXCEL_PATH,
    CACHED_EXCEL_DATA,
    excel_cache_lock,
    get_excel_data,
    find_cinvcode_from_excel,
    find_parent_codes_batch,
    register_routes as register_excel_routes,
    check_excel_connection,
    get_cache_status
)

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

# Register Excel helper routes
register_excel_routes(app)

# Initialize database
init_db()
migrate_to_v2()
ensure_default_users()

# ========================================================================
# Session Management (Persistent across server restarts)
# Imported from src.session_manager
# ========================================================================
from src.session_manager import (
    sessions,
    sessions_lock,
    SESSION_TIMEOUT as _SERVER_SESSION_TIMEOUT,
    SESSION_FILE,
    load_sessions_from_file,
    save_sessions_to_file,
    schedule_save_sessions,
    cleanup_sessions,
    generate_token,
    check_rate_limit,
    record_login_attempt
)

# Register auth routes blueprint (extracted from this file)
# This must be called AFTER sessions are imported from session_manager
register_auth_routes(
    app, 
    sessions,  # Session storage dictionary
    sessions_lock,  # Threading lock for sessions
    schedule_save_sessions,  # Debounced save function
    check_rate_limit,  # Rate limiting function
    record_login_attempt  # Login attempt recording function
)

# Register project routes (extracted from this file - lines 569-669)
# Provide db_functions needed by project routes
project_db_functions = {
    'get_paged_data_sql': get_paged_data_sql,
    'add_record': add_record,
    'get_record_by_id': get_record_by_id,
    'update_record': update_record,
    'delete_records': delete_records
}
register_project_routes(app, project_db_functions)

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

# Register code routes (extracted from this file - lines 672-782)
# Provide code state and helper functions
code_state = {
    'used_codes': used_codes,
    'history': history,
    'deleted_codes': deleted_codes,
    'cached_sorted_history_ref': [cached_sorted_history],
    'history_version_ref': [history_version]
}
code_helpers = {
    'generate_code': generate_code,
    'save_data_data': save_data_data
}
register_code_routes(app, code_state, code_helpers)

# Register log routes (extracted from this file - lines 785-855)
# Provide session state for authenticated logging
session_state = {
    'sessions': sessions,
    'sessions_lock': sessions_lock
}
register_log_routes(app, session_state)

# Register customer routes (extracted from this file - lines 864-900)
register_customer_routes(app)

# Register notice routes (extracted from this file - lines 907-1006)
# Provide db_functions for notice operations
notice_db_functions = {
    'get_pending_notices': get_pending_notices,
    'get_pending_count': get_pending_count,
    'get_all_notices_for_engineer': get_all_notices_for_engineer,
    'accept_job': accept_job
}
register_notice_routes(app, notice_db_functions)

# Register AI routes
# Provide sessions_lock for AI routes that need to access user info

# Helper function to load credentials (used by AI routes)
def _load_credentials():
    """Load credentials from credentials.json file"""
    try:
        if os.path.exists('credentials.json'):
            with open('credentials.json', 'r', encoding='utf-8') as f:
                return json.load(f)
    except Exception:
        pass
    return {}

ai_state = {
    'sessions': sessions,
    'sessions_lock': sessions_lock,
    'load_credentials': _load_credentials,  # FIX: Pass credentials loader to AI routes
    'detect_intent': detect_intent,
    'AgentPlanner': AgentPlanner,
    'get_extended_tool_definitions': get_extended_tool_definitions,
    'get_context_for_ai': get_context_for_ai,
    'search_for_ai_context': search_for_ai_context,
    'detect_search_intent': detect_search_intent
}

# Register Gemini routes
register_gemini_routes(app, ai_state)

# Register Ollama routes
register_ollama_routes(app, ai_state)

# Register OpenRouter routes
register_openrouter_routes(app, ai_state)

# Register Agent routes
register_agent_routes(app, ai_state)

# Use server's SESSION_TIMEOUT (24 hours) instead of default 30 minutes
SESSION_TIMEOUT = 3600 * 24  # 24 hours

# Rate limiting for login (from session_manager)
LOGIN_RATE_LIMIT = 5
LOGIN_RATE_WINDOW = 300
login_attempts = {}
login_attempts_lock = threading.Lock()

# Flag to track if using temporary/auto-generated secret key
USING_TEMP_SECRET_KEY = not _secret_key

# Debug warning for session persistence
if USING_TEMP_SECRET_KEY:
    print("[CRITICAL] Using auto-generated temporary secret_key!")
    print("[CRITICAL] Sessions will NOT persist across server restart!")
    print("[CRITICAL] To fix: Add 'secret_key' to credentials.json or set FLASK_SECRET_KEY env variable")

# ========================================================================
# Code Generator Module
# ========================================================================
from src.code_generator import (
    CATEGORY_PREFIXES,
    generate_code as cg_generate_code,
    create_code,
    get_history,
    search_history,
    delete_history_record,
    validate_employee_code,
    register_routes as register_code_generator_routes
)

# ========================================================================
# Socket API - HTTP endpoints that replace TCP socket
# Imported from src.socket_api
# ========================================================================

from src.socket_api import register_routes as register_socket_routes

# Register socket routes with the Flask app
register_socket_routes(app, __import__('src.db_helper', fromlist=['*']), 
                       {'db_data': db_data, 'cached_sorted_history': cached_sorted_history, 
                        'history_version': history_version, 'used_codes': used_codes, 
                        'history': history, 'deleted_codes': deleted_codes},
                       {'generate_code': generate_code, 'save_data_data': save_data_data})

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

# Import TCP Server module for legacy V7 client
from src.tcp_server import (
    start_tcp_server,
    update_data_references
)

# ========================================================================
# Run Server on Multiple Ports (8001 and 12345)
# ========================================================================

if __name__ == '__main__':
    import threading
    import time
    from src.ai_memory import clean_expired_short_term
    
    # Initialize TCP server with references to server's data
    from src.db_helper import (
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
    
    # Create data reference dictionary for TCP server
    server_data_refs = {
        'db_data': db_data,
        'cached_sorted_history': cached_sorted_history,
        'history_version': history_version,
        'used_codes': used_codes,
        'history': history,
        'deleted_codes': deleted_codes,
        'generate_code': generate_code,
        'save_data_data': save_data_data
    }
    
    # Initialize TCP server with db_helper and data references
    from src import db_helper as db_helper_module
    from src.tcp_server import initialize
    initialize(db_helper_module, server_data_refs)
    start_tcp_server(12345)
    
    # Memory cleanup scheduler - runs every 5 minutes
    def run_memory_cleanup():
        """Background thread to clean expired short-term memories every 5 minutes"""
        while True:
            time.sleep(300)  # 5 minutes
            try:
                deleted = clean_expired_short_term()
                if deleted > 0:
                    print(f"[Memory Cleanup] Removed {deleted} expired short-term memories")
            except Exception as e:
                print(f"[Memory Cleanup] Error: {e}")
    
    # Start memory cleanup thread
    cleanup_thread = threading.Thread(target=run_memory_cleanup, daemon=True)
    cleanup_thread.start()
    print("[Memory Cleanup] Scheduler started (runs every 5 minutes)")
    
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
    
    print("Servers started:")
    print("  - HTTP Server: http://localhost:8001")
    print("  - TCP Socket Server: localhost:12345")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down servers...")
