# -*- coding: utf-8 -*-
"""
Code Routes - Endpoints cho Code generation
Tách ra từ server.py (dòng 672-782)
"""
from flask import request, jsonify


def register_routes(app, code_state, helper_functions):
    """
    Register code generation routes.
    
    Args:
        app: Flask application instance
        code_state: Dictionary containing code state variables
            - used_codes: dict of used codes by category
            - history: list of code creation history
            - deleted_codes: set of deleted codes
            - cached_sorted_history: cached sorted history
            - history_version: version counter for cache invalidation
        helper_functions: Dictionary containing helper functions
            - generate_code: function to generate new code
            - save_data_data: function to save code state to file
    """
    used_codes = code_state.get('used_codes')
    history = code_state.get('history')
    deleted_codes = code_state.get('deleted_codes')
    generate_code = helper_functions.get('generate_code')
    save_data_data = helper_functions.get('save_data_data')
    
    # Reference to cached_sorted_history and history_version (mutated in-place)
    cached_sorted_history_ref = code_state.get('cached_sorted_history_ref')
    history_version_ref = code_state.get('history_version_ref')
    
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
        
        if cached_sorted_history_ref is not None and history_version_ref is not None:
            current_version = len(history)
            if cached_sorted_history_ref[0] is None or history_version_ref[0] != current_version:
                cached_sorted_history_ref[0] = sorted(history, key=lambda x: x.get('time', ''), reverse=True)
                history_version_ref[0] = current_version
            
            offset = (page - 1) * limit
            limited_history = cached_sorted_history_ref[0][offset:offset + limit]
            
            return jsonify({
                "data": limited_history,
                "total": len(cached_sorted_history_ref[0]),
                "total_pages": (len(cached_sorted_history_ref[0]) + limit - 1) // limit,
                "page": page
            })
        else:
            # Fallback if references not provided
            sorted_history = sorted(history, key=lambda x: x.get('time', ''), reverse=True)
            offset = (page - 1) * limit
            limited_history = sorted_history[offset:offset + limit]
            
            return jsonify({
                "data": limited_history,
                "total": len(sorted_history),
                "total_pages": (len(sorted_history) + limit - 1) // limit,
                "page": page
            })


    @app.route('/api/codes/export', methods=['GET'])
    def api_codes_export():
        """Xuất lịch sử tạo mã"""
        if cached_sorted_history_ref is not None:
            if cached_sorted_history_ref[0] is None:
                cached_sorted_history_ref[0] = sorted(history, key=lambda x: x.get('time', ''), reverse=True)
            
            return jsonify({
                "success": True,
                "data": cached_sorted_history_ref[0],
                "total": len(cached_sorted_history_ref[0])
            })
        else:
            # Fallback
            sorted_history = sorted(history, key=lambda x: x.get('time', ''), reverse=True)
            return jsonify({
                "success": True,
                "data": sorted_history,
                "total": len(sorted_history)
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