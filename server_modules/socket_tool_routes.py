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
            sort_order = req_data.get('sort_order', 'asc')
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
            response_data = {"success": success, "record": get_record_by_id(tracking_id) if success else None}
            
        elif request_type == "ADD_SALES_RECORD":
            record_data = req_data.get('record', {})
            new_record = add_sales_record(record_data)
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
        sshfs_exists = os.path.exists(SSHFS_EXCEL_PATH)
        sshfs_cache_exists = os.path.exists(SSHFS_EXCEL_CACHE_PATH)
        fallback_exists = os.path.exists(FALLBACK_EXCEL_PATH)
        fallback_available = sshfs_exists or sshfs_cache_exists or fallback_exists or bool(FALLBACK_EXCEL_URL)
        usable = excel_exists or fallback_available
        
        return jsonify({
            "status": "ready" if usable else "error",
            "message": "Sẵn sàng" if excel_exists else (
                "Excel nội bộ lỗi, sẽ dùng fallback" if fallback_available else "Không thể kết nối Excel"
            ),
            "excel_path": excel_path,
            "excel_exists": excel_exists,
            "sshfs_excel_path": SSHFS_EXCEL_PATH,
            "sshfs_excel_exists": sshfs_exists,
            "sshfs_excel_cache_path": SSHFS_EXCEL_CACHE_PATH,
            "sshfs_excel_cache_exists": sshfs_cache_exists,
            "fallback_excel_url": FALLBACK_EXCEL_URL,
            "fallback_excel_path": FALLBACK_EXCEL_PATH,
            "fallback_excel_exists": fallback_exists
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


@app.route('/api/materials/<path:code>/documents', methods=['GET'])
def api_material_documents(code):
    """Tra tài liệu theo mã liệu/mã bản vẽ và trả file URLs qua API server."""
    if not TOOL_OPEN_AVAILABLE:
        return jsonify({"success": False, "message": "Tool Open not available", "documents": []}), 503

    clean_code = str(code or '').strip().strip('"').strip("'")
    if not clean_code:
        return jsonify({"success": False, "message": "Mã không được để trống", "documents": []}), 400

    try:
        include_erp = request.args.get('include_erp', '1') != '0'
        if material_core.is_engineer_fig_no(clean_code):
            requested_cinv_code = str(request.args.get('cinv_code') or '').strip()
            if requested_cinv_code:
                urls = material_core.query_material(requested_cinv_code)
                payload = build_material_documents_payload(
                    clean_code,
                    urls,
                    resolved_code=requested_cinv_code,
                    matches=[],
                    include_erp=include_erp
                )
                return jsonify(payload), 200 if payload["success"] else 404

            matches = material_core.find_cinvcode_from_excel(clean_code, return_all=True)
            if not matches:
                return jsonify({
                    "success": False,
                    "code": clean_code,
                    "documents": [],
                    "matches": [],
                    "message": f"Không tìm thấy mã mẹ cho: {clean_code}"
                }), 404

            if len(matches) > 1 and not request.args.get('cinv_code'):
                return jsonify({
                    "success": False,
                    "code": clean_code,
                    "documents": [],
                    "matches": matches,
                    "message": f"Tìm thấy {len(matches)} mã mẹ, cần chọn một mã"
                }), 409

            resolved_code = request.args.get('cinv_code') or matches[0]['cInvCode']
            urls = material_core.query_material(resolved_code)
            payload = build_material_documents_payload(clean_code, urls, resolved_code=resolved_code, matches=matches, include_erp=include_erp)
            return jsonify(payload), 200 if payload["success"] else 404

        urls = material_core.query_material(clean_code)
        payload = build_material_documents_payload(clean_code, urls, resolved_code=clean_code, include_erp=include_erp)
        return jsonify(payload), 200 if payload["success"] else 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e), "documents": []}), 500


@app.route('/api/materials/file/<token>', methods=['GET'])
def api_material_file(token):
    """Trả file vật liệu qua server để browser không truy cập trực tiếp ổ mạng."""
    path = get_material_file_path_from_token(token)
    if not path:
        return jsonify({"success": False, "message": "File token không hợp lệ hoặc đã hết hạn"}), 404

    normalized_path = material_core.normalize_unc_path(path) if TOOL_OPEN_AVAILABLE else path
    if not os.path.exists(normalized_path) or not os.path.isfile(normalized_path):
        return jsonify({"success": False, "message": "File không tồn tại hoặc server không truy cập được"}), 404

    mimetype = mimetypes.guess_type(normalized_path)[0] or 'application/octet-stream'
    response = send_file(
        normalized_path,
        mimetype=mimetype,
        as_attachment=request.args.get('download') == '1',
        download_name=os.path.basename(normalized_path)
    )
    try:
        response.headers['X-Material-File-Size'] = str(os.path.getsize(normalized_path))
    except OSError:
        pass
    return response


