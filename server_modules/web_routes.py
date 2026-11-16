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
            os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tools', 'open', 'favicon.ico'),
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

register_scanner_routes(app, os.path.dirname(os.path.abspath(__file__)))


@app.route('/download/customer_selector.py')
def download_customer_selector():
    """Download the folder scanner customer selector script."""
    script_path = os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..',
            '..',
            'folderscaner',
            'customer_selector',
            'customer_selector.py',
        )
    )
    if not os.path.isfile(script_path):
        return "File not found", 404

    return send_file(script_path, as_attachment=True, download_name='customer_selector.py')


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
            create_web_session(token, user_info, client_ip)
            
            # Remove password from response
            user_info_copy = _sanitize_session_user(user_info)
            
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
        remove_web_session(token)
    
    return jsonify({"success": True, "message": "Đăng xuất thành công"})


@app.route('/api/me', methods=['GET'])
def api_me():
    """Lấy thông tin user hiện tại"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"authenticated": False, "user": None, "reason": "no_token"})
    
    token = auth_header[7:]
    session_data, error = get_web_session(token)
    if error:
        return jsonify({"authenticated": False, "user": None, "reason": error})
    
    if SESSION_TIMEOUT is None:
        remaining = None
        is_expiring_soon = False
    else:
        created_at = session_data.get('created_at', 0)
        remaining = SESSION_TIMEOUT - (time.time() - created_at)
        is_expiring_soon = remaining < 300
    
    session_user = session_data.get('user') or {}
    latest_user = get_user_with_permissions(session_user.get('username', '')) if session_user.get('username') else None
    if latest_user:
        latest_user = _sanitize_session_user(latest_user)
        session_data['user'] = latest_user
        with sessions_lock:
            if token in sessions:
                sessions[token]['user'] = latest_user
                _save_sessions_unlocked()
    else:
        latest_user = session_user

    return jsonify({
        "authenticated": True,
        "user": latest_user,
        "expires_in": int(remaining) if remaining is not None else None,
        "expiring_soon": is_expiring_soon
    })


@app.route('/api/user-preferences/<preference_key>', methods=['GET', 'PUT'])
def api_user_preference(preference_key):
    """Đọc/lưu tùy chỉnh giao diện theo user hiện tại."""
    user, error = get_user_from_bearer_token()
    if error:
        return jsonify({"success": False, "error": "Chưa đăng nhập"}), 401

    user_id = user.get('user_id') or user.get('username')
    if not user_id:
        return jsonify({"success": False, "error": "Không xác định được user"}), 400

    safe_key = str(preference_key or '').strip()
    if not safe_key or len(safe_key) > 100:
        return jsonify({"success": False, "error": "Preference key không hợp lệ"}), 400

    if request.method == 'GET':
        return jsonify({
            "success": True,
            "key": safe_key,
            "value": get_user_preference(user_id, safe_key)
        })

    data = request.get_json(silent=True) or {}
    value = data.get('value')
    success = set_user_preference(user_id, safe_key, value)
    if not success:
        return jsonify({"success": False, "error": "Không lưu được cài đặt"}), 500
    return jsonify({"success": True, "key": safe_key})


@app.route('/api/profile', methods=['PUT'])
def api_profile_update():
    """Cập nhật thông tin profile của user hiện tại"""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Bearer '):
        return jsonify({"success": False, "error": "Chưa đăng nhập"}), 401
    
    token = auth_header[7:]
    session_data, error = get_web_session(token)
    if error:
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
            if token in sessions:
                sessions[token]['user'] = _sanitize_session_user(current_user)
                _save_sessions_unlocked()
        
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
    session_data, error = get_web_session(token)
    if error:
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
        # Get projects with cursor pagination
        limit = int(request.args.get('limit', 50))
        cursor_str = request.args.get('cursor')
        sort_by = request.args.get('sort_by', 'Tracking ID')
        sort_order = request.args.get('sort_order', 'desc')
        result = get_cursor_paged_data_sql(cursor_str, limit, sort_by, sort_order)
        return jsonify(result)
    
    elif request.method == 'POST':
        # Add new project
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "Dữ liệu không hợp lệ"}), 400

        allowed, error = can_user_create_project(get_project_user_from_request())
        if not allowed:
            return jsonify({"success": False, "error": error}), 403
        
        # Auto-set is_pending = 'yes' for new projects
        data['is_pending'] = 'yes'
        
        new_record = add_record(data)
        if new_record:
            publish_notice_event(
                event_type='new_project_pending',
                message=f"Dự án #{new_record.get('Tracking ID')} mới đang chờ nhận",
                target_roles=['engineer', 'eng', 'admin'],
                record=new_record,
                tracking_id=new_record.get('Tracking ID')
            )
            publish_project_event(
                'project_created',
                message=f"Dự án #{new_record.get('Tracking ID')} mới được tạo",
                tracking_id=new_record.get('Tracking ID'),
                record=new_record
            )
            return jsonify({"success": True, "record": new_record}), 201
        else:
            return jsonify({"success": False, "error": "Lỗi khi thêm dự án"}), 400


@app.route('/api/projects/stream', methods=['GET'])
def api_projects_stream():
    """SSE stream cho bảng projects realtime collaboration."""
    username = request.args.get('username', '')
    user_id = request.args.get('user_id', '')
    user_name = request.args.get('user_name', '') or request.args.get('full_name', '') or username or user_id

    client_id = uuid.uuid4().hex
    client_queue = queue.Queue(maxsize=100)

    with project_subscribers_lock:
        project_subscribers[client_id] = {
            "queue": client_queue,
            "username": username,
            "user_id": user_id,
            "user_name": user_name,
            "connected_at": time.time()
        }

    client_queue.put({
        "event_id": f"connected-{int(time.time())}",
        "type": "connected",
        "message": "project-stream-connected",
        "locks": get_active_project_locks(),
        "online_users": get_project_online_users(),
        "timestamp": int(time.time())
    })
    publish_project_event('presence', extra={"online_users": get_project_online_users()})

    def event_stream():
        try:
            while True:
                try:
                    payload = client_queue.get(timeout=20)
                    yield format_sse('project', payload)
                except queue.Empty:
                    yield format_sse('ping', {"timestamp": int(time.time())})
        except GeneratorExit:
            pass
        finally:
            with project_subscribers_lock:
                project_subscribers.pop(client_id, None)
            publish_project_event('presence', extra={"online_users": get_project_online_users()})

    response = Response(stream_with_context(event_stream()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Connection'] = 'keep-alive'
    return response


@app.route('/api/projects/locks', methods=['GET'])
def api_project_locks():
    return jsonify({"success": True, "locks": get_active_project_locks()})


@app.route('/api/users/designers', methods=['GET'])
def api_user_designers():
    """Danh sách tên nhân viên thiết kế lấy từ thông tin tài khoản user."""
    user, error = get_user_from_bearer_token()
    if error:
        return jsonify({"success": False, "error": "Chưa đăng nhập"}), 401

    designer_roles = {'engineer', 'eng', 'designer', 'admin', 'it'}
    designers = []
    seen = set()
    for item in get_all_users():
        username = str(item.get('username') or '').strip()
        employee_id = str(item.get('employee_id') or '').strip()
        status = str(item.get('status') or '').lower()
        if status and status not in {'active', 'enabled'}:
            continue
        role = str(item.get('role') or '').lower()
        if role not in designer_roles:
            continue
        if re.fullmatch(r'ENG\d{3}', username, re.IGNORECASE) or re.fullmatch(r'ENG\d{3}', employee_id, re.IGNORECASE):
            continue
        name = str(item.get('full_name') or item.get('username') or '').strip()
        if re.fullmatch(r'Engineer\s+\d{3}', name, re.IGNORECASE):
            continue
        if not name or name.lower() in seen:
            continue
        seen.add(name.lower())
        designers.append({
            "value": name,
            "label": name,
            "username": username,
            "employee_id": employee_id,
            "role": item.get('role') or ''
        })

    designers.sort(key=lambda row: str(row.get('label') or '').lower())
    return jsonify({"success": True, "designers": designers})


@app.route('/api/projects/column-edit-locks', methods=['GET', 'PUT'])
def api_project_column_edit_locks():
    """Đọc/lưu danh sách cột project bị khóa chỉnh sửa toàn cục."""
    if request.method == 'GET':
        return jsonify({
            "success": True,
            "locked_columns": get_project_column_edit_locks()
        })

    user, error = get_user_from_bearer_token()
    if error:
        return jsonify({"success": False, "error": "Chưa đăng nhập"}), 401
    if not is_admin_user(user):
        return jsonify({"success": False, "error": "Chỉ admin được khóa/mở khóa chỉnh sửa cột"}), 403

    data = request.get_json(silent=True) or {}
    locked_columns = normalize_project_column_edit_locks(data.get('locked_columns', []))
    if not set_project_column_edit_locks(locked_columns):
        return jsonify({"success": False, "error": "Không lưu được danh sách cột khóa"}), 500
    publish_project_event('column_edit_locks_updated', extra={"locked_columns": locked_columns})
    return jsonify({"success": True, "locked_columns": locked_columns})


@app.route('/api/projects/cursor', methods=['POST'])
def api_project_cursor():
    """Broadcast ô project user đang chọn/chỉnh cho các client khác."""
    user, _ = get_user_from_bearer_token()
    data = request.get_json(silent=True) or {}
    tracking_id = data.get('tracking_id')
    field_name = data.get('field_name') or data.get('field') or ''
    row = data.get('row')
    column = data.get('column')

    if tracking_id in (None, '') and row in (None, ''):
        return jsonify({"success": False, "error": "Thiếu tracking_id hoặc row"}), 400

    user_id = str(data.get('user_id') or (user or {}).get('user_id') or (user or {}).get('username') or 'anonymous')
    user_name = str(data.get('user_name') or (user or {}).get('full_name') or (user or {}).get('username') or user_id)
    payload = {
        "user_id": user_id,
        "user_name": user_name,
        "tracking_id": tracking_id,
        "field_name": normalize_project_field_name(field_name) if field_name else '',
        "field_label": data.get('field_label') or '',
        "row": row,
        "column": column
    }
    publish_project_event('cursor', tracking_id=tracking_id, field_name=payload["field_name"], extra={"cursor": payload})
    return jsonify({"success": True})


@app.route('/api/projects/<int:tracking_id>/locks', methods=['POST', 'DELETE'])
def api_project_cell_lock(tracking_id):
    user, _ = get_user_from_bearer_token()
    data = request.get_json(silent=True) or {}
    field_name = data.get('field_name') or data.get('field') or ''
    if not field_name:
        return jsonify({"success": False, "error": "Thiếu field_name"}), 400

    allowed, error = can_user_update_project(get_project_user_from_request(), {field_name: ''})
    if not allowed:
        return jsonify({"success": False, "error": error}), 403

    user_id = str(data.get('user_id') or (user or {}).get('user_id') or (user or {}).get('username') or 'anonymous')
    user_name = str(data.get('user_name') or (user or {}).get('full_name') or (user or {}).get('username') or user_id)

    if request.method == 'POST':
        result = lock_project_cell(tracking_id, field_name, user_id, user_name)
        status = 200 if result.get('success') else 423
        if result.get('success'):
            publish_project_event('cell_locked', tracking_id=tracking_id, field_name=field_name, lock=result.get('lock'))
        return jsonify(result), status

    unlocked = unlock_project_cell(tracking_id, field_name, user_id)
    if unlocked:
        publish_project_event('cell_unlocked', tracking_id=tracking_id, field_name=field_name, extra={
            "locked_by": user_id
        })
    return jsonify({"success": True, "unlocked": unlocked})


@app.route('/api/projects/<int:tracking_id>/changes', methods=['GET'])
def api_project_change_logs(tracking_id):
    """Lấy nhật ký thay đổi của một project hoặc một field."""
    field_name = request.args.get('field_name') or request.args.get('field') or ''
    limit = request.args.get('limit', 100)
    try:
        logs = get_project_change_logs(tracking_id, field_name=field_name, limit=int(limit))
        return jsonify({"success": True, "logs": logs, "total": len(logs)})
    except Exception as e:
        return jsonify({"success": False, "error": str(e), "logs": []}), 500


@app.route('/api/projects/changes/<int:change_id>/revert', methods=['POST'])
def api_project_change_revert(change_id):
    """Hoàn tác một thay đổi từ audit log."""
    data = request.get_json(silent=True) or {}
    change_log = get_project_change_log(change_id)
    if not change_log:
        return jsonify({"success": False, "error": "Không tìm thấy lịch sử chỉnh sửa"}), 404
    field_name = change_log.get('field_name') or ''

    request_user = get_project_user_from_request()
    allowed, error = can_user_update_project(request_user, {field_name: ''})
    if not allowed:
        return jsonify({"success": False, "error": error}), 403

    user = request_user or {}
    expected_version = data.get('expected_version', data.get('version'))
    changed_by = str(user.get('user_id') or user.get('username') or data.get('changed_by') or 'anonymous')
    changed_by_name = str(user.get('full_name') or user.get('username') or data.get('changed_by_name') or changed_by)
    result = revert_project_change_log(change_id, expected_version, changed_by, changed_by_name)
    status = int(result.pop('status', 200 if result.get('success') else 400))
    if result.get('success'):
        publish_project_event(
            'project_updated',
            tracking_id=result.get('tracking_id'),
            record=result.get('record'),
            extra={
                "version": result.get('version'),
                "changed_fields": result.get('changed_fields', []),
                "reverted_change_id": result.get('reverted_change_id')
            }
        )
    return jsonify(result), status


@app.route('/api/projects/<int:tracking_id>/comments', methods=['GET', 'POST'])
def api_project_comments(tracking_id):
    """Đọc/thêm bình luận cho project hoặc field."""
    if request.method == 'GET':
        field_name = request.args.get('field_name') or request.args.get('field') or ''
        include_resolved = request.args.get('include_resolved') == '1'
        comments = get_project_comments(tracking_id, field_name=field_name, include_resolved=include_resolved)
        return jsonify({"success": True, "comments": comments, "total": len(comments)})

    data = request.get_json(silent=True) or {}
    text = data.get('comment_text') or data.get('text') or ''
    if not str(text).strip():
        return jsonify({"success": False, "error": "Bình luận không được để trống"}), 400

    user = get_project_user_from_request()
    user_id = str((user or {}).get('user_id') or (user or {}).get('username') or data.get('created_by') or 'anonymous')
    user_name = str((user or {}).get('full_name') or (user or {}).get('username') or data.get('created_by_name') or user_id)
    field_name = data.get('field_name') or data.get('field') or ''
    comment = add_project_comment(tracking_id, text, field_name=field_name, created_by=user_id, created_by_name=user_name)
    if not comment:
        return jsonify({"success": False, "error": "Không thể thêm bình luận"}), 400

    publish_project_event('comment_added', tracking_id=tracking_id, field_name=comment.get('field_name'), extra={"comment": comment})
    return jsonify({"success": True, "comment": comment}), 201


@app.route('/api/projects/comments/<int:comment_id>', methods=['DELETE'])
def api_project_comment_delete(comment_id):
    """Xóa mềm bình luận."""
    user = get_project_user_from_request()
    success = delete_project_comment(comment_id, deleted_by=str((user or {}).get('user_id') or ''))
    if not success:
        return jsonify({"success": False, "error": "Không tìm thấy bình luận hoặc đã xóa"}), 404
    publish_project_event('comment_deleted', extra={"comment_id": comment_id})
    return jsonify({"success": True})


def _get_scanner_repair_user_key(user):
    user = user or {}
    return str(
        user.get('user_id')
        or user.get('id')
        or user.get('username')
        or user.get('full_name')
        or ''
    ).strip()


def _is_scanner_project_code(value):
    return bool(re.match(r'^[A-Z][A-Z0-9]{0,7}-\d{4}-\d{3}(?:-[A-Z0-9]+)?$', str(value or '').strip(), re.IGNORECASE))


def _find_project_by_plan_code(plan_code):
    code = str(plan_code or '').strip().upper()
    if not code:
        return None

    try:
        db_path = os.path.abspath('DB.db')
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT tracking_id
            FROM projects
            WHERE UPPER(COALESCE(ma_ban_ve, '')) = ?
            ORDER BY tracking_id DESC
            LIMIT 1
            """,
            (code,),
        )
        row = cursor.fetchone()
        conn.close()
        if row:
            return get_record_by_id(row["tracking_id"])
    except Exception as exc:
        print(f"[ScannerRepair] Cannot find project by plan code {code}: {exc}")
    return None


