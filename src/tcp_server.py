# -*- coding: utf-8 -*-
"""
TCP Server Module - Legacy V7 Client Support

Module này cung cấp TCP socket server để hỗ trợ legacy V7 client kết nối.
Server chạy trên port 12345 và xử lý các request types:
- GET_DB_ALL: Lấy tất cả dữ liệu database
- ADD_SALES_RECORD: Thêm record bán hàng mới
- UPDATE_SALES_RECORD: Cập nhật record
- DELETE_SALES_RECORD: Xóa record
- SEARCH_SALES: Tìm kiếm dữ liệu
- GET_EMPLOYEES: Lấy danh sách nhân viên
- GET_CUSTOMERS: Lấy danh sách khách hàng

Author: System
Version: 1.0.0
"""

import socket
import threading
import json
import time

# ========================================================================
# TCP Server Configuration
# ========================================================================

TCP_PORT = 12345
TCP_HOST = '0.0.0.0'

# Server state
tcp_server_running = False
tcp_server_socket = None
tcp_server_thread = None

# Thread lock for safe_print
_print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    """Thread-safe print"""
    try:
        with _print_lock:
            print(*args, **kwargs)
    except (ValueError, OSError):
        pass

# ========================================================================
# TCP Client Handler
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
        
        # Get the global data references from server module
        # These will be set when start_tcp_server() is called
        global db_data, cached_sorted_history, history_version, used_codes, history
        global deleted_codes, db_helper, server_module
        
        response_data = None
        
        # ==================== DB Operations ====================
        if request_type == "GET_DB_ALL":
            db_data = db_helper.load_all()
            response_data = db_data
            
        elif request_type == "GET_DB_PROJECT":
            tracking_id = request.get('tracking_id')
            project = db_helper.get_record_by_id(tracking_id)
            response_data = project
            
        elif request_type == "GET_DB_PAGED":
            page = request.get('page', 1)
            limit = request.get('limit', 50)
            sort_by = request.get('sort_by', 'Tracking ID')
            sort_order = request.get('sort_order', 'desc')
            result = db_helper.get_paged_data_sql(page, limit, sort_by, sort_order)
            response_data = result
            
        elif request_type == "ADD_DB_RECORD":
            record = request.get('record', {})
            tracking_id = max([r.get("Tracking ID", 0) for r in db_data] + [0]) + 1
            record["Tracking ID"] = tracking_id
            db_data.append(record)
            db_helper.save_all(db_data)
            response_data = {"success": True, "record": record}
            
        elif request_type == "UPDATE_DB_RECORD":
            tracking_id = request.get('tracking_id')
            new_data = request.get('data', {})
            success = db_helper.update_record(tracking_id, new_data)
            response_data = {"success": success}
            
        elif request_type == "DELETE_DB_RECORDS":
            user_role = request.get('user_role')
            tracking_ids = request.get('tracking_ids', [])
            
            if user_role != 'admin':
                response_data = {"success": False, "error": "Bạn không có quyền xóa"}
            else:
                deleted_count = db_helper.delete_records(tracking_ids)
                response_data = {"success": True, "deleted_count": deleted_count}
                
        elif request_type == "SEARCH_DB_DATA":
            search_text = request.get('search_text', '')
            columns = request.get('columns', [])
            results = db_helper.search_data(db_data, search_text, columns)
            response_data = results
            
        elif request_type == "FILTER_DB_DATA":
            column_filters = request.get('filters', {})
            results = db_helper.filter_data(db_data, column_filters)
            response_data = results
            
        # ==================== User Operations ====================
        elif request_type == "DB_LOGIN":
            username = request.get('username', '').strip()
            password = request.get('password', '')
            
            user_info = db_helper.get_user_with_permissions(username)
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
            users = db_helper.get_all_users()
            response_data = users
            
        elif request_type == "ADD_USER":
            user_data = request.get('user_data', {})
            user_id = db_helper.add_user(user_data)
            if user_id:
                db_helper.assign_default_permissions(user_id, user_data.get('role', 'sales'))
                response_data = {"success": True, "user_id": user_id}
            else:
                response_data = {"success": False, "error": "Username already exists"}
                
        elif request_type == "UPDATE_USER":
            user_id = request.get('user_id')
            user_data = request.get('user_data', {})
            success = db_helper.update_user(user_id, user_data)
            if 'permissions' in user_data:
                db_helper.set_user_permissions(user_id, user_data['permissions'])
            response_data = {"success": success}
            
        elif request_type == "DELETE_USER":
            user_id = request.get('user_id')
            success = db_helper.delete_user(user_id)
            response_data = {"success": success}
            
        # ==================== Notice/Pending Operations ====================
        elif request_type == "GET_PENDING_NOTICES":
            user_id = request.get('user_id')
            notices = db_helper.get_pending_notices(user_id)
            response_data = notices
            
        elif request_type == "GET_PENDING_COUNT":
            user_id = request.get('user_id')
            count = db_helper.get_pending_count(user_id)
            response_data = {"count": count}
            
        elif request_type == "ACCEPT_JOB":
            tracking_id = request.get('tracking_id')
            engineer_name = request.get('engineer_name')
            success = db_helper.accept_job(tracking_id, engineer_name)
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
                new_record = db_helper.add_sales_record(record_data)
                if new_record:
                    response_data = {"success": True, "record": new_record}
                else:
                    response_data = {"success": False, "error": "Failed to add record"}
                    
        elif request_type == "GET_SALES_PROJECTS":
            user_id = request.get('user_id')
            projects = db_helper.get_projects_by_user(user_id)
            response_data = projects
            
        elif request_type == "GET_ENGINEER_JOBS":
            engineer_name = request.get('engineer_name')
            projects = db_helper.get_accepted_projects_by_engineer(engineer_name)
            response_data = projects
            
        elif request_type == "GET_ALL_NOTICES_FOR_ENGINEER":
            engineer_name = request.get('engineer_name')
            notices = db_helper.get_all_notices_for_engineer(engineer_name)
            response_data = notices
            
        # ==================== Code Generation ====================
        elif request_type == "REQUEST_CODE":
            name = request.get('name', '').strip()
            category = request.get('category', '')
            employee = request.get('employee', '').strip()
            
            if not name or not category or not employee:
                response_data = "INVALID_REQUEST"
            else:
                code = server_module.get('generate_code')(used_codes, category, employee)
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
                    server_module.get('save_data_data')(used_codes, history)
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
                        server_module.get('save_data_data')(used_codes, history)
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
            
            user_info = db_helper.get_user_with_permissions(username)
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


