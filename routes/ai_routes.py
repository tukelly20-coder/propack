# ai_routes.py - AI Integration Routes (Gemini, Ollama, OpenRouter)
# Extracted from server.py for better modularity
import json
"""
AI Routes:
- POST /api/ai/agent/detect-intent  - Detect intent from message
- POST /api/ai/agent/plan        - Plan tool execution
- GET  /api/ai/agent/triggers    - Get active triggers
- GET  /api/ai/agent/tools      - Get agent tools
- POST /api/gemini/chat         - Gemini chat
- POST /api/gemini/chat/stream - Gemini streaming chat
- POST /api/ollama/chat/stream - Ollama streaming chat
- POST /api/openrouter/chat/stream - OpenRouter streaming chat
"""
from flask import Blueprint, request, jsonify, Response

ai_bp = Blueprint('ai', __name__, url_prefix='/api')

# AI configuration (to be set via init)
_GEMINI_API_KEY = None
_GEMINI_MODEL = 'gemini-3-flash-preview'
_OLLAMA_URL = 'http://localhost:11434'
_OLLAMA_ENABLED = True


def init_ai_routes(config):
    """Initialize AI configuration"""
    global _GEMINI_API_KEY, _GEMINI_MODEL, _OLLAMA_URL, _OLLAMA_ENABLED
    
    if 'gemini_api_key' in config:
        _GEMINI_API_KEY = config['gemini_api_key']
    if 'gemini_model' in config:
        _GEMINI_MODEL = config['gemini_model']
    if 'ollama_url' in config:
        _OLLAMA_URL = config['ollama_url']
    if 'ollama_enabled' in config:
        _OLLAMA_ENABLED = config['ollama_enabled']