def _get_active_scanner_user_keys():
    candidates = []
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_paths = [
        os.getenv('SCANNER_DB_PATH', ''),
        os.path.abspath(os.path.join(os.getcwd(), '..', '..', 'folderscaner', 'folders.db')),
        os.path.abspath(os.path.join(base_dir, '..', '..', 'folderscaner', 'folders.db')),
        os.path.abspath(os.path.join(base_dir, '..', '..', '..', 'folderscaner', 'folders.db')),
    ]
    seen_paths = set()
    for db_path in db_paths:
        if not db_path:
            continue
        db_path = os.path.abspath(db_path)
        if db_path in seen_paths or not os.path.exists(db_path):
            continue
        seen_paths.add(db_path)
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT user_key FROM user_smb_roots WHERE active = 1 AND COALESCE(smb_root, '') != ''")
            candidates.extend(str(row[0]).strip() for row in cursor.fetchall() if str(row[0]).strip())
            conn.close()
        except Exception as exc:
            print(f"[ScannerRepair] Cannot read scanner roots from {db_path}: {exc}")
    return list(dict.fromkeys(candidates))


def _repair_deleted_scanner_projects(plan_codes, user_key):
    codes = [str(code or '').strip().upper() for code in plan_codes if _is_scanner_project_code(code)]
    codes = list(dict.fromkeys(codes))
    if not codes or not user_key:
        return

    def worker():
        try:
            scanner_backend_url = os.getenv('SCANNER_BACKEND_URL', 'http://127.0.0.1:18001').rstrip('/')
            user_keys = list(dict.fromkeys([user_key] + _get_active_scanner_user_keys()))
            scanned = False
            for scanner_user_key in user_keys:
                response = requests.post(
                    f"{scanner_backend_url}/api/scanner/scan",
                    params={"user_key": scanner_user_key, "force_documents": "true"},
                    timeout=120,
                )
                if response.ok:
                    scanned = True
                    if all(_find_project_by_plan_code(code) for code in codes):
                        break
                else:
                    print(f"[ScannerRepair] Scan failed for user {scanner_user_key}: {response.status_code} {response.text[:200]}")

            if not scanned:
                return

            for code in codes:
                record = _find_project_by_plan_code(code)
                if record:
                    publish_project_event(
                        'project_created',
                        message=f"Dự án {code} được scanner đồng bộ lại",
                        tracking_id=record.get('Tracking ID') or record.get('tracking_id'),
                        record=record
                    )
        except Exception as exc:
            print(f"[ScannerRepair] Cannot resync deleted scanner project: {exc}")

    threading.Thread(target=worker, daemon=True).start()


