# -*- coding: utf-8 -*-
"""
Ollama AI Routes - Tách từ server.py
Bao gồm các endpoints:
- /api/ollama-test
- /api/ollama/<path> (proxy endpoint)
- /api/ollama-models
- /api/ollama-status
- /api/ollama/chat/stream
"""

def register_routes(app, config):
    """Register Ollama AI routes with Flask app"""
    from flask import request, jsonify, make_response, Response
    import requests
    import json
    import os
    
    # Import necessary modules
    from src.chat_service import get_context_for_ai, detect_search_intent, search_for_ai_context
    from src.system_prompt import DEFAULT_SYSTEM_PROMPT
    
    # Get config values
    sessions = config.get('sessions')
    sessions_lock = config.get('sessions_lock')
    OLLAMA_URL = config.get('OLLAMA_URL', 'http://localhost:11434')
    OLLAMA_ENABLED = config.get('OLLAMA_ENABLED', True)
    SYSTEM_PROMPT = config.get('SYSTEM_PROMPT', DEFAULT_SYSTEM_PROMPT)
    safe_print = config.get('safe_print', print)
    
    # Default Ollama URLs
    DEFAULT_OLLAMA_URLS = [
        'http://localhost:11434',
        'http://127.0.0.1:11434',
        'http://0.0.0.0:11434',
    ]
    
    # ========== Ollama Test Endpoint ==========
    @app.route('/api/ollama-test', methods=['POST', 'OPTIONS'])
    def ollama_test():
        """Test endpoint to diagnose Ollama issues"""
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        data = request.get_json() or {}
        prompt = data.get('prompt', 'Hello')
        model = data.get('model', 'qwen3:8b')
        
        safe_print(f"[Ollama Test] Received request - model: {model}, prompt: {prompt}")
        safe_print(f"[Ollama Test] OLLAMA_URL: {OLLAMA_URL}")
        safe_print(f"[Ollama Test] Request from IP: {request.remote_addr}")
        
        # Try to call Ollama directly
        try:
            target_url = f"{OLLAMA_URL}/api/generate"
            safe_print(f"[Ollama Test] Calling: {target_url}")
            
            resp = requests.post(
                target_url,
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            
            safe_print(f"[Ollama Test] Response status: {resp.status_code}")
            safe_print(f"[Ollama Test] Response body: {resp.text[:200]}")
            
            if resp.ok:
                return jsonify({
                    "success": True,
                    "status_code": resp.status_code,
                    "response": resp.json()
                })
            else:
                return jsonify({
                    "success": False,
                    "status_code": resp.status_code,
                    "error": resp.text,
                    "ollama_url": OLLAMA_URL
                }), resp.status_code
                
        except Exception as e:
            safe_print(f"[Ollama Test] Exception: {e}")
            return jsonify({
                "success": False,
                "error": str(e),
                "ollama_url": OLLAMA_URL
            }), 500

    # ========== Ollama Proxy Endpoint ==========
    @app.route('/api/ollama/<path:ollama_path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    def ollama_proxy(ollama_path):
        """Proxy requests to Ollama server with improved error handling"""
        # Handle OPTIONS preflight
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, PUT, DELETE, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        if not OLLAMA_ENABLED:
            return jsonify({
                "error": "Ollama đang tắt. Vui lòng bật Ollama server.",
                "hint": "Chạy 'ollama serve' để khởi động Ollama"
            }), 503
        
        # Log ALL requests for debugging
        safe_print(f"="*50)
        safe_print(f"[Ollama Proxy] NEW REQUEST:")
        safe_print(f"  Path: {ollama_path}")
        safe_print(f"  Method: {request.method}")
        safe_print(f"  Remote IP: {request.remote_addr}")
        safe_print(f"  Host: {request.host}")
        safe_print(f"  Origin: {request.headers.get('Origin', 'N/A')}")
        safe_print(f"  User-Agent: {request.headers.get('User-Agent', 'N/A')[:50]}")
        
        try:
            # Build the target URL
            target_url = f"{OLLAMA_URL}/{ollama_path}"
            safe_print(f"[Ollama Proxy] Forwarding to: {target_url}")
            
            # Get headers from original request
            headers = {key: value for key, value in request.headers if key.lower() != 'host'}
            safe_print(f"[Ollama Proxy] Headers: {headers}")
            
            # Get request body for logging
            request_body = request.get_data()
            safe_print(f"[Ollama Proxy] Body length: {len(request_body)} bytes")
            
            # Handle different methods
            if request.method == 'GET':
                resp = requests.get(target_url, headers=headers, timeout=30)
            elif request.method == 'POST':
                resp = requests.post(
                    target_url, 
                    headers=headers, 
                    json=request.get_json(), 
                    timeout=120
                )
            elif request.method == 'PUT':
                resp = requests.put(
                    target_url, 
                    headers=headers, 
                    json=request.get_json(), 
                    timeout=120
                )
            elif request.method == 'DELETE':
                resp = requests.delete(target_url, headers=headers, timeout=30)
            else:
                return jsonify({"error": "Method not allowed"}), 405
            
            # Log the response status
            safe_print(f"[Ollama Proxy] Response status: {resp.status_code}")
            safe_print(f"[Ollama Proxy] Response headers: {dict(resp.headers)}")
            
            # Debug: Log full request and response for troubleshooting
            if resp.status_code >= 400:
                safe_print(f"[Ollama Proxy] FULL REQUEST DEBUG:")
                safe_print(f"  Target URL: {target_url}")
                safe_print(f"  Request method: {request.method}")
                safe_print(f"  Request headers: {dict(request.headers)}")
                safe_print(f"  Request body: {request.get_json()}")
                safe_print(f"  Response status: {resp.status_code}")
                safe_print(f"  Response body: {resp.text[:500]}")
            
            # If Ollama returns error status, provide helpful message
            if resp.status_code >= 400:
                error_msg = f"Ollama server trả về lỗi {resp.status_code}"
                error_details = {}
                
                try:
                    error_data = resp.json()
                    if 'error' in error_data:
                        error_msg = f"Ollama: {error_data['error']}"
                        error_details['ollama_error'] = error_data['error']
                except:
                    pass
                
                # Provide specific guidance for 403 Forbidden
                if resp.status_code == 403:
                    safe_print(f"[Ollama Proxy] 403 Forbidden - Access denied to Ollama at {OLLAMA_URL}")
                    try:
                        error_data = resp.json()
                        ollama_error = error_data.get('error', '')
                    except:
                        ollama_error = ''
                    
                    return jsonify({
                        "error": "Ollama server từ chối truy cập (403 Forbidden)",
                        "ollama_url": OLLAMA_URL,
                        "ollama_error": ollama_error,
                        "hint": "Có thể do: (1) Ollama chưa được cấu hình cho phép remote access, (2) IP bị chặn, (3) Cần thiết lập OLLAMA_HOST=0.0.0.0:11434 khi chạy Ollama",
                        "fix_instructions": "Để cho phép remote access, hãy chạy:\n• Windows: set OLLAMA_HOST=0.0.0.0:11434 && ollama serve\n• Linux/Mac: export OLLAMA_HOST=0.0.0.0:11434 && ollama serve\n\nHoặc thêm vào config: { \"host\": \"0.0.0.0:11434\" }",
                        "debug_info": {
                            "target_url": target_url,
                            "response_status": resp.status_code,
                            "ollama_host_env": os.environ.get('OLLAMA_HOST', 'not set'),
                            "ollama_url_env": os.environ.get('OLLAMA_URL', 'not set')
                        },
                        "details": error_details
                    }), 403
                
                # Provide specific guidance for connection issues
                if resp.status_code == 503:
                    safe_print(f"[Ollama Proxy] 503 Service Unavailable - Ollama may not be running")
                    return jsonify({
                        "error": "Ollama server không khả dụng (503)",
                        "ollama_url": OLLAMA_URL,
                        "hint": "Vui lòng khởi động Ollama bằng lệnh 'ollama serve' trong terminal",
                        "details": error_details
                    }), 503
                
                return jsonify({
                    "error": error_msg,
                    "ollama_url": OLLAMA_URL,
                    "hint": "Vui lòng kiểm tra Ollama server có đang chạy không",
                    "details": error_details
                }), resp.status_code
            
            # Return the response from Ollama
            response = make_response(resp.content, resp.status_code)
            response.headers['Content-Type'] = resp.headers.get('Content-Type', 'application/json')
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
            
        except requests.exceptions.ConnectionError as e:
            safe_print(f"[Ollama Proxy] Connection error: {e}")
            ollama_host_env = os.environ.get('OLLAMA_HOST', 'not set')
            ollama_url_env = os.environ.get('OLLAMA_URL', 'not set')
            
            return jsonify({
                "error": "Không thể kết nối đến Ollama server",
                "ollama_url": OLLAMA_URL,
                "details": str(e),
                "hint": "Vui lòng đảm bảo Ollama đang chạy (thường là localhost:11434). \n\nĐể khởi động Ollama, hãy chạy lệnh 'ollama serve' trong terminal.\n\nĐể cho phép remote access, hãy thiết lập:\n• Windows: set OLLAMA_HOST=0.0.0.0:11434\n• Linux/Mac: export OLLAMA_HOST=0.0.0.0:11434",
                "debug_info": {
                    "target_url": target_url,
                    "ollama_host_env": ollama_host_env,
                    "ollama_url_env": ollama_url_env,
                    "troubleshooting": "Kiểm tra: (1) Ollama đang chạy, (2) Firewall không chặn, (3) Đúng port 11434"
                }
            }), 503
        except requests.exceptions.Timeout:
            safe_print(f"[Ollama Proxy] Timeout")
            return jsonify({
                "error": "Yêu cầu Ollama hết thời gian chờ",
                "hint": "Model có thể đang tải, vui lòng thử lại sau. Nếu vẫn lỗi, hãy thử model nhẹ hơn."
            }), 504
        except Exception as e:
            safe_print(f"[Ollama Proxy] Error: {e}")
            return jsonify({
                "error": f"Lỗi proxy Ollama: {str(e)}",
                "hint": "Liên hệ admin nếu lỗi tiếp tục"
            }), 500

    # ========== Ollama Models Endpoint ==========
    @app.route('/api/ollama-models', methods=['GET', 'OPTIONS'])
    def ollama_models():
        """Get available Ollama models"""
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        if not OLLAMA_ENABLED:
            return jsonify({
                "error": "Ollama đang tắt",
                "models": [],
                "hint": "Bật Ollama server để sử dụng tính năng AI"
            }), 200
        
        try:
            safe_print(f"[Ollama] Checking models at {OLLAMA_URL}")
            resp = requests.get(f"{OLLAMA_URL}/api/tags", timeout=10)
            
            if resp.status_code >= 400:
                safe_print(f"[Ollama] Error getting models: {resp.status_code}")
                return jsonify({
                    "error": f"Ollama server lỗi: {resp.status_code}",
                    "models": [],
                    "hint": "Kiểm tra Ollama đang chạy"
                }), 200
            
            response = make_response(resp.content, resp.status_code)
            response.headers['Content-Type'] = resp.headers.get('Content-Type', 'application/json')
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
        except requests.exceptions.ConnectionError as e:
            safe_print(f"[Ollama] Connection failed: {e}")
            return jsonify({
                "error": "Không thể kết nối Ollama server",
                "models": [],
                "ollama_url": OLLAMA_URL,
                "hint": "Vui lòng chạy 'ollama serve' để khởi động Ollama"
            }), 200
        except Exception as e:
            safe_print(f"[Ollama] Error: {e}")
            return jsonify({
                "error": str(e),
                "models": []
            }), 200

    # ========== Ollama Status Endpoint ==========
    @app.route('/api/ollama-status', methods=['GET', 'POST', 'OPTIONS'])
    def ollama_status():
        """Get or set Ollama configuration with detailed status"""
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
            return response
        
        ollama_url = OLLAMA_URL
        ollama_enabled = OLLAMA_ENABLED
        
        if request.method == 'POST':
            data = request.get_json()
            if data:
                if 'url' in data:
                    url = data['url']
                    if not url.startswith('http'):
                        url = f'http://{url}'
                    ollama_url = url
                    config['OLLAMA_URL'] = url
                    safe_print(f"[Ollama] URL updated to: {ollama_url}")
                if 'enabled' in data:
                    ollama_enabled = data['enabled']
                    config['OLLAMA_ENABLED'] = data['enabled']
                    safe_print(f"[Ollama] Enabled: {ollama_enabled}")
            
            return jsonify({
                "success": True,
                "url": ollama_url,
                "enabled": ollama_enabled
            })
        
        # GET - check status with detailed information
        can_connect = False
        error_msg = None
        tried_urls = []
        
        # Try current URL first
        try:
            resp = requests.get(f"{ollama_url}/api/tags", timeout=5)
            can_connect = resp.ok
            tried_urls.append({
                "url": ollama_url,
                "status": "success" if resp.ok else f"error_{resp.status_code}",
                "status_code": resp.status_code
            })
        except Exception as e:
            error_msg = str(e)
            tried_urls.append({
                "url": ollama_url,
                "status": "connection_failed",
                "error": str(e)
            })
        
        # If current URL fails, try others for discovery
        if not can_connect:
            for url in DEFAULT_OLLAMA_URLS:
                if url == ollama_url:
                    continue
                try:
                    resp = requests.get(f"{url}/api/tags", timeout=3)
                    tried_urls.append({
                        "url": url,
                        "status": "success" if resp.ok else f"error_{resp.status_code}",
                        "status_code": resp.status_code
                    })
                    if resp.ok and not can_connect:
                        safe_print(f"[Ollama] Found working URL: {url}")
                except Exception as e:
                    tried_urls.append({
                        "url": url,
                        "status": "connection_failed",
                        "error": str(e)
                    })
        
        return jsonify({
            "url": ollama_url,
            "enabled": ollama_enabled,
            "connected": can_connect,
            "error": error_msg,
            "tried_urls": tried_urls,
            "environment": {
                "OLLAMA_HOST": os.environ.get('OLLAMA_HOST', 'not set'),
                "OLLAMA_URL": os.environ.get('OLLAMA_URL', 'not set')
            },
            "fix_instructions": "Để cho phép remote access, hãy chạy:\n• Windows: set OLLAMA_HOST=0.0.0.0:11434 && ollama serve\n• Linux/Mac: export OLLAMA_HOST=0.0.0.0:11434 && ollama serve"
        })

    # ========== Ollama Chat Stream Endpoint ==========
    @app.route('/api/ollama/chat/stream', methods=['POST', 'OPTIONS'])
    def ollama_chat_stream():
        """Chat với Ollama với Streaming (SSE)"""
        
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        if not OLLAMA_ENABLED:
            return Response(
                f"data: {json.dumps({'error': 'Ollama đang tắt. Vui lòng bật Ollama server.'})}\n\n",
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Access-Control-Allow-Origin': '*'
                }
            )
        
        data = request.get_json() or {}
        message = data.get('message', '')
        model = data.get('model', 'llama3.2:latest')
        history = data.get('history', [])
        stream_option = data.get('stream', True)
        session_id = data.get('session_id', '')
        
        # Get user info from token
        auth_header = request.headers.get('Authorization', '')
        user_info_str = ''
        user_id = None
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            with sessions_lock:
                session_data = sessions.get(token)
                if session_data:
                    user = session_data.get('user', {})
                    user_id = user.get('user_id')
                    user_info_str = f"""
## THÔNG TIN USER HIỆN TẠI
- Username: {user.get('username', 'unknown')}
- Role: {user.get('role', 'unknown')}
- Full Name: {user.get('full_name', '')}
- User ID: {user.get('user_id', '')}

Lưu ý: Đây là user đang sử dụng AI. Nếu họ hỏi về dự án của họ, hãy:
- Nếu là Sales: Xem projects với user_id = {user.get('user_id', '')}
- Nếu là Engineer: Xem projects với accepted_by = '{user.get('username', '')}'"
"""
        
        # Get AI context from database if session_id provided
        ai_context_str = ''
        if session_id and user_id:
            try:
                ai_context_str = get_context_for_ai(session_id, user_id)
                if ai_context_str:
                    safe_print(f"[Ollama Stream] Loaded context for session: {session_id}")
            except Exception as e:
                safe_print(f"[Ollama Stream] Error loading context: {e}")
        
        # Detect search intent and auto-search cross-session context
        cross_session_context = ''
        if user_id and message:
            try:
                should_search, keywords = detect_search_intent(message)
                if should_search and keywords:
                    safe_print(f"[Ollama Stream] Detected search intent in message, searching for: {keywords[:50]}...")
                    cross_session_context = search_for_ai_context(user_id, keywords, limit=5)
                    if cross_session_context:
                        safe_print(f"[Ollama Stream] Found cross-session context, length: {len(cross_session_context)}")
            except Exception as e:
                safe_print(f"[Ollama Stream] Error in cross-session search: {e}")
        
        if not message:
            return Response(
                f"data: {json.dumps({'error': 'Tin nhắn không được để trống'})}\n\n",
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Access-Control-Allow-Origin': '*'
                }
            )
        
        def generate_stream():
            try:
                # 1. Gửi status: SENDING
                yield f"data: {json.dumps({'type': 'status', 'value': 'sending'})}\n\n"
                
                # Build prompt from history + current message
                base_system = SYSTEM_PROMPT + user_info_str
                if ai_context_str:
                    base_system = base_system + "\n\n" + ai_context_str
                if cross_session_context:
                    base_system = base_system + "\n\n" + cross_session_context
                
                prompt_parts = [f"System: {base_system}"]
                for msg in history:
                    role = msg.get('role', 'user')
                    content = msg.get('content', '')
                    if role == 'user':
                        prompt_parts.append(f"User: {content}")
                    else:
                        prompt_parts.append(f"Assistant: {content}")
                
                prompt_parts.append(f"User: {message}")
                full_prompt = "\n".join(prompt_parts)
                
                safe_print(f"[Ollama Stream] Model: {model}")
                
                # Use the streaming API endpoint of Ollama
                target_url = f"{OLLAMA_URL}/api/generate"
                
                # Send initial ping
                yield f"data: {json.dumps({'type': 'start'})}\n\n"
                
                # 2. Gửi status: THINKING
                yield f"data: {json.dumps({'type': 'status', 'value': 'thinking'})}\n\n"
                
                # Call Ollama with streaming
                resp = requests.post(
                    target_url,
                    json={
                        "model": model,
                        "prompt": full_prompt,
                        "stream": True
                    },
                    stream=True,
                    timeout=120
                )
                
                if resp.status_code >= 400:
                    safe_print(f"[Ollama Stream] Error: {resp.status_code} - {resp.text}")
                    yield f"data: {json.dumps({'error': f'Lỗi API: {resp.status_code}', 'details': resp.text[:500]})}\n\n"
                    return
                
                # Process streaming response from Ollama
                full_response = ""
                
                # 3. Gửi status: STREAMING
                yield f"data: {json.dumps({'type': 'status', 'value': 'streaming'})}\n\n"
                
                for line in resp.iter_lines():
                    if line:
                        try:
                            data_json = json.loads(line.decode('utf-8'))
                            
                            if 'response' in data_json:
                                chunk = data_json['response']
                                full_response += chunk
                                yield f"data: {json.dumps({'type': 'chunk', 'content': chunk, 'full': full_response})}\n\n"
                            
                            if data_json.get('done', False):
                                break
                                
                        except json.JSONDecodeError:
                            continue
                
                # 4. Gửi status: DONE
                yield f"data: {json.dumps({'type': 'status', 'value': 'done'})}\n\n"
                
                # Send completion
                yield f"data: {json.dumps({'type': 'done', 'full': full_response})}\n\n"
                
            except requests.exceptions.ConnectionError as e:
                safe_print(f"[Ollama Stream] Connection error: {e}")
                yield f"data: {json.dumps({'type': 'status', 'value': 'error'})}\n\n"
                yield f"data: {json.dumps({'error': f'Không thể kết nối đến Ollama: {str(e)}'})}\n\n"
            except Exception as e:
                safe_print(f"[Ollama Stream] Exception: {e}")
                yield f"data: {json.dumps({'type': 'status', 'value': 'error'})}\n\n"
                yield f"data: {json.dumps({'error': str(e)})}\n\n"
        
        return Response(
            generate_stream(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Content-Type'
            }
        )
    
    print("[Ollama Routes] Registered successfully")