# Intent Detection
@ai_bp.route('/ai/agent/detect-intent', methods=['POST', 'OPTIONS'])
def detect_intent():
    """Detect intent from message"""
    if request.method == 'OPTIONS':
        return Response('', status=204)
    
    data = request.get_json() or {}
    message = data.get('message', '')
    
    if not message:
        return jsonify({"success": False, "error": "Tin nhắn trống"}), 400
    
    try:
        from src.intent_detector import detect_intent as detect
        intent_result = detect(message)
        return jsonify({
            "success": True,
            "intent": intent_result
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@ai_bp.route('/ai/agent/plan', methods=['POST', 'OPTIONS'])
def agent_plan():
    """Plan tool execution"""
    if request.method == 'OPTIONS':
        return Response('', status=204)
    
    data = request.get_json() or {}
    message = data.get('message', '')
    session_id = data.get('session_id', '')
    
    # Get user_id from auth header
    user_id = 1  # Default
    auth_header = request.headers.get('Authorization', '')
    # ... (would need session lookup)
    
    if not message:
        return jsonify({"success": False, "error": "Tin nhắn trống"}), 400
    
    try:
        planner = __import__('src.agent_planner', fromlist=['AgentPlanner']).AgentPlanner(user_id)
        plan = planner.plan(message, session_id)
        return jsonify({
            "success": True,
            "plan": plan.to_dict()
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@ai_bp.route('/ai/agent/triggers', methods=['GET', 'OPTIONS'])
def agent_triggers():
    """Get active triggers for user"""
    if request.method == 'OPTIONS':
        return Response('', status=204)
    
    user_id = 1  # Default
    
    try:
        from src.agent_triggers import get_suggestions_for_user
        suggestions = get_suggestions_for_user(user_id, limit=5)
        return jsonify({
            "success": True,
            "suggestions": suggestions
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@ai_bp.route('/ai/agent/tools', methods=['GET', 'OPTIONS'])
def agent_tools():
    """Get agent tools"""
    if request.method == 'OPTIONS':
        return Response('', status=204)
    
    try:
        from src.agent_tools import get_extended_tool_definitions
        tools = get_extended_tool_definitions()
        return jsonify({
            "success": True,
            "tools": tools,
            "count": len(tools)
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# Gemini Chat
@ai_bp.route('/gemini/chat', methods=['POST', 'OPTIONS'])
def gemini_chat():
    """Chat with Gemini AI"""
    if request.method == 'OPTIONS':
        return Response('', status=204)
    
    if not _GEMINI_API_KEY:
        return jsonify({"success": False, "error": "Chưa cấu hình Gemini API Key"}), 500
    
    data = request.get_json() or {}
    message = data.get('message', '')
    model = data.get('model', _GEMINI_MODEL)
    history = data.get('history', [])
    
    if not message:
        return jsonify({"success": False, "error": "Tin nhắn không được để trống"}), 400
    
    try:
        import urllib.parse
        gemini_url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={_GEMINI_API_KEY}"
        
        headers = {'Content-Type': 'application/json'}
        payload = {
            "contents": history + [{"role": "user", "parts": [{"text": message}]}],
            "generationConfig": {
                "temperature": 0.9,
                "maxOutputTokens": 2048
            }
        }
        
        resp = __import__('requests').post(gemini_url, headers=headers, json=payload, timeout=60)
        
        if resp.status_code >= 400:
            return jsonify({"success": False, "error": f"Lỗi API: {resp.status_code}"}), resp.status_code
        
        result = resp.json()
        response_text = ""
        if 'candidates' in result and len(result['candidates']) > 0:
            candidate = result['candidates'][0]
            if 'content' in candidate and 'parts' in candidate['content']:
                parts = candidate['content']['parts']
                response_text = "\n".join([p.get('text', '') for p in parts])
        
        return jsonify({
            "success": True,
            "response": response_text or "Không có phản hồi từ AI",
            "model": model
        })
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# Gemini Streaming Chat
@ai_bp.route('/gemini/chat/stream', methods=['POST', 'OPTIONS'])
def gemini_chat_stream():
    """Gemini streaming chat"""
    if request.method == 'OPTIONS':
        return Response('', status=204)
    
    if not _GEMINI_API_KEY:
        return Response(
            f"data: {json.dumps({'error': 'Chưa cấu hình Gemini API Key'})}\n\n",
            mimetype='text/event-stream'
        )
    
    # ... streaming implementation similar to server.py
    return Response('', status=501)  # Placeholder


# Ollama Chat Stream
@ai_bp.route('/ollama/chat/stream', methods=['POST', 'OPTIONS'])
def ollama_chat_stream():
    """Ollama streaming chat"""
    if request.method == 'OPTIONS':
        return Response('', status=204)
    
    if not _OLLAMA_ENABLED:
        return Response(
            f"data: {json.dumps({'error': 'Ollama đang tắt'})}\n\n",
            mimetype='text/event-stream'
        )
    
    # ... streaming implementation
    return Response('', status=501)  # Placeholder


# OpenRouter Chat Stream
@ai_bp.route('/openrouter/chat/stream', methods=['POST', 'OPTIONS'])
def openrouter_chat_stream():
    """OpenRouter streaming chat with retry"""
    if request.method == 'OPTIONS':
        return Response('', status=204)
    
    # Would need API key from credentials
    return Response('', status=501)  # Placeholder


# Ollama models
@ai_bp.route('/ollama-models', methods=['GET', 'OPTIONS'])
def ollama_models():
    """Get available Ollama models"""
    if request.method == 'OPTIONS':
        return Response('', status=204)
    
    if not _OLLAMA_ENABLED:
        return jsonify({"error": "Ollama đang tắt", "models": []}), 200
    
    try:
        import requests
        resp = requests.get(f"{_OLLAMA_URL}/api/tags", timeout=10)
        
        if not resp.ok:
            return jsonify({"error": "Lỗi kết nối Ollama", "models": []}), 200
        
        return Response(resp.content, status=200, mimetype=resp.headers.get('Content-Type'))
    except Exception as e:
        return jsonify({"error": str(e), "models": []}), 200


# Ollama status
@ai_bp.route('/ollama-status', methods=['GET', 'POST', 'OPTIONS'])
def ollama_status():
    """Get or set Ollama configuration"""
    if request.method == 'OPTIONS':
        return Response('', status=204)
    
    global _OLLAMA_URL, _OLLAMA_ENABLED
    
    if request.method == 'POST':
        data = request.get_json()
        if data:
            if 'url' in data:
                url = data['url']
                if not url.startswith('http'):
                    url = f'http://{url}'
                _OLLAMA_URL = url
            if 'enabled' in data:
                _OLLAMA_ENABLED = data['enabled']
        
        return jsonify({"success": True, "url": _OLLAMA_URL, "enabled": _OLLAMA_ENABLED})
    
    # GET status
    can_connect = False
    try:
        import requests
        resp = requests.get(f"{_OLLAMA_URL}/api/tags", timeout=5)
        can_connect = resp.ok
    except:
        pass
    
    return jsonify({
        "url": _OLLAMA_URL,
        "enabled": _OLLAMA_ENABLED,
        "connected": can_connect
    })