@app.route('/api/projects/<tracking_id>', methods=['DELETE'])
@app.route('/api/projects/<int:tracking_id>', methods=['GET', 'PUT'])
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

        request_user = get_project_user_from_request()
        allowed, error = can_user_update_project(request_user, data)
        if not allowed:
            return jsonify({"success": False, "error": error}), 403

        if 'version' in data or 'expected_version' in data:
            user = request_user
            expected_version = data.pop('expected_version', data.pop('version', None))
            changed_by = str((user or {}).get('user_id') or (user or {}).get('username') or data.pop('changed_by', '') or 'anonymous')
            changed_by_name = str((user or {}).get('full_name') or (user or {}).get('username') or data.pop('changed_by_name', '') or changed_by)
            result = update_project_with_version(tracking_id, data, expected_version, changed_by, changed_by_name)
            status = int(result.pop('status', 200 if result.get('success') else 400))
            if result.get('success'):
                publish_project_event(
                    'project_updated',
                    tracking_id=tracking_id,
                    record=result.get('record'),
                    extra={"version": result.get('version'), "changed_fields": result.get('changed_fields', [])}
                )
            return jsonify(result), status
        
        success = update_record(tracking_id, data)
        if success:
            publish_project_event('project_updated', tracking_id=tracking_id, record=get_record_by_id(tracking_id))
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Lỗi khi cập nhật dự án"}), 400
    
    elif request.method == 'DELETE':
        # Check admin role
        role = request.args.get('role', '')
        request_user = get_project_user_from_request()
        
        if not can_user_delete_project(request_user, role):
            return jsonify({
                "success": False,
                "error": "Bạn không có quyền xóa dự án. Chỉ Admin mới được phép thực hiện thao tác này."
            }), 403
        
        tracking_ids = []
        for raw_id in str(tracking_id).split(','):
            raw_id = raw_id.strip()
            if not raw_id:
                continue
            try:
                tracking_ids.append(int(raw_id))
            except ValueError:
                return jsonify({"success": False, "error": "Tracking ID không hợp lệ"}), 400

        if not tracking_ids:
            return jsonify({"success": False, "error": "Chưa chọn dự án cần xóa"}), 400

        deleted_plan_codes = []
        for tid in tracking_ids:
            record = get_record_by_id(tid)
            plan_code = (record or {}).get('ma_ban_ve') or (record or {}).get('Mã bản vẽ') or ''
            if _is_scanner_project_code(plan_code):
                deleted_plan_codes.append(plan_code)

        deleted_count = delete_records(tracking_ids)
        if deleted_count:
            for deleted_id in tracking_ids:
                publish_project_event('project_deleted', tracking_id=deleted_id)
            _repair_deleted_scanner_projects(deleted_plan_codes, _get_scanner_repair_user_key(request_user))
        return jsonify({"success": True, "deleted_count": deleted_count})


