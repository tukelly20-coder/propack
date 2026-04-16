# -*- coding: utf-8 -*-
"""
Gemini AI Routes - Tách từ server.py
Bao gồm các endpoints:
- /api/gemini/chat
- /api/gemini/chat/stream
- /api/gemini/models
- /api/gemini/status
- /api/gemini/config
"""

def register_routes(app, config):
    """Register Gemini AI routes with Flask app"""
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
    GEMINI_API_KEY = config.get('GEMINI_API_KEY')
    GEMINI_MODEL = config.get('GEMINI_MODEL', 'gemini-3-flash-preview')
    SYSTEM_PROMPT = config.get('SYSTEM_PROMPT', DEFAULT_SYSTEM_PROMPT)
    safe_print = config.get('safe_print', print)
    
    # ========== Gemini Chat Endpoint ==========
    @app.route('/api/gemini/chat', methods=['POST', 'OPTIONS'])
    def gemini_chat():
        """Chat với Gemini AI"""
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        if not GEMINI_API_KEY:
            return jsonify({
                "success": False,
                "error": "Chưa cấu hình Gemini API Key"
            }), 500
        
        data = request.get_json() or {}
        message = data.get('message', '')
        model = data.get('model', GEMINI_MODEL)
        history = data.get('history', [])
        
        # Get user info from token (Authorization header)
        auth_header = request.headers.get('Authorization', '')
        user_info_str = ''
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            with sessions_lock:
                session_data = sessions.get(token)
                if session_data:
                    user = session_data.get('user', {})
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
        
        if not message:
            return jsonify({
                "success": False,
                "error": "Tin nhắn không được để trống"
            }), 400
        
        try:
            # Build messages for Gemini API
            system_instruction_text = SYSTEM_PROMPT + user_info_str
            
            system_instruction = {
                "role": "user",
                "parts": [{"text": system_instruction_text}]
            }
            contents = [system_instruction]
            
            # Add history messages
            for msg in history:
                role = msg.get('role', 'user')
                if role == 'user':
                    contents.append({
                        "role": "user",
                        "parts": [{"text": msg.get('content', '')}]
                    })
                else:  # model
                    contents.append({
                        "role": "model",
                        "parts": [{"text": msg.get('content', '')}]
                    })
            
            # Add current message
            contents.append({
                "role": "user",
                "parts": [{"text": message}]
            })
            
            # Call Gemini API
            safe_print(f"[Gemini] Calling model: {model}")
            
            gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
            
            headers = {
                'Content-Type': 'application/json'
            }
            
            payload = {
                "contents": contents,
                "generationConfig": {
                    "temperature": 0.9,
                    "maxOutputTokens": 2048,
                    "topP": 0.95,
                    "topK": 40
                }
            }
            
            resp = requests.post(gemini_url, headers=headers, json=payload, timeout=60)
            
            if resp.status_code >= 400:
                safe_print(f"[Gemini] Error: {resp.status_code} - {resp.text}")
                return jsonify({
                    "success": False,
                    "error": f"Lỗi API: {resp.status_code}",
                    "details": resp.text
                }), resp.status_code
            
            result = resp.json()
            
            # Extract response text
            response_text = ""
            if 'candidates' in result and len(result['candidates']) > 0:
                candidate = result['candidates'][0]
                if 'content' in candidate and 'parts' in candidate['content']:
                    parts = candidate['content']['parts']
                    response_text = "\n".join([p.get('text', '') for p in parts])
            
            if not response_text:
                response_text = "Không có phản hồi từ AI"
            
            return jsonify({
                "success": True,
                "response": response_text,
                "model": model
            })
            
        except Exception as e:
            safe_print(f"[Gemini] Exception: {e}")
            return jsonify({
                "success": False,
                "error": f"Lỗi: {str(e)}"
            }), 500

    # ========== Gemini Chat Stream Endpoint ==========
    @app.route('/api/gemini/chat/stream', methods=['POST', 'OPTIONS'])
    def gemini_chat_stream():
        """Chat với Gemini AI với Streaming (SSE)"""
        
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        if not GEMINI_API_KEY:
            return Response(
                f"data: {json.dumps({'error': 'Chưa cấu hình Gemini API Key'})}\n\n",
                mimetype='text/event-stream',
                headers={
                    'Cache-Control': 'no-cache',
                    'Access-Control-Allow-Origin': '*'
                }
            )
        
        data = request.get_json() or {}
        message = data.get('message', '')
        model = data.get('model', GEMINI_MODEL)
        history = data.get('history', [])
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
                    safe_print(f"[Gemini Stream] Loaded context for session: {session_id}")
            except Exception as e:
                safe_print(f"[Gemini Stream] Error loading context: {e}")
        
        # Detect search intent and auto-search cross-session context
        cross_session_context = ''
        if user_id and message:
            try:
                should_search, keywords = detect_search_intent(message)
                if should_search and keywords:
                    safe_print(f"[Gemini Stream] Detected search intent in message, searching for: {keywords[:50]}...")
                    cross_session_context = search_for_ai_context(user_id, keywords, limit=5)
                    if cross_session_context:
                        safe_print(f"[Gemini Stream] Found cross-session context, length: {len(cross_session_context)}")
            except Exception as e:
                safe_print(f"[Gemini Stream] Error in cross-session search: {e}")
        
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
                
                # Build messages for Gemini API
                system_instruction = {
                    "role": "user",
                    "parts": [{"text": SYSTEM_PROMPT + user_info_str}]
                }
                contents = [system_instruction]
                
                # Add history messages
                for msg in history:
                    role = msg.get('role', 'user')
                    if role == 'user':
                        contents.append({
                            "role": "user",
                            "parts": [{"text": msg.get('content', '')}]
                        })
                    else:  # model
                        contents.append({
                            "role": "model",
                            "parts": [{"text": msg.get('content', '')}]
                        })
                
                # Add current message
                contents.append({
                    "role": "user",
                    "parts": [{"text": message}]
                })
                
                safe_print(f"[Gemini Stream] Calling model: {model}")
                
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={GEMINI_API_KEY}"
                
                headers = {
                    'Content-Type': 'application/json'
                }
                
                payload = {
                    "contents": contents,
                    "generationConfig": {
                        "temperature": 0.9,
                        "maxOutputTokens": 2048,
                        "topP": 0.95,
                        "topK": 40
                    }
                }
                
                # Send initial ping
                yield f"data: {json.dumps({'type': 'start'})}\n\n"
                
                # 2. Gửi status: THINKING
                yield f"data: {json.dumps({'type': 'status', 'value': 'thinking'})}\n\n"
                
                resp = requests.post(gemini_url, headers=headers, json=payload, timeout=120)
                
                if resp.status_code >= 400:
                    safe_print(f"[Gemini Stream] Error: {resp.status_code} - {resp.text}")
                    yield f"data: {json.dumps({'type': 'status', 'value': 'error'})}\n\n"
                    yield f"data: {json.dumps({'error': f'Lỗi API: {resp.status_code}', 'details': resp.text[:500]})}\n\n"
                    return
                
                result = resp.json()
                
                # Extract response text
                response_text = ""
                if 'candidates' in result and len(result['candidates']) > 0:
                    candidate = result['candidates'][0]
                    if 'content' in candidate and 'parts' in candidate['content']:
                        parts = candidate['content']['parts']
                        response_text = "\n".join([p.get('text', '') for p in parts])
                
                if not response_text:
                    response_text = "Không có phản hồi từ AI"
                
                # 3. Gửi status: STREAMING
                yield f"data: {json.dumps({'type': 'status', 'value': 'streaming'})}\n\n"
                
                # Simulate streaming by sending in chunks
                chunk_size = 20
                for i in range(0, len(response_text), chunk_size):
                    chunk = response_text[i:i + chunk_size]
                    yield f"data: {json.dumps({'type': 'chunk', 'content': chunk, 'full': response_text})}\n\n"
                
                # 4. Gửi status: DONE
                yield f"data: {json.dumps({'type': 'status', 'value': 'done'})}\n\n"
                
                # Send completion
                yield f"data: {json.dumps({'type': 'done', 'full': response_text})}\n\n"
                
            except Exception as e:
                safe_print(f"[Gemini Stream] Exception: {e}")
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

    # ========== Gemini Models Endpoint ==========
    @app.route('/api/gemini/models', methods=['GET', 'OPTIONS'])
    def gemini_models():
        """Lấy danh sách models Gemini"""
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        if not GEMINI_API_KEY:
            return jsonify({
                "success": False,
                "error": "Chưa cấu hình Gemini API Key",
                "models": []
            }), 200
        
        # Return available Gemini models
        models = [
            {"name": "gemini-3-flash-preview", "display": "Gemini 3.0 Flash Preview (Nhanh nhất)"},
            {"name": "gemini-2.0-flash", "display": "Gemini 2.0 Flash"},
            {"name": "gemini-1.5-flash", "display": "Gemini 1.5 Flash"},
            {"name": "gemini-1.5-pro", "display": "Gemini 1.5 Pro"}
        ]
        
        return jsonify({
            "success": True,
            "models": models,
            "current_model": GEMINI_MODEL
        })

    # ========== Gemini Status Endpoint ==========
    @app.route('/api/gemini/status', methods=['GET', 'OPTIONS'])
    def gemini_status():
        """Kiểm tra trạng thái Gemini API"""
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        has_key = bool(GEMINI_API_KEY)
        
        # Test connection if API key exists
        connected = False
        error_msg = None
        
        if has_key:
            try:
                # Quick test with a minimal request
                gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{GEMINI_MODEL}:generateContent?key={GEMINI_API_KEY}"
                resp = requests.post(
                    gemini_url,
                    headers={'Content-Type': 'application/json'},
                    json={"contents": [{"role": "user", "parts": [{"text": "test"}]}]},
                    timeout=10
                )
                connected = resp.status_code < 400
                if not connected:
                    error_msg = f"HTTP {resp.status_code}"
            except Exception as e:
                error_msg = str(e)
        
        return jsonify({
            "success": True,
            "configured": has_key,
            "connected": connected,
            "model": GEMINI_MODEL,
            "error": error_msg
        })

    # ========== Gemini Config Endpoint ==========
    @app.route('/api/gemini/config', methods=['POST', 'OPTIONS'])
    def gemini_config():
        """Cấu hình Gemini API (update API key or model)"""
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        # Update global config via config dict
        gemini_api_key = GEMINI_API_KEY
        gemini_model = GEMINI_MODEL
        
        data = request.get_json() or {}
        
        if 'api_key' in data:
            gemini_api_key = data['api_key']
            # Save to credentials.json
            try:
                cred_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'credentials.json')
                if os.path.exists(cred_path):
                    with open(cred_path, 'r', encoding='utf-8') as f:
                        creds = json.load(f)
                    creds['gemini_api_key'] = gemini_api_key
                    with open(cred_path, 'w', encoding='utf-8') as f:
                        json.dump(creds, f, ensure_ascii=False, indent=4)
                    safe_print("[Gemini] API Key saved to credentials.json")
            except Exception as e:
                safe_print(f"[Gemini] Error saving config: {e}")
        
        if 'model' in data:
            gemini_model = data['model']
        
        # Update config
        config['GEMINI_API_KEY'] = gemini_api_key
        config['GEMINI_MODEL'] = gemini_model
        
        return jsonify({
            "success": True,
            "api_key_configured": bool(gemini_api_key),
            "model": gemini_model
        })
    
    print("[Gemini Routes] Registered successfully")
