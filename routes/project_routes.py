# -*- coding: utf-8 -*-
"""
Project Routes - CRUD endpoints cho Projects
Tách ra từ server.py (dòng 569-669)
"""
from flask import request, jsonify


def register_routes(app, db_functions):
    """
    Register project-related routes.
    
    Args:
        app: Flask application instance
        db_functions: Dictionary containing database helper functions
    """
    get_paged_data_sql = db_functions.get('get_paged_data_sql')
    add_record = db_functions.get('add_record')
    get_record_by_id = db_functions.get('get_record_by_id')
    update_record = db_functions.get('update_record')
    delete_records = db_functions.get('delete_records')
    
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