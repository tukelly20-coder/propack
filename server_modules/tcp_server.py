# TCP Socket Server for Legacy Client V7
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
        
        # Process request using the same logic as HTTP /api/socket
        # Import the global variables needed
        global db_data, cached_sorted_history, history_version, used_codes, history
        
        response_data = None
        
        # ==================== DB Operations ====================
        if request_type == "GET_DB_ALL":
            db_data = load_all()
            response_data = db_data
            
        elif request_type == "GET_DB_PROJECT":
            tracking_id = request.get('tracking_id')
            project = get_record_by_id(tracking_id)
            response_data = project
            
        elif request_type == "GET_DB_PAGED":
            page = request.get('page', 1)
            limit = request.get('limit', 50)
            sort_by = request.get('sort_by', 'Tracking ID')
            sort_order = request.get('sort_order', 'asc')
            result = get_paged_data_sql(page, limit, sort_by, sort_order)
            response_data = result
            
        elif request_type == "ADD_DB_RECORD":
            record = request.get('record', {})
            tracking_id = max([r.get("Tracking ID", 0) for r in db_data] + [0]) + 1
            record["Tracking ID"] = tracking_id
            db_data.append(record)
            save_all(db_data)
            response_data = {"success": True, "record": record}
            
        elif request_type == "UPDATE_DB_RECORD":
            tracking_id = request.get('tracking_id')
            new_data = request.get('data', {})
            success = update_record(tracking_id, new_data)
            response_data = {"success": success}
            
        elif request_type == "DELETE_DB_RECORDS":
            user_role = request.get('user_role')
            tracking_ids = request.get('tracking_ids', [])
            
            if user_role != 'admin':
                response_data = {"success": False, "error": "Bạn không có quyền xóa"}
            else:
                deleted_count = delete_records(tracking_ids)
                response_data = {"success": True, "deleted_count": deleted_count}
                
        elif request_type == "SEARCH_DB_DATA":
            search_text = request.get('search_text', '')
            columns = request.get('columns', [])
            results = db_search_data(db_data, search_text, columns)
            response_data = results
            
        elif request_type == "FILTER_DB_DATA":
            column_filters = request.get('filters', {})
            results = db_filter_data(db_data, column_filters)
            response_data = results
            
        # ==================== User Operations ====================
        elif request_type == "DB_LOGIN":
            username = request.get('username', '').strip()
            password = request.get('password', '')
            
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
            user_data = request.get('user_data', {})
            user_id = add_user(user_data)
            if user_id:
                assign_default_permissions(user_id, user_data.get('role', 'sales'))
                response_data = {"success": True, "user_id": user_id}
            else:
                response_data = {"success": False, "error": "Username already exists"}
                
        elif request_type == "UPDATE_USER":
            user_id = request.get('user_id')
            user_data = request.get('user_data', {})
            success = update_user(user_id, user_data)
            if 'permissions' in user_data:
                set_user_permissions(user_id, user_data['permissions'])
            response_data = {"success": success}
            
        elif request_type == "DELETE_USER":
            user_id = request.get('user_id')
            success = delete_user(user_id)
            response_data = {"success": success}
            
        # ==================== Notice/Pending Operations ====================
        elif request_type == "GET_PENDING_NOTICES":
            user_id = request.get('user_id')
            notices = get_pending_notices(user_id)
            response_data = notices
            
        elif request_type == "GET_PENDING_COUNT":
            user_id = request.get('user_id')
            count = get_pending_count(user_id)
            response_data = {"count": count}
            
        elif request_type == "ACCEPT_JOB":
            tracking_id = request.get('tracking_id')
            engineer_name = request.get('engineer_name')
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
            record_data = request.get('record', {})
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
            user_id = request.get('user_id')
            projects = get_projects_by_user(user_id)
            response_data = projects
            
        elif request_type == "GET_ENGINEER_JOBS":
            engineer_name = request.get('engineer_name')
            projects = get_accepted_projects_by_engineer(engineer_name)
            response_data = projects
            
        elif request_type == "GET_ALL_NOTICES_FOR_ENGINEER":
            engineer_name = request.get('engineer_name')
            notices = get_all_notices_for_engineer(engineer_name)
            response_data = notices
            
        # ==================== Code Generation ====================
        elif request_type == "REQUEST_CODE":
            name = request.get('name', '').strip()
            category = request.get('category', '')
            employee = request.get('employee', '').strip()
            
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
                        save_data_data(used_codes, history)
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


def run_tcp_server(port):
    """Run TCP socket server on specified port for legacy V7 client"""
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_socket.bind(('0.0.0.0', port))
    server_socket.listen(5)
    safe_print(f"[TCP] Server listening on port {port}")
    
    while True:
        try:
            client_socket, client_address = server_socket.accept()
            safe_print(f"[TCP] Client connected from {client_address}")
            # Handle each client in a separate thread
            client_thread = threading.Thread(target=handle_tcp_client, args=(client_socket, client_address), daemon=True)
            client_thread.start()
        except Exception as e:
            safe_print(f"[TCP] Error accepting connection: {e}")
            break


def print_startup_banner(http_port=8001, tcp_port=12345):
    border = '=' * 72
    safe_print(border)
    safe_print('Unified Server | Multi-Port Runtime')
    safe_print(border)
    safe_print(f"[HTTP] Web UI        : http://localhost:{http_port}")
    safe_print(f"[HTTP] REST API      : http://localhost:{http_port}/api/projects")
    safe_print(f"[HTTP] Login         : http://localhost:{http_port}/api/login")
    safe_print(f"[HTTP] Tool Open API : http://localhost:{http_port}/api/tool-search")
    safe_print(f"[TCP ] Legacy Socket : localhost:{tcp_port}")
    safe_print(
        f"[LOG ] level={os.getenv('SERVER_LOG_LEVEL', 'INFO').upper()} "
        f"requests={'on' if REQUEST_LOG_ENABLED else 'off'} "
        f"static={'on' if STATIC_LOG_ENABLED else 'off'}"
    )
    safe_print(border)


# ========================================================================
# Run Server on Multiple Ports (8001 and 12345)
# ========================================================================

if __name__ == '__main__':
    import threading
    import time

    print_startup_banner(http_port=8001, tcp_port=12345)
    
    # Run Flask HTTP server on port 8001
    def run_http_server(port):
        """Run Flask server on specified port"""
        app.run(host='0.0.0.0', port=port, debug=False, threaded=True, use_reloader=False)
    
    # Start HTTP server on port 8001
    http_thread = threading.Thread(target=run_http_server, args=(8001,), daemon=True)
    http_thread.start()
    time.sleep(0.5)
    
    # Start TCP socket server on port 12345 (for legacy V7 client)
    tcp_thread = threading.Thread(target=run_tcp_server, args=(12345,), daemon=True)
    tcp_thread.start()

    safe_print("[System] Servers started successfully")
    
    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        safe_print("[System] Shutting down servers...")