# ========================================================================
# TCP Server Core Functions
# ========================================================================

def _run_tcp_server(port):
    """Run TCP socket server on specified port for legacy V7 client (internal)"""
    global tcp_server_running, tcp_server_socket
    
    tcp_server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    tcp_server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        tcp_server_socket.bind((TCP_HOST, port))
        tcp_server_socket.listen(5)
        tcp_server_running = True
        safe_print(f"[TCP] Server listening on {TCP_HOST}:{port}")
        
        while tcp_server_running:
            try:
                client_socket, client_address = tcp_server_socket.accept()
                safe_print(f"[TCP] Client connected from {client_address}")
                # Handle each client in a separate thread
                client_thread = threading.Thread(
                    target=handle_tcp_client, 
                    args=(client_socket, client_address), 
                    daemon=True
                )
                client_thread.start()
            except Exception as e:
                if tcp_server_running:
                    safe_print(f"[TCP] Error accepting connection: {e}")
                break
    except Exception as e:
        safe_print(f"[TCP] Server error: {e}")
    finally:
        tcp_server_running = False
        if tcp_server_socket:
            try:
                tcp_server_socket.close()
            except:
                pass
        safe_print(f"[TCP] Server stopped on port {port}")


# ========================================================================
# Public API Functions
# ========================================================================

