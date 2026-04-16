# api_routes.py - REST API Endpoints for Projects, Codes, Notices
# Extracted from server.py for better modularity
"""
API Routes:
- GET/POST    /api/projects      - List/Create projects
- GET/PUT/DELETE /api/projects/<id> - Project CRUD
- POST       /api/projects/search - Search projects
- POST       /api/projects/filter - Filter projects
- POST       /api/codes/create   - Create code
- GET        /api/codes/history - Code history
- DELETE     /api/codes/history/<code> - Delete history
- GET        /api/notices/pending  - Pending notices
- GET        /api/notices/count    - Notice count
- POST       /api/notices/accept  - Accept job
"""
from flask import Blueprint, request, jsonify

api_bp = Blueprint('api', __name__, url_prefix='/api')

# Database helpers (will be set by init)
_get_paged_data_sql = None
_get_record_by_id = None
_update_record = None
_add_record = None
_delete_records = None
_add_sales_record = None
_get_projects_by_user = None
_get_accepted_projects_by_engineer = None
_get_all_notices_for_engineer = None
_get_pending_notices = None
_get_pending_count = None
_accept_job = None
_generate_code = None
_save_data_data = None
_used_codes = None
_history = None
_cached_sorted_history = None
_history_version = None

# Session lock for code generation
_sessions_lock = None
_schedule_save_sessions = None


def init_api_routes(db_helpers, code_helpers, sessions_lock=None, schedule_save_sessions=None):
    """Initialize with database helpers references"""
    global _get_paged_data_sql, _get_record_by_id, _update_record, _add_record
    global _delete_records, _add_sales_record, _get_projects_by_user
    global _get_accepted_projects_by_engineer, _get_all_notices_for_engineer
    global _get_pending_notices, _get_pending_count, _accept_job
    global _generate_code, _save_data_data, _used_codes, _history
    global _cached_sorted_history, _history_version
    global _sessions_lock, _schedule_save_sessions
    
    _get_paged_data_sql = db_helpers.get('get_paged_data_sql')
    _get_record_by_id = db_helpers.get('get_record_by_id')
    _update_record = db_helpers.get('update_record')
    _add_record = db_helpers.get('add_record')
    _delete_records = db_helpers.get('delete_records')
    _add_sales_record = db_helpers.get('add_sales_record')
    _get_projects_by_user = db_helpers.get('get_projects_by_user')
    _get_accepted_projects_by_engineer = db_helpers.get('get_accepted_projects_by_engineer')
    _get_all_notices_for_engineer = db_helpers.get('get_all_notices_for_engineer')
    _get_pending_notices = db_helpers.get('get_pending_notices')
    _get_pending_count = db_helpers.get('get_pending_count')
    _accept_job = db_helpers.get('accept_job')
    
    _generate_code = code_helpers.get('generate_code')
    _save_data_data = code_helpers.get('save_data_data')
    _used_codes = code_helpers.get('used_codes')
    _history = code_helpers.get('history')
    _cached_sorted_history = code_helpers.get('cached_sorted_history')
    _history_version = code_helpers.get('history_version')
    
    _sessions_lock = sessions_lock
    _schedule_save_sessions = schedule_save_sessions


@api_bp.route('/projects', methods=['GET', 'POST'])
def projects():
    """Get projects or add new project"""
    if request.method == 'GET':
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 50))
        sort_by = request.args.get('sort_by', 'Tracking ID')
        sort_order = request.args.get('sort_order', 'desc')
        
        result = _get_paged_data_sql(page, limit, sort_by, sort_order) if _get_paged_data_sql else {}
        return jsonify(result)
    
    elif request.method == 'POST':
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Dữ liệu không hợp lệ"}), 400
        
        data['is_pending'] = 'yes'
        
        new_record = _add_record(data) if _add_record else None
        if new_record:
            return jsonify({"success": True, "record": new_record}), 201
        else:
            return jsonify({"success": False, "error": "Lỗi khi thêm dự án"}), 400


@api_bp.route('/projects/<int:tracking_id>', methods=['GET', 'PUT', 'DELETE'])
def project_detail(tracking_id):
    """Project CRUD operations"""
    if request.method == 'GET':
        project = _get_record_by_id(tracking_id) if _get_record_by_id else None
        if project:
            return jsonify(project)
        else:
            return jsonify({"error": "Không tìm thấy dự án"}), 404
    
    elif request.method == 'PUT':
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Dữ liệu không hợp lệ"}), 400
        
        success = _update_record(tracking_id, data) if _update_record else False
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Lỗi khi cập nhật dự án"}), 400
    
    elif request.method == 'DELETE':
        role = request.args.get('role', 'admin')
        
        if role != 'admin':
            return jsonify({
                "success": False,
                "error": "Bạn không có quyền xóa dự án. Chỉ Admin mới được phép thực hiện thao tác này."
            }), 403
        
        deleted_count = _delete_records([tracking_id]) if _delete_records else 0
        return jsonify({"success": True, "deleted_count": deleted_count})


