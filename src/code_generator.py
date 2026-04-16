# -*- coding: utf-8 -*-
"""
Code Generator Module - Tạo và quản lý mã bản vẽ

Chức năng:
- Tạo mã bản vẽ theo danh mục (SJT, WLJ, ZZC, GZT, WCP, LSX, ZWJ, GZL, BSX, WLL, GTX, ZHT, LHX)
- Quản lý lịch sử tạo mã
- Xóa và khôi phục mã đã xóa
- Tìm kiếm trong lịch sử tạo mã
- Hỗ trợ batch generate

Author: Propack VP
"""

import json
import os
import threading
import datetime

# ========================================================================
# Global State
# ========================================================================

# Storage path for JSON data
STORAGE_PATH = 'used_codes.json'

# Cache for sorted history
cached_sorted_history = None
history_version = 0

# Global state variables (thread-safe access via lock)
deleted_codes = set()
used_codes = {}
history = []

# Thread lock for concurrent access
_code_lock = threading.Lock()

# CATEGORY_PREFIXES: Map category code to prefix
CATEGORY_PREFIXES = {
    "WLJ": "PWLJ", "ZZC": "PZZC", "GZT": "PGZT", "WCP": "PWCP",
    "LSX": "PLSX", "ZWJ": "PZWJ", "GZL": "PGZL", "SJT": "PSJT",
    "BSX": "PBSX", "WLL": "PWLL", "GTX": "PGTX", "ZHT": "PZHT", "LHX": "PLHX"
}

# ========================================================================
# Data Loading & Saving
# ========================================================================

def load_data():
    """
    Load data from JSON file.
    
    Returns:
        tuple: (used_codes_dict, history_list)
    """
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
    """
    Save data to JSON file.
    
    Args:
        used_codes_param: Dictionary of used codes
        history_param: List of history records
    """
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


def initialize():
    """
    Initialize the code generator module.
    Call this at server startup.
    
    Returns:
        tuple: (used_codes, history)
    """
    global used_codes, history
    used_codes, history = load_data()
    return used_codes, history


# ========================================================================
# Code Generation Logic
# ========================================================================

def generate_code(used_codes_param, category, employee=None):
    """
    Generate a new code for the given category.
    
    Args:
        used_codes_param: Dictionary to track used codes
        category: Category code (e.g., 'SJT', 'WLJ', etc.)
        employee: Employee code (required for 'SJT' category)
    
    Returns:
        str: Generated code or None if no more available
    
    Logic:
        - SJT: PSJT{employee}-{serial}-00-A0 (e.g., PSJT001-0001-00-A0)
        - Others: P{prefix}{number}-0000-00-A0 (e.g., PWLJ001-0000-00-A0)
    """
    global deleted_codes
    
    if category not in CATEGORY_PREFIXES:
        return None
    
    prefix = CATEGORY_PREFIXES[category]
    
    if category == "SJT":
        if not employee:
            return None
        key = f"SJT_{employee}"
        seri_used = used_codes_param.get(key, set())
        
        # First, try to reuse deleted codes for this employee
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
        
        # If no deleted codes available, generate new code
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


def add_to_history(name, employee, category, code, parent_code=''):
    """
    Add a new record to history.
    
    Args:
        name: Name
        employee: Employee code
        category: Category code
        code: Generated code
        parent_code: Parent code (optional)
    
    Returns:
        dict: The history record added
    """
    global history
    
    record = {
        'name': name,
        'employee': employee,
        'category': category,
        'code': code,
        'time': datetime.datetime.now().isoformat(),
        'parent_code': parent_code
    }
    history.append(record)
    return record


def delete_history_record(code):
    """
    Delete a history record and mark code as deleted.
    
    Args:
        code: The code to delete
    
    Returns:
        bool: True if deleted successfully, False otherwise
    """
    global used_codes, history, deleted_codes, cached_sorted_history, history_version
    
    with _code_lock:
        to_remove = None
        for item in history:
            if item.get('code') == code:
                to_remove = item
                break
        
        if not to_remove:
            return False
        
        category = to_remove['category']
        employee = to_remove.get('employee', '')
        key = f"SJT_{employee}" if category == "SJT" else category
        
        if key in used_codes and code in used_codes.get(key, set()):
            used_codes.get(key, set()).remove(code)
            deleted_codes.add(code)
        
        history.remove(to_remove)
        
        # Invalidate cache
        cached_sorted_history = None
        history_version = len(history)
        
        save_data_data(used_codes, history)
        return True


def search_history(search_text, columns=None):
    """
    Search in history records.
    
    Args:
        search_text: Text to search for
        columns: List of columns to search in (default: all)
    
    Returns:
        list: Matching history records
    """
    global cached_sorted_history, history
    
    if columns is None:
        columns = ['name', 'employee', 'category', 'code', 'time']
    
    if cached_sorted_history is None:
        cached_sorted_history = sorted(history, key=lambda x: x.get('time', ''), reverse=True)
    
    search_text = search_text.lower().strip()
    
    if not search_text:
        return cached_sorted_history
    
    results = []
    for item in cached_sorted_history:
        for col in columns:
            value = item.get(col, '')
            if value and search_text in str(value).lower():
                results.append(item)
                break
    
    return results