# Global references to server's data
db_helper = None
server_module = None
db_data = []
cached_sorted_history = None
history_version = 0
used_codes = {}
history = []
deleted_codes = set()


def initialize(db_helper_module, server_data_refs):
    """
    Initialize TCP server with references to server's modules and data.
    
    Args:
        db_helper_module: The db_helper module reference
        server_data_refs: Dictionary containing references to server data:
            - 'db_data': Global db_data list
            - 'cached_sorted_history': Global cached_sorted_history
            - 'history_version': Global history_version
            - 'used_codes': Global used_codes dict
            - 'history': Global history list
            - 'deleted_codes': Global deleted_codes set
            - 'generate_code': generate_code function
            - 'save_data_data': save_data_data function
    """
    global db_helper, server_module
    global db_data, cached_sorted_history, history_version
    global used_codes, history, deleted_codes
    
    db_helper = db_helper_module
    server_module = server_data_refs
    
    # Set global data references
    db_data = server_data_refs.get('db_data', [])
    cached_sorted_history = server_data_refs.get('cached_sorted_history')
    history_version = server_data_refs.get('history_version', 0)
    used_codes = server_data_refs.get('used_codes', {})
    history = server_data_refs.get('history', [])
    deleted_codes = server_data_refs.get('deleted_codes', set())
    
    safe_print("[TCP] Server module initialized")


def start_tcp_server(port=None):
    """
    Start TCP server on specified port.
    
    Args:
        port: Port number (default: TCP_PORT = 12345)
    
    Returns:
        threading.Thread: The server thread
    """
    global tcp_server_running, tcp_server_thread
    
    if tcp_server_running:
        safe_print(f"[TCP] Server is already running on port {port or TCP_PORT}")
        return tcp_server_thread
    
    target_port = port or TCP_PORT
    safe_print(f"[TCP] Starting server on port {target_port}...")
    
    tcp_server_thread = threading.Thread(
        target=_run_tcp_server,
        args=(target_port,),
        daemon=True
    )
    tcp_server_thread.start()
    
    safe_print(f"[TCP] Server thread started")
    return tcp_server_thread


def stop_tcp_server():
    """
    Stop TCP server gracefully.
    """
    global tcp_server_running, tcp_server_socket
    
    if not tcp_server_running:
        safe_print("[TCP] Server is not running")
        return
    
    safe_print("[TCP] Stopping server...")
    tcp_server_running = False
    
    # Close the server socket to break the accept() loop
    if tcp_server_socket:
        try:
            tcp_server_socket.close()
        except:
            pass
    
    safe_print("[TCP] Server stop requested")


def get_status():
    """
    Get TCP server status.
    
    Returns:
        dict: Status information including:
            - running: Boolean indicating if server is running
            - port: Port number
            - thread: Thread object or None
    """
    return {
        'running': tcp_server_running,
        'port': TCP_PORT,
        'host': TCP_HOST,
        'thread': tcp_server_thread
    }


def update_data_references(data_refs):
    """
    Update the global data references.
    Call this when server's data changes.
    
    Args:
        data_refs: Dictionary with updated data references
    """
    global db_data, cached_sorted_history, history_version
    global used_codes, history, deleted_codes
    
    if 'db_data' in data_refs:
        db_data = data_refs['db_data']
    if 'cached_sorted_history' in data_refs:
        cached_sorted_history = data_refs['cached_sorted_history']
    if 'history_version' in data_refs:
        history_version = data_refs['history_version']
    if 'used_codes' in data_refs:
        used_codes = data_refs['used_codes']
    if 'history' in data_refs:
        history = data_refs['history']
    if 'deleted_codes' in data_refs:
        deleted_codes = data_refs['deleted_codes']


# ========================================================================
# Module Info
# ========================================================================

__all__ = [
    'TCP_PORT',
    'TCP_HOST',
    'tcp_server_running',
    'handle_tcp_client',
    'start_tcp_server',
    'stop_tcp_server',
    'get_status',
    'initialize',
    'update_data_references'
]