@api_bp.route('/projects/search', methods=['POST'])
def projects_search():
    """Search projects"""
    from src.db_helper import search_data_sql
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Dữ liệu không hợp lệ"}), 400
    
    search_text = data.get('search', '')
    page = data.get('page', 1)
    limit = data.get('limit', 50)
    sort_by = data.get('sort_by', 'Tracking ID')
    sort_order = data.get('sort_order', 'desc')
    
    result = search_data_sql(search_text, page, limit, sort_by, sort_order)
    return jsonify(result)


@api_bp.route('/projects/filter', methods=['POST'])
def projects_filter():
    """Filter projects"""
    from src.db_helper import filter_data_sql
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "Dữ liệu không hợp lệ"}), 400
    
    page = data.get('page', 1)
    limit = data.get('limit', 50)
    sort_by = data.get('sort_by', 'Tracking ID')
    sort_order = data.get('sort_order', 'desc')
    
    filters = {k: v for k, v in data.items() if k not in ['page', 'limit', 'sort_by', 'sort_order']}
    
    result = filter_data_sql(filters, page, limit, sort_by, sort_order)
    return jsonify(result)


@api_bp.route('/codes/create', methods=['POST'])
def create_code():
    """Create new drawing code"""
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
    
    code = _generate_code(_used_codes, category, employee) if _generate_code else None
    if code:
        if category != "SJT":
            if category not in _used_codes:
                _used_codes[category] = set()
            _used_codes[category].add(code)
        _history.append({
            'name': name,
            'employee': employee,
            'category': category,
            'code': code,
            'time': __import__('datetime').datetime.now().isoformat(),
            'parent_code': ''
        })
        _save_data_data(_used_codes, _history)
        return jsonify({"success": True, "code": code})
    else:
        return jsonify({"success": False, "error": "Không còn mã available cho hạng mục này"}), 400


@api_bp.route('/codes/history', methods=['GET'])
def codes_history():
    """Get code history"""
    page = int(request.args.get('page', 1))
    limit = int(request.args.get('limit', 100))
    
    global _cached_sorted_history, _history_version
    
    current_version = len(_history)
    if _cached_sorted_history is None or _history_version != current_version:
        _cached_sorted_history = sorted(_history, key=lambda x: x.get('time', ''), reverse=True)
        _history_version = current_version
    
    offset = (page - 1) * limit
    limited_history = _cached_sorted_history[offset:offset + limit]
    
    return jsonify({
        "data": limited_history,
        "total": len(_cached_sorted_history),
        "total_pages": (len(_cached_sorted_history) + limit - 1) // limit,
        "page": page
    })


@api_bp.route('/codes/export', methods=['GET'])
def codes_export():
    """Export code history"""
    global _cached_sorted_history
    if _cached_sorted_history is None:
        _cached_sorted_history = sorted(_history, key=lambda x: x.get('time', ''), reverse=True)
    
    return jsonify({
        "success": True,
        "data": _cached_sorted_history,
        "total": len(_cached_sorted_history)
    })


# Notice endpoints
@api_bp.route('/notices/pending', methods=['GET'])
def notices_pending():
    """Get pending notices for user"""
    user_id_str = request.args.get('user_id')
    user_id = int(user_id_str) if user_id_str and user_id_str.isdigit() else None
    
    try:
        notices = _get_pending_notices(user_id) if _get_pending_notices else []
        return jsonify({
            "success": True,
            "data": notices,
            "total": len(notices)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/notices/count', methods=['GET'])
def notices_count():
    """Get pending notice count"""
    user_id_str = request.args.get('user_id')
    user_id = int(user_id_str) if user_id_str and user_id_str.isdigit() else None
    
    try:
        count = _get_pending_count(user_id) if _get_pending_count else 0
        return jsonify({
            "success": True,
            "count": count
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/notices/engineer', methods=['GET'])
def notices_engineer():
    """Get all notices for engineer"""
    engineer_name = request.args.get('engineer_name')
    
    if not engineer_name:
        return jsonify({"success": False, "error": "Thiếu tên kỹ sư"}), 400
    
    try:
        notices = _get_all_notices_for_engineer(engineer_name) if _get_all_notices_for_engineer else []
        return jsonify({
            "success": True,
            "data": notices,
            "total": len(notices)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@api_bp.route('/notices/accept', methods=['POST'])
def notices_accept():
    """Engineer accepts a job"""
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "error": "Dữ liệu không hợp lệ"}), 400
    
    tracking_id = data.get('tracking_id')
    engineer_name = data.get('engineer_name')
    
    if not tracking_id or not engineer_name:
        return jsonify({"success": False, "error": "Thiếu tracking_id hoặc engineer_name"}), 400
    
    try:
        success = _accept_job(tracking_id, engineer_name) if _accept_job else False
        if success:
            return jsonify({
                "success": True,
                "message": f"Đã nhận job {tracking_id}"
            })
        else:
            return jsonify({"success": False, "error": "Không thể nhận job"}), 400
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500