# -*- coding: utf-8 -*-
"""
Socket API Module - HTTP endpoints that replace TCP socket

Module này chứa tất cả các HTTP endpoints xử lý request từ legacy V7 client
thông qua TCP socket. Các endpoint này thay thế cho TCP socket server
và cung cấp cùng chức năng qua HTTP/JSON.

Endpoints:
- POST /api/socket - Unified request handler cho tất cả các loại request

Request types được hỗ trợ:
- DB Operations: GET_DB_ALL, GET_DB_PROJECT, GET_DB_PAGED, ADD_DB_RECORD, 
                UPDATE_DB_RECORD, DELETE_DB_RECORDS, SEARCH_DB_DATA, FILTER_DB_DATA
- User Operations: DB_LOGIN, GET_USERS, ADD_USER, UPDATE_USER, DELETE_USER
- Notice/Pending: GET_PENDING_NOTICES, GET_PENDING_COUNT, ACCEPT_JOB
- Sales: ADD_SALES_RECORD, GET_SALES_PROJECTS, GET_ENGINEER_JOBS, GET_ALL_NOTICES_FOR_ENGINEER
- Code Generation: REQUEST_CODE, GET_HISTORY, DELETE_HISTORY, SEARCH_HISTORY
- Authentication: LOGIN, PING
"""

from flask import request, jsonify
import threading

# Import db_helper functions - sẽ được inject qua hàm init
_db_helpers = None

def init_socket_api(db_helpers, code_helpers, code_generator_helpers):
    """
    Initialize Socket API với các dependencies cần thiết.
    
    Args:
        db_helpers: Module chứa các hàm database (load_all, save_all, etc.)
        code_helpers: Module chứa các hàm xử lý mã (used_codes, history, etc.)
        code_generator_helpers: Module chứa hàm generate_code
    """
    global _db_helpers, _code_helpers, _code_generator_helpers
    _db_helpers = db_helpers
    _code_helpers = code_helpers
    _code_generator_helpers = code_generator_helpers


def get_db_helpers():
    """Get database helpers - backward compatibility"""
    global _db_helpers
    return _db_helpers


def get_code_helpers():
    """Get code helpers - backward compatibility"""
    global _code_helpers
    return _code_helpers


def get_code_generator():
    """Get code generator helper"""
    global _code_generator_helpers
    return _code_generator_helpers


# Thread-safe print function
_print_lock = threading.Lock()

def _safe_print(*args, **kwargs):
    """Thread-safe print"""
    try:
        with _print_lock:
            print(*args, **kwargs)
    except (ValueError, OSError):
        pass