def get_history(page=1, limit=100):
    """
    Get paginated history records.
    
    Args:
        page: Page number (1-indexed)
        limit: Number of records per page
    
    Returns:
        dict: {
            'data': list of records,
            'total': total count,
            'total_pages': total pages,
            'page': current page
        }
    """
    global cached_sorted_history, history, history_version
    
    current_version = len(history)
    if cached_sorted_history is None or history_version != current_version:
        cached_sorted_history = sorted(history, key=lambda x: x.get('time', ''), reverse=True)
        history_version = current_version
    
    offset = (page - 1) * limit
    limited_history = cached_sorted_history[offset:offset + limit]
    
    return {
        'data': limited_history,
        'total': len(cached_sorted_history),
        'total_pages': (len(cached_sorted_history) + limit - 1) // limit,
        'page': page
    }


def create_code(name, employee, category):
    """
    Create a new code and add to history.
    
    Args:
        name: Name
        employee: Employee code (3 digits, not '000')
        category: Category code
    
    Returns:
        tuple: (success, code_or_error_message)
    """
    global used_codes, history, cached_sorted_history, history_version
    
    with _code_lock:
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
                'time': datetime.datetime.now().isoformat(),
                'parent_code': ''
            })
            
            # Invalidate cache
            cached_sorted_history = None
            history_version = len(history)
            
            save_data_data(used_codes, history)
            return True, code
        else:
            return False, "NO_MORE_CODES"


def validate_employee_code(employee):
    """
    Validate employee code format.
    
    Args:
        employee: Employee code to validate
    
    Returns:
        bool: True if valid, False otherwise
    """
    return len(employee) == 3 and employee.isdigit() and employee != '000'


# ========================================================================
# Flask Routes Registration
# ========================================================================

def register_routes(app):
    """
    Register code generator routes with Flask app.
    
    Args:
        app: Flask application instance
    """
    from flask import request, jsonify
    
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
        
        if not validate_employee_code(employee):
            return jsonify({"success": False, "error": "Mã nhân viên phải là 3 chữ số và không phải 000"}), 400
        
        success, result = create_code(name, employee, category)
        
        if success:
            return jsonify({"success": True, "code": result})
        else:
            return jsonify({"success": False, "error": result}), 400
    
    @app.route('/api/codes/history', methods=['GET'])
    def api_codes_history():
        """Lấy lịch sử tạo mã"""
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 100))
        
        result = get_history(page, limit)
        return jsonify(result)
    
    @app.route('/api/codes/export', methods=['GET'])
    def api_codes_export():
        """Xuất lịch sử tạo mã"""
        global cached_sorted_history, history
        
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
        data = request.get_json() or {}
        password = data.get('password', '')
        
        if not password:
            return jsonify({"success": False, "error": "Vui lòng cung cấp mật khẩu"}), 400
        
        if password != "kelly":
            return jsonify({"success": False, "error": "Mật khẩu không đúng"}), 400
        
        success = delete_history_record(code)
        
        if success:
            return jsonify({"success": True, "message": "Đã xóa thành công"})
        else:
            return jsonify({"success": False, "error": "Mã không tồn tại trong lịch sử"}), 404
    
    @app.route('/api/codes/search', methods=['GET'])
    def api_codes_search():
        """Tìm kiếm trong lịch sử tạo mã"""
        search_text = request.args.get('q', '').strip()
        results = search_history(search_text)
        return jsonify({
            "success": True,
            "data": results,
            "total": len(results)
        })
    
    @app.route('/api/codes/validate', methods=['POST'])
    def api_codes_validate():
        """Validate employee code format"""
        data = request.get_json() or {}
        employee = data.get('employee', '').strip()
        
        is_valid = validate_employee_code(employee)
        return jsonify({
            "valid": is_valid,
            "employee": employee
        })
    
    @app.route('/api/codes/restore', methods=['POST'])
    def api_codes_restore():
        """Khôi phục mã đã xóa (nếu còn trong deleted_codes)"""
        data = request.get_json() or {}
        code = data.get('code', '').strip()
        
        if not code:
            return jsonify({"success": False, "error": "Mã không được để trống"}), 400
        
        # Check if code is in deleted_codes
        if code in deleted_codes:
            # Move back to used_codes
            deleted_codes.remove(code)
            save_data_data(used_codes, history)
            return jsonify({"success": True, "message": f"Đã khôi phục mã {code}"})
        else:
            return jsonify({"success": False, "error": "Mã không tồn tại trong danh sách đã xóa"}), 404
    
    @app.route('/api/codes/batch', methods=['POST'])
    def api_codes_batch():
        """Tạo nhiều mã cùng lúc"""
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Dữ liệu không hợp lệ"}), 400
        
        category = data.get('category', '').strip()
        employee = data.get('employee', '').strip()
        count = data.get('count', 1)
        
        if not category or not employee:
            return jsonify({"success": False, "error": "Vui lòng cung cấp category và employee"}), 400
        
        if not validate_employee_code(employee):
            return jsonify({"success": False, "error": "Mã nhân viên không hợp lệ"}), 400
        
        if count < 1 or count > 10:
            return jsonify({"success": False, "error": "Số lượng phải từ 1 đến 10"}), 400
        
        results = []
        for i in range(count):
            success, result = create_code(f"Batch_{i+1}", employee, category)
            if success:
                results.append(result)
            else:
                break
        
        return jsonify({
            "success": True,
            "codes": results,
            "count": len(results)
        })


# ========================================================================
# Module Exports
# ========================================================================

__all__ = [
    'CATEGORY_PREFIXES',
    'used_codes',
    'history',
    'deleted_codes',
    'STORAGE_PATH',
    'load_data',
    'save_data_data',
    'initialize',
    'generate_code',
    'add_to_history',
    'delete_history_record',
    'search_history',
    'get_history',
    'create_code',
    'validate_employee_code',
    'register_routes'
]