@app.route('/api/projects/restore', methods=['POST'])
def api_projects_restore():
    """Khôi phục dự án đã xóa từ snapshot undo ở frontend."""
    data = request.get_json() or {}
    records = data.get('records') or []
    restored_count = restore_records(records)
    return jsonify({"success": restored_count > 0, "restored_count": restored_count})


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
    sort_order = data.get('sort_order', 'asc')
    
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
    sort_order = data.get('sort_order', 'asc')
    
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
    plan_code = data.get('plan_code', '').strip()
    
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
            'plan_code': plan_code,
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
    search = request.args.get('search', '').strip().lower()
    normalized_search = ''.join(ch for ch in search if ch.isalnum())
    
    global history_version, cached_sorted_history
    current_version = len(history)
    if cached_sorted_history is None or history_version != current_version:
        cached_sorted_history = sorted(history, key=lambda x: x.get('time', ''), reverse=True)
        history_version = current_version
    
    filtered_history = cached_sorted_history
    if search:
        searchable_fields = ('name', 'employee', 'category', 'plan_code', 'code', 'parent_code', 'time')
        filtered_history = [
            item for item in cached_sorted_history
            if any(
                search in str(item.get(field, '')).lower()
                or (
                    normalized_search
                    and normalized_search in ''.join(ch for ch in str(item.get(field, '')).lower() if ch.isalnum())
                )
                for field in searchable_fields
            )
        ]
    
    offset = (page - 1) * limit
    limited_history = filtered_history[offset:offset + limit]

    # Build lightweight stats from full history (not only current page)
    from datetime import datetime, timedelta
    now = datetime.now()
    today = now.date()
    week_start = today - timedelta(days=today.weekday())  # Monday

    today_count = 0
    week_count = 0
    latest_time = filtered_history[0].get('time') if filtered_history else None

    for item in filtered_history:
        ts = item.get('time')
        if not ts:
            continue
        try:
            item_dt = datetime.fromisoformat(ts)
        except Exception:
            continue
        item_date = item_dt.date()
        if item_date == today:
            today_count += 1
        if item_date >= week_start:
            week_count += 1
    
    return jsonify({
        "data": limited_history,
        "total": len(filtered_history),
        "total_pages": (len(filtered_history) + limit - 1) // limit,
        "page": page,
        "stats": {
            "total": len(filtered_history),
            "today": today_count,
            "week": week_count,
            "latest_time": latest_time
        }
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
    from datetime import datetime, timedelta

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

    created_at_raw = to_remove.get('time', '')
    try:
        created_at = datetime.fromisoformat(created_at_raw)
    except Exception:
        return jsonify({
            "success": False,
            "error": "Không thể xóa mã không có thời gian tạo hợp lệ"
        }), 400

    if datetime.now() - created_at > timedelta(hours=2):
        return jsonify({
            "success": False,
            "error": "Chỉ được xóa mã trong vòng 2 giờ kể từ khi tạo"
        }), 403
    
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
        session_data, _ = get_web_session(token)
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

_CUSTOMER_DOC_LOOKUP_CACHE = None

def _load_customer_doc_lookup():
    """Read docs/customer archive as a fallback for missing phonetic metadata."""
    global _CUSTOMER_DOC_LOOKUP_CACHE
    if _CUSTOMER_DOC_LOOKUP_CACHE is not None:
        return _CUSTOMER_DOC_LOOKUP_CACHE

    lookup = {}
    docs_path = os.path.abspath(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            '..',
            'docs',
            '客户档案.md',
        )
    )
    try:
        with open(docs_path, 'r', encoding='utf-8') as file:
            for line in file:
                text = line.strip()
                if not text.startswith('|') or text.startswith('|---') or 'Tên Khách Hàng' in text:
                    continue
                cells = [cell.strip() for cell in text.strip('|').split('|')]
                if len(cells) < 4:
                    continue
                code, name, phonetic, english_name = cells[:4]
                if not name:
                    continue
                lookup[name] = {
                    'code': code,
                    'phonetic': phonetic,
                    'english_name': english_name,
                }
    except Exception as e:
        safe_print(f"[Customers] Cannot load customer archive fallback: {e}")

    _CUSTOMER_DOC_LOOKUP_CACHE = lookup
    return lookup

@app.route('/api/customers', methods=['GET'])
def api_customers():
    """Lấy danh sách khách hàng cho dropdown"""
    try:
        # Dùng helper để tương thích schema cũ/mới của bảng customers
        # (một số DB không có các cột code/phonetic/english_name).
        results = get_all_customers()
        archive_lookup = _load_customer_doc_lookup()

        customers = []
        for row in results:
            customer_name = row.get('name') or ''
            archive_customer = archive_lookup.get(customer_name, {})
            customer_code = row.get('code')
            if not customer_code:
                # Fallback cho schema hiện tại: dùng id để giữ định dạng hiển thị ổn định
                customer_id = row.get('id')
                customer_code = archive_customer.get('code') or (str(customer_id) if customer_id is not None else '')

            customers.append({
                'id': row.get('id'),
                'code': customer_code,
                'name': customer_name,
                'phonetic': row.get('phonetic') or archive_customer.get('phonetic') or '',
                'english_name': row.get('english_name') or archive_customer.get('english_name') or '',
                'contact_person': row.get('contact_person') or '',
                'phone': row.get('phone') or '',
                'email': row.get('email') or '',
                'address': row.get('address') or ''
            })

        customers.sort(key=lambda c: (c.get('code', ''), c.get('name', '')))
        
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


@app.route('/api/customers', methods=['POST'])
def api_create_customer():
    """Tạo khách hàng mới (cần đăng nhập)"""
    user, error = get_user_from_bearer_token()
    if error:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        data = request.get_json() or {}
        name = (data.get('name') or '').strip()
        if not name:
            return jsonify({"success": False, "error": "Tên khách hàng không được để trống"}), 400

        customer_data = {
            'code': data.get('code', ''),
            'name': name,
            'phonetic': data.get('phonetic', ''),
            'english_name': data.get('english_name', ''),
            'contact_person': data.get('contact_person', ''),
            'phone': data.get('phone', ''),
            'email': data.get('email', ''),
            'address': data.get('address', '')
        }

        customer_id = add_customer(customer_data)
        if customer_id:
            customer = get_customer_by_id(customer_id)
            return jsonify({"success": True, "data": customer}), 201
        else:
            return jsonify({"success": False, "error": "Khách hàng đã tồn tại"}), 409

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/customers/<int:customer_id>', methods=['PUT'])
def api_update_customer(customer_id):
    """Cập nhật thông tin khách hàng (cần đăng nhập)"""
    user, error = get_user_from_bearer_token()
    if error:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        data = request.get_json() or {}
        customer_data = {k: v for k, v in data.items() if k in {
            'code', 'name', 'phonetic', 'english_name',
            'contact_person', 'phone', 'email', 'address'
        }}

        if not customer_data:
            return jsonify({"success": False, "error": "Không có dữ liệu để cập nhật"}), 400

        success = update_customer(customer_id, customer_data)
        if success:
            customer = get_customer_by_id(customer_id)
            return jsonify({"success": True, "data": customer})
        else:
            return jsonify({"success": False, "error": "Không tìm thấy khách hàng"}), 404

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@app.route('/api/customers/<int:customer_id>', methods=['DELETE'])
def api_delete_customer(customer_id):
    """Xóa khách hàng (cần đăng nhập)"""
    user, error = get_user_from_bearer_token()
    if error:
        return jsonify({"success": False, "error": "Unauthorized"}), 401

    try:
        success = delete_customer(customer_id)
        if success:
            return jsonify({"success": True})
        else:
            return jsonify({"success": False, "error": "Không tìm thấy khách hàng"}), 404

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# ========================================================================
# Notice/Pending Tab API Endpoints (for web client)
# ========================================================================

@app.route('/api/notices/stream', methods=['GET'])
def api_notices_stream():
    """
    SSE stream cho thông báo realtime.
    Dùng cho roles engineer/eng/admin để nhận notice ngay khi có job pending mới.
    """
    role = normalize_notice_role(request.args.get('role', ''))
    username = request.args.get('username', '')
    user_id = request.args.get('user_id', '')

    client_id = uuid.uuid4().hex
    client_queue = queue.Queue(maxsize=100)

    with notice_subscribers_lock:
        notice_subscribers[client_id] = {
            "queue": client_queue,
            "role": role,
            "username": username,
            "user_id": user_id,
            "connected_at": time.time()
        }

    # Push connected event ngay khi đăng ký thành công
    client_queue.put({
        "event_id": f"connected-{int(time.time())}",
        "type": "connected",
        "message": "notice-stream-connected",
        "targets": [],
        "timestamp": int(time.time())
    })

    def event_stream():
        try:
            while True:
                try:
                    payload = client_queue.get(timeout=20)
                    yield format_sse('notice', payload)
                except queue.Empty:
                    yield format_sse('ping', {"timestamp": int(time.time())})
        except GeneratorExit:
            pass
        finally:
            with notice_subscribers_lock:
                notice_subscribers.pop(client_id, None)

    response = Response(stream_with_context(event_stream()), mimetype='text/event-stream')
    response.headers['Cache-Control'] = 'no-cache'
    response.headers['X-Accel-Buffering'] = 'no'
    response.headers['Connection'] = 'keep-alive'
    return response

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
            updated_record = get_record_by_id(tracking_id)
            publish_notice_event(
                event_type='job_accepted',
                message=f"Job #{tracking_id} đã được {engineer_name} nhận",
                target_roles=['engineer', 'eng', 'admin'],
                tracking_id=tracking_id,
                extra={"accepted_by": engineer_name}
            )
            publish_project_event(
                'project_updated',
                message=f"Job #{tracking_id} đã được {engineer_name} nhận",
                tracking_id=tracking_id,
                record=updated_record,
                extra={"accepted_by": engineer_name}
            )
            return jsonify({
                "success": True,
                "message": f"Đã nhận job {tracking_id}",
                "record": updated_record
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