@app.route('/api/materials/folder/<token>', methods=['GET'])
def api_material_folder(token):
    """Liệt kê nội dung thư mục vật liệu qua API server."""
    path = get_material_path_from_token(token, expected_type='folder')
    if not path:
        return jsonify({"success": False, "message": "Folder token không hợp lệ hoặc đã hết hạn"}), 404

    normalized_path = material_core.normalize_unc_path(path) if TOOL_OPEN_AVAILABLE else path
    if not os.path.isdir(normalized_path):
        return jsonify({"success": False, "message": "Thư mục không tồn tại hoặc server không truy cập được"}), 404

    try:
        entries = []
        with os.scandir(normalized_path) as iterator:
            for entry in iterator:
                try:
                    is_dir = entry.is_dir()
                    item = {
                        "name": entry.name,
                        "type": "folder" if is_dir else classify_material_file(entry.path),
                        "is_dir": is_dir,
                        "size": 0 if is_dir else entry.stat().st_size,
                        "modified_at": datetime.fromtimestamp(entry.stat().st_mtime).isoformat()
                    }
                    if is_dir:
                        child_token = create_material_file_token(entry.path, token_type='folder')
                        item["list_url"] = f"/api/materials/folder/{child_token}"
                        item["open_url"] = f"/api/materials/folder/{child_token}/open"
                    else:
                        file_token = create_material_file_token(entry.path)
                        item["view_url"] = f"/api/materials/file/{file_token}"
                        item["download_url"] = f"/api/materials/file/{file_token}?download=1"
                    entries.append(item)
                except OSError:
                    continue

        entries.sort(key=lambda item: (not item.get("is_dir"), item.get("name", "").lower()))
        return jsonify({
            "success": True,
            "folder_name": os.path.basename(normalized_path),
            "entries": entries[:300],
            "total": len(entries),
            "truncated": len(entries) > 300,
            "open_url": f"/api/materials/folder/{token}/open"
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500


@app.route('/api/materials/folder/<token>/open', methods=['POST'])
def api_material_folder_open(token):
    """Mở thư mục vật liệu bằng Windows Explorer trên máy chạy server."""
    path = get_material_path_from_token(token, expected_type='folder')
    if not path:
        return jsonify({"success": False, "message": "Folder token không hợp lệ hoặc đã hết hạn"}), 404

    normalized_path = material_core.normalize_unc_path(path) if TOOL_OPEN_AVAILABLE else path
    if not os.path.isdir(normalized_path):
        return jsonify({"success": False, "message": "Thư mục không tồn tại hoặc server không truy cập được"}), 404
    if os.name != 'nt':
        return jsonify({"success": False, "message": "Chỉ hỗ trợ mở Windows Explorer trên Windows"}), 400

    try:
        if _should_skip_recent_explorer_open(normalized_path):
            return jsonify({
                "success": True,
                "folder_name": os.path.basename(normalized_path),
                "path": normalized_path,
                "skipped_duplicate": True
            })
        _open_folder_reusing_explorer(normalized_path)
        return jsonify({
            "success": True,
            "folder_name": os.path.basename(normalized_path),
            "path": normalized_path
        })
    except OSError as e:
        return jsonify({"success": False, "message": f"Không mở được Windows Explorer: {e}"}), 500


def _should_skip_recent_explorer_open(path):
    time_module = __import__('time')
    threading_module = __import__('threading')
    lock = getattr(_should_skip_recent_explorer_open, '_lock', None)
    if lock is None:
        lock = threading_module.Lock()
        setattr(_should_skip_recent_explorer_open, '_lock', lock)

    key = os.path.normcase(os.path.abspath(path))
    now = time_module.monotonic()
    with lock:
        state = getattr(_should_skip_recent_explorer_open, '_state', {})
        last_opened_at = state.get(key, 0)
        if now - last_opened_at < 3.0:
            return True
        state[key] = now
        setattr(_should_skip_recent_explorer_open, '_state', state)
    return False


def _open_folder_reusing_explorer(path):
    script = """
$Target = $args[0]
$ErrorActionPreference = 'Stop'
$shell = New-Object -ComObject Shell.Application
$windows = @($shell.Windows() | Where-Object {
    try { [System.IO.Path]::GetFileName($_.FullName).ToLowerInvariant() -eq 'explorer.exe' } catch { $false }
})
if ($windows.Count -gt 0) {
    $windows[0].Navigate2($Target)
    $windows[0].Visible = $true
} else {
    Start-Process explorer.exe -ArgumentList $Target
}
"""
    subprocess_module = __import__('subprocess')
    try:
        completed = subprocess_module.run(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", script, path],
            timeout=5,
            check=False,
            stdout=subprocess_module.DEVNULL,
            stderr=subprocess_module.DEVNULL,
        )
        if completed.returncode != 0:
            os.startfile(path)
    except OSError:
        os.startfile(path)
    except subprocess_module.TimeoutExpired:
        os.startfile(path)


# ========================================================================
