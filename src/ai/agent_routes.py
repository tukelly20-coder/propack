# -*- coding: utf-8 -*-
"""
AI Agent Routes - Tách từ server.py
Bao gồm các endpoints:
- /api/ai/agent/detect-intent
- /api/ai/agent/plan
- /api/ai/agent/triggers
- /api/ai/agent/tools
- /api/ai/chat/agent/tools
"""

def register_routes(app, config):
    """Register AI Agent routes with Flask app"""
    from flask import request, jsonify, make_response
    
    # Import necessary modules
    from src.intent_detector import detect_intent
    from src.agent_planner import AgentPlanner
    from src.agent_triggers import get_suggestions_for_user
    from src.agent_tools import get_extended_tool_definitions
    
    # Get config values
    sessions = config.get('sessions')
    sessions_lock = config.get('sessions_lock')
    safe_print = config.get('safe_print', print)
    
    # ========== Detect Intent Endpoint ==========
    @app.route('/api/ai/agent/detect-intent', methods=['POST', 'OPTIONS'])
    def agent_detect_intent():
        """Phát hiện intent từ message"""
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        data = request.get_json() or {}
        message = data.get('message', '')
        
        if not message:
            return jsonify({"success": False, "error": "Tin nhắn trống"}), 400
        
        try:
            intent_result = detect_intent(message)
            return jsonify({
                "success": True,
                "intent": intent_result
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # ========== Agent Plan Endpoint ==========
    @app.route('/api/ai/agent/plan', methods=['POST', 'OPTIONS'])
    def agent_plan():
        """Lập kế hoạch tool execution"""
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        data = request.get_json() or {}
        message = data.get('message', '')
        session_id = data.get('session_id', '')
        
        # Get user_id from auth header
        user_id = 1  # Default
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            with sessions_lock:
                session_data = sessions.get(token)
                if session_data:
                    user_id = session_data.get('user', {}).get('user_id', 1)
        
        if not message:
            return jsonify({"success": False, "error": "Tin nhắn trống"}), 400
        
        try:
            planner = AgentPlanner(user_id)
            plan = planner.plan(message, session_id)
            return jsonify({
                "success": True,
                "plan": plan.to_dict()
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # ========== Agent Triggers Endpoint ==========
    @app.route('/api/ai/agent/triggers', methods=['GET', 'OPTIONS'])
    def agent_triggers():
        """Lấy active triggers cho user"""
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        # Get user_id from auth header
        user_id = 1  # Default
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            with sessions_lock:
                session_data = sessions.get(token)
                if session_data:
                    user_id = session_data.get('user', {}).get('user_id', 1)
        
        try:
            suggestions = get_suggestions_for_user(user_id, limit=5)
            return jsonify({
                "success": True,
                "suggestions": suggestions
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # ========== Agent Tools Endpoint ==========
    @app.route('/api/ai/agent/tools', methods=['GET', 'OPTIONS'])
    def agent_tools():
        """Lấy danh sách tools cho Agent"""
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        try:
            tools = get_extended_tool_definitions()
            return jsonify({
                "success": True,
                "tools": tools,
                "count": len(tools)
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    # ========== Chat Agent Tools Endpoint ==========
    @app.route('/api/ai/chat/agent/tools', methods=['GET', 'OPTIONS'])
    def chat_agent_tools():
        """Lấy danh sách tools cho Agent (alias cho /api/ai/agent/tools)"""
        if request.method == 'OPTIONS':
            response = make_response()
            response.headers['Access-Control-Allow-Origin'] = '*'
            response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
            response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
            return response
        
        try:
            tools = get_extended_tool_definitions()
            return jsonify({
                "success": True,
                "tools": tools,
                "count": len(tools)
            })
        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500
    
    print("[Agent Routes] Registered successfully")