def create_socket_api_handler(app, db_helpers_module, code_helpers_module, code_generator_module):
    """
    Tạo và đăng ký socket API handler với Flask app.
    
    Args:
        app: Flask application instance
        db_helpers_module: Module chứa các hàm database
        code_helpers_module: Module chứa các biến và hàm xử lý code (used_codes, history, etc.)
        code_generator_module: Module chứa hàm generate_code
    
    Returns:
        Function endpoint đã được đăng ký
    """
    
    # Khởi tạo modules
    init_socket_api(db_helpers_module, code_helpers_module, code_generator_module)
    
    @app.route('/api/socket', methods=['POST'])
    def socket_api():
        """HTTP endpoint thay thế cho TCP socket"""
        global _db_helpers, _code_helpers, _code_generator_helpers
        
        try:
            # Import globals từ code_helpers
            db_data = _code_helpers.get('db_data', [])
            cached_sorted_history = _code_helpers.get('cached_sorted_history')
            history_version = _code_helpers.get('history_version', 0)
            used_codes = _code_helpers.get('used_codes', {})
            history = _code_helpers.get('history', [])
            deleted_codes = _code_helpers.get('deleted_codes', set())
            
            req_data = request.get_json()
            if not req_data:
                return jsonify({"success": False, "error": "No data provided"}), 400
            
            request_type = req_data.get('request', 'unknown')
            _safe_print(f"[SocketAPI] Request: {request_type}")
            
            response_data = None
            
            # ==================== DB Operations ====================
            if request_type == "GET_DB_ALL":
                db_data = db_helpers_module.load_all()
                response_data = db_data
                
            elif request_type == "GET_DB_PROJECT":
                tracking_id = req_data.get('tracking_id')
                project = db_helpers_module.get_record_by_id(tracking_id)
                response_data = project
                
            elif request_type == "GET_DB_PAGED":
                page = req_data.get('page', 1)
                limit = req_data.get('limit', 50)
                sort_by = req_data.get('sort_by', 'Tracking ID')
                sort_order = req_data.get('sort_order', 'desc')
                result = db_helpers_module.get_paged_data_sql(page, limit, sort_by, sort_order)
                response_data = result
                
            elif request_type == "ADD_DB_RECORD":
                record = req_data.get('record', {})
                tracking_id = max([r.get("Tracking ID", 0) for r in db_data] + [0]) + 1
                record["Tracking ID"] = tracking_id
                db_data.append(record)
                db_helpers_module.save_all(db_data)
                response_data = {"success": True, "record": record}
                
            elif request_type == "UPDATE_DB_RECORD":
                tracking_id = req_data.get('tracking_id')
                new_data = req_data.get('data', {})
                success = db_helpers_module.update_record(tracking_id, new_data)
                response_data = {"success": success}
                
            elif request_type == "DELETE_DB_RECORDS":
                user_role = req_data.get('user_role')
                tracking_ids = req_data.get('tracking_ids', [])
                
                if user_role != 'admin':
                    response_data = {"success": False, "error": "Bạn không có quyền xóa"}
                else:
                    deleted_count = db_helpers_module.delete_records(tracking_ids)
                    response_data = {"success": True, "deleted_count": deleted_count}
                    
            elif request_type == "SEARCH_DB_DATA":
                search_text = req_data.get('search_text', '')
                columns = req_data.get('columns', [])
                results = db_helpers_module.search_data(db_data, search_text, columns)
                response_data = results
                
            elif request_type == "FILTER_DB_DATA":
                column_filters = req_data.get('filters', {})
                results = db_helpers_module.filter_data(db_data, column_filters)
                response_data = results
                
            # ==================== User Operations ====================
            elif request_type == "DB_LOGIN":
                username = req_data.get('username', '').strip()
                password = req_data.get('password', '')
                
                user_info = db_helpers_module.get_user_with_permissions(username)
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
                users = db_helpers_module.get_all_users()
                response_data = users
                
            elif request_type == "ADD_USER":
                user_data = req_data.get('user_data', {})
                user_id = db_helpers_module.add_user(user_data)
                if user_id:
                    db_helpers_module.assign_default_permissions(user_id, user_data.get('role', 'sales'))
                    response_data = {"success": True, "user_id": user_id}
                else:
                    response_data = {"success": False, "error": "Username already exists"}
                    
            elif request_type == "UPDATE_USER":
                user_id = req_data.get('user_id')
                user_data = req_data.get('user_data', {})
                success = db_helpers_module.update_user(user_id, user_data)
                if 'permissions' in user_data:
                    db_helpers_module.set_user_permissions(user_id, user_data['permissions'])
                response_data = {"success": success}
                
            elif request_type == "DELETE_USER":
                user_id = req_data.get('user_id')
                success = db_helpers_module.delete_user(user_id)
                response_data = {"success": success}
                
            # ==================== Notice/Pending Operations ====================
            elif request_type == "GET_PENDING_NOTICES":
                user_id = req_data.get('user_id')
                notices = db_helpers_module.get_pending_notices(user_id)
                response_data = notices
                
            elif request_type == "GET_PENDING_COUNT":
                user_id = req_data.get('user_id')
                count = db_helpers_module.get_pending_count(user_id)
                response_data = {"count": count}
                
            elif request_type == "ACCEPT_JOB":
                tracking_id = req_data.get('tracking_id')
                engineer_name = req_data.get('engineer_name')
                success = db_helpers_module.accept_job(tracking_id, engineer_name)
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
                    new_record = db_helpers_module.add_sales_record(record_data)
                    if new_record:
                        response_data = {"success": True, "record": new_record}
                    else:
                        response_data = {"success": False, "error": "Failed to add record"}
                        
            elif request_type == "GET_SALES_PROJECTS":
                user_id = req_data.get('user_id')
                projects = db_helpers_module.get_projects_by_user(user_id)
                response_data = projects
                
            elif request_type == "GET_ENGINEER_JOBS":
                engineer_name = req_data.get('engineer_name')
                projects = db_helpers_module.get_accepted_projects_by_engineer(engineer_name)
                response_data = projects
                
            elif request_type == "GET_ALL_NOTICES_FOR_ENGINEER":
                engineer_name = req_data.get('engineer_name')
                notices = db_helpers_module.get_all_notices_for_engineer(engineer_name)
                response_data = notices
                
            # ==================== Code Generation ====================
            elif request_type == "REQUEST_CODE":
                name = req_data.get('name', '').strip()
                category = req_data.get('category', '')
                employee = req_data.get('employee', '').strip()
                
                if not name or not category or not employee:
                    response_data = "INVALID_REQUEST"
                else:
                    # Get generate_code from code_generator module
                    generate_code_func = _code_generator_helpers.get('generate_code')
                    save_data_func = _code_generator_helpers.get('save_data_data')
                    
                    if generate_code_func and save_data_func:
                        code = generate_code_func(used_codes, category, employee)
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
                            save_data_func(used_codes, history)
                            response_data = code
                        else:
                            response_data = "NO_MORE_CODES"
                    else:
                        response_data = "GENERATOR_NOT_INITIALIZED"
                        
            elif request_type == "GET_HISTORY":
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
                            
                            # Save data
                            save_data_func = _code_generator_helpers.get('save_data_data')
                            if save_data_func:
                                save_data_func(used_codes, history)
                            response_data = "DELETED"
                        else:
                            response_data = "ERROR"
                    else:
                        response_data = "ERROR"
                        
            elif request_type == "SEARCH_HISTORY":
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
                
                user_info = db_helpers_module.get_user_with_permissions(username)
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
    
    return socket_api


def register_routes(app, db_helpers_module, code_helpers_module, code_generator_module):
    """
    Đăng ký tất cả socket API routes với Flask app.
    
    Đây là function chính để gọi từ server.py để đăng ký routes.
    
    Args:
        app: Flask application instance
        db_helpers_module: Module chứa các hàm database (db_helper)
        code_helpers_module: Module chứa các biến và hàm xử lý code (thường là server module)
        code_generator_module: Module chứa hàm generate_code (code_generator)
    """
    return create_socket_api_handler(
        app, 
        db_helpers_module, 
        code_helpers_module, 
        code_generator_module
    )


# Export functions for external use
__all__ = [
    'init_socket_api',
    'get_db_helpers', 
    'get_code_helpers', 
    'get_code_generator',
    'create_socket_api_handler',
    'register_routes'
]