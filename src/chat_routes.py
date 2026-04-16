# -*- coding: utf-8 -*-
"""
Chat Routes Module - Flask API endpoints for AI Chat Long-term Memory
"""

import json
import uuid
from flask import Blueprint, request, jsonify, session
from functools import wraps

# Create Blueprint
chat_bp = Blueprint('chat', __name__, url_prefix='/api/ai/chat')

# ============================================
# Helper Functions
# ============================================

# FIX #2: Moved imports to module level to avoid circular import,
# but uses lazy import pattern to avoid issues when server not ready
_server_sessions = None
_server_sessions_lock = None

def _get_server_sessions():
    """Lazy load server sessions to avoid circular import"""
    global _server_sessions, _server_sessions_lock
    if _server_sessions is None:
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        try:
            from server import sessions as _server_sessions, sessions_lock as _server_sessions_lock
        except ImportError:
            pass
    return _server_sessions, _server_sessions_lock

def get_user_from_token():
    """Get user_id from Authorization token or X-User-ID header"""
    # Use X-User-ID header (simplified solution for 401)
    user_id_header = request.headers.get('X-User-ID')
    if user_id_header:
        try:
            user_id = int(user_id_header)
            return user_id
        except (ValueError, TypeError):
            return None
    
    # Fallback to Bearer token
    auth_header = request.headers.get('Authorization', '')
    
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    
    token = auth_header[7:]
    
    # Use lazy import pattern to avoid circular import
    server_sessions, sessions_lock = _get_server_sessions()
    if server_sessions and sessions_lock:
        with sessions_lock:
            session_data = server_sessions.get(token)
            if session_data:
                user_id = session_data.get('user', {}).get('user_id')
                return user_id
    
    return None

def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        user_id = get_user_from_token()
        if not user_id:
            return jsonify({"success": False, "error": "Chưa đăng nhập"}), 401
        return f(user_id, *args, **kwargs)
    return decorated_function

# ============================================
# Session Endpoints
# ============================================

@chat_bp.route('/sessions', methods=['GET'])
@require_auth
def get_sessions(user_id):
    """Get all chat sessions for user"""
    limit = int(request.args.get('limit', 50))
    offset = int(request.args.get('offset', 0))
    
    from src import chat_service
    sessions = chat_service.get_user_sessions(user_id, limit, offset)
    
    return jsonify({
        "success": True,
        "sessions": sessions,
        "total": len(sessions)
    })

@chat_bp.route('/sessions/count', methods=['GET'])
@require_auth
def get_session_count(user_id):
    """Get total session count for user"""
    from src import chat_service
    count = chat_service.get_total_session_count(user_id)
    
    return jsonify({
        "success": True,
        "count": count
    })

@chat_bp.route('/sessions', methods=['POST'])
@require_auth
def create_session(user_id):
    """Create a new chat session"""
    data = request.get_json() or {}
    title = data.get('title', 'Cuộc trò chuyện mới')
    model = data.get('model', 'stepfun/step-3.5-flash:free')
    
    from src import chat_service
    session = chat_service.create_new_session(user_id, title, model)
    
    if session:
        return jsonify({
            "success": True,
            "session": session
        }), 201
    else:
        return jsonify({
            "success": False,
            "error": "Không thể tạo session"
        }), 500

@chat_bp.route('/sessions/<session_id>', methods=['GET'])
@require_auth
def get_session(user_id, session_id):
    """Get a specific chat session"""
    from src import chat_service
    session = chat_service.get_session_by_id(session_id, user_id)
    
    if session:
        return jsonify({
            "success": True,
            "session": session
        })
    else:
        return jsonify({
            "success": False,
            "error": "Session không tồn tại"
        }), 404

@chat_bp.route('/sessions/<session_id>', methods=['PUT'])
@require_auth
def update_session(user_id, session_id):
    """Update session title"""
    data = request.get_json() or {}
    title = data.get('title')
    
    if not title:
        return jsonify({
            "success": False,
            "error": "Tiêu đề không được để trống"
        }), 400
    
    from src import chat_service
    success = chat_service.update_title(session_id, user_id, title)
    
    if success:
        return jsonify({
            "success": True,
            "message": "Đã cập nhật tiêu đề"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Không thể cập nhật tiêu đề"
        }), 500

@chat_bp.route('/sessions/<session_id>', methods=['DELETE'])
@require_auth
def delete_session(user_id, session_id):
    """Delete a chat session"""
    from src import chat_service
    success = chat_service.delete_session_by_id(session_id, user_id)
    
    if success:
        return jsonify({
            "success": True,
            "message": "Đã xóa session"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Không thể xóa session"
        }), 500

# ============================================
# Message Endpoints
# ============================================

@chat_bp.route('/sessions/<session_id>/messages', methods=['GET'])
@require_auth
def get_messages(user_id, session_id):
    """Get messages for a session"""
    limit = int(request.args.get('limit', 100))
    offset = int(request.args.get('offset', 0))
    
    from src import chat_service
    messages = chat_service.get_session_messages(session_id, user_id, limit, offset)
    
    return jsonify({
        "success": True,
        "messages": messages,
        "total": len(messages)
    })

@chat_bp.route('/sessions/<session_id>/messages', methods=['POST'])
@require_auth
def add_message(user_id, session_id):
    """Add a message to a session"""
    # DEBUG: Log incoming request
    print(f"[DEBUG] add_message called - user_id: {user_id}, session_id: {session_id}")
    
    data = request.get_json() or {}
    role = data.get('role', 'user')
    content = data.get('content', '')
    
    # DEBUG: Log request data
    print(f"[DEBUG] add_message - role: {role}, content length: {len(content) if content else 0}, content preview: {content[:50] if content else 'EMPTY'}")
    
    if not content:
        print("[DEBUG] add_message - ERROR: Content is empty!")
        return jsonify({
            "success": False,
            "error": "Nội dung không được để trống"
        }), 400
    
    if role not in ['user', 'ai']:
        role = 'user'
    
    from src import chat_service
    print(f"[DEBUG] add_message - Calling chat_service.add_chat_message...")
    message = chat_service.add_chat_message(session_id, role, content)
    
    print(f"[DEBUG] add_message - Result: {message is not None}")
    
    if message:
        # Update summary if needed
        from src import chat_db
        message_count = chat_db.get_message_count(session_id)
        if message_count > 50 and message_count % 50 == 0:
            # Generate summary every 50 messages
            messages = chat_db.get_messages(session_id, limit=10000)
            summary = chat_service.generate_auto_summary(messages)
            chat_service.update_summary(session_id, summary)
        
        return jsonify({
            "success": True,
            "message": message
        }), 201
    else:
        return jsonify({
            "success": False,
            "error": "Không thể thêm tin nhắn"
        }), 500

@chat_bp.route('/sessions/<session_id>/messages/<message_id>', methods=['DELETE'])
@require_auth
def delete_message(user_id, session_id, message_id):
    """Delete a message"""
    from src import chat_service
    success = chat_service.delete_message_by_id(message_id, session_id, user_id)
    
    if success:
        return jsonify({
            "success": True,
            "message": "Đã xóa tin nhắn"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Không thể xóa tin nhắn"
        }), 500

# ============================================
# Search Endpoints
# ============================================

@chat_bp.route('/search', methods=['GET'])
@require_auth
def search_chat(user_id):
    """Search in chat history (legacy endpoint for user display)"""
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 50))
    
    if not query:
        return jsonify({
            "success": False,
            "error": "Từ khóa tìm kiếm không được để trống"
        }), 400
    
    from src import chat_service
    results = chat_service.search_chat_history(user_id, query, limit)
    
    return jsonify({
        "success": True,
        "results": results,
        "total": len(results)
    })


@chat_bp.route('/search-for-context', methods=['GET'])
@require_auth
def search_for_context(user_id):
    """
    Search for AI context - returns formatted context string for AI
    This is used by AI to automatically find relevant information from past sessions
    """
    query = request.args.get('q', '')
    limit = int(request.args.get('limit', 10))
    
    if not query:
        return jsonify({
            "success": False,
            "error": "Từ khóa tìm kiếm không được để trống"
        }), 400
    
    from src import chat_service
    
    # Get formatted context
    context = chat_service.search_for_ai_context(user_id, query, limit)
    
    # Also check if we should auto-detect search intent
    should_search, keywords = chat_service.detect_search_intent(query)
    
    return jsonify({
        "success": True,
        "context": context,
        "should_search": should_search,
        "keywords": keywords if should_search else query,
        "result_count": len(context) > 0
    })

# ============================================
# Export Endpoints
# ============================================

@chat_bp.route('/export/<session_id>', methods=['GET'])
@require_auth
def export_session(user_id, session_id):
    """Export a chat session"""
    from src import chat_service
    data = chat_service.export_chat_session(session_id, user_id)
    
    if data:
        return jsonify({
            "success": True,
            "data": data
        })
    else:
        return jsonify({
            "success": False,
            "error": "Session không tồn tại"
        }), 404

# ============================================
# System State Endpoints
# ============================================

@chat_bp.route('/system-state', methods=['GET'])
@require_auth
def get_system_state(user_id):
    """Get system state for user"""
    from src import chat_service
    state = chat_service.get_system_state(user_id)
    
    return jsonify({
        "success": True,
        "system_state": state or {}
    })

@chat_bp.route('/system-state', methods=['PUT'])
@require_auth
def update_system_state(user_id):
    """Update system state"""
    data = request.get_json() or {}
    
    # Allowed fields
    allowed_fields = ['current_project', 'current_step', 'last_action', 'metadata']
    update_data = {k: v for k, v in data.items() if k in allowed_fields}
    
    if not update_data:
        return jsonify({
            "success": False,
            "error": "Không có dữ liệu để cập nhật"
        }), 400
    
    from src import chat_service
    success = chat_service.update_system_state(user_id, **update_data)
    
    if success:
        return jsonify({
            "success": True,
            "message": "Đã cập nhật system state"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Không thể cập nhật system state"
        }), 500

# ============================================
# Context Endpoint for AI
# ============================================

@chat_bp.route('/context/<session_id>', methods=['GET'])
@require_auth
def get_ai_context(user_id, session_id):
    """Get AI context for a session (for AI API calls)"""
    from src import chat_service
    
    # Verify session exists
    session = chat_service.get_session_by_id(session_id, user_id)
    if not session:
        return jsonify({
            "success": False,
            "error": "Session không tồn tại"
        }), 404
    
    # Build context
    context = chat_service.build_ai_context(session_id, user_id)
    
    return jsonify({
        "success": True,
        "context": context
    })

# ============================================
# Migration Endpoint
# ============================================

@chat_bp.route('/migrate', methods=['POST'])
@require_auth
def migrate_messages(user_id):
    """Migrate messages from localStorage to server"""
    data = request.get_json() or {}
    messages = data.get('messages', [])
    session_id = data.get('session_id')
    
    if not messages:
        return jsonify({
            "success": False,
            "error": "Không có tin nhắn để migrate"
        }), 400
    
    from src import chat_service
    
    # Create new session if not provided
    if not session_id:
        session = chat_service.create_new_session(user_id, "Imported Chat")
        if session:
            session_id = session['id']
        else:
            return jsonify({
                "success": False,
                "error": "Không thể tạo session mới"
            }), 500
    
    # Migrate messages
    count = chat_service.migrate_localStorage_messages(user_id, session_id, messages)
    
    return jsonify({
        "success": True,
        "session_id": session_id,
        "imported_count": count
    })

# ============================================
# Summary Endpoint
# ============================================

@chat_bp.route('/sessions/<session_id>/summary', methods=['GET'])
@require_auth
def get_summary(user_id, session_id):
    """Get summary for a session"""
    from src import chat_service
    
    # Verify session exists
    session = chat_service.get_session_by_id(session_id, user_id)
    if not session:
        return jsonify({
            "success": False,
            "error": "Session không tồn tại"
        }), 404
    
    summary = chat_service.get_or_create_summary(session_id)
    
    return jsonify({
        "success": True,
        "summary": summary
    })

@chat_bp.route('/sessions/<session_id>/summary', methods=['PUT'])
@require_auth
def update_summary(user_id, session_id):
    """Update summary for a session"""
    data = request.get_json() or {}
    summary = data.get('summary', '')
    
    from src import chat_service
    success = chat_service.update_summary(session_id, summary)
    
    if success:
        return jsonify({
            "success": True,
            "message": "Đã cập nhật tóm tắt"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Không thể cập nhật tóm tắt"
        }), 500

# ============================================
# AI Memory Endpoints (Layer 1-3)
# ============================================

@chat_bp.route('/memory/short-term', methods=['POST'])
@require_auth
def add_short_term_memory(user_id):
    """Add to short-term memory (Layer 2)"""
    data = request.get_json() or {}
    content = data.get('content', '')
    project_id = data.get('project_id')
    session_id = data.get('session_id')
    metadata = data.get('metadata')
    
    if not content:
        return jsonify({
            "success": False,
            "error": "Nội dung không được để trống"
        }), 400
    
    from src import ai_memory
    memory_id = ai_memory.add_short_term_memory(user_id, content, project_id, session_id, metadata)
    
    return jsonify({
        "success": True,
        "memory_id": memory_id
    }), 201

@chat_bp.route('/memory/short-term', methods=['GET'])
@require_auth
def get_short_term_memories(user_id):
    """Get short-term memories (Layer 2)"""
    project_id = request.args.get('project_id')
    limit = int(request.args.get('limit', 10))
    
    from src import ai_memory
    memories = ai_memory.get_short_term_memory(user_id, project_id, limit)
    
    return jsonify({
        "success": True,
        "memories": memories,
        "total": len(memories)
    })

@chat_bp.route('/memory/long-term', methods=['POST'])
@require_auth
def add_long_term_memory(user_id):
    """Add to long-term memory (Layer 3)"""
    # Check user consent first
    from src import ai_memory
    consent = ai_memory.get_user_consent(user_id)
    if not consent or not consent.get('long_term_storage'):
        return jsonify({
            "success": False,
            "error": "Chưa đồng ý lưu trữ dài hạn"
        }), 403
    
    data = request.get_json() or {}
    content = data.get('content', '')
    role = data.get('role')
    project_id = data.get('project_id')
    metadata = data.get('metadata')
    
    if not content:
        return jsonify({
            "success": False,
            "error": "Nội dung không được để trống"
        }), 400
    
    memory_id = ai_memory.add_long_term_memory(user_id, content, role, project_id, metadata)
    
    if memory_id:
        return jsonify({
            "success": True,
            "memory_id": memory_id
        }), 201
    else:
        return jsonify({
            "success": False,
            "error": "Nội dung đã tồn tại"
        }), 409

@chat_bp.route('/memory/long-term/search', methods=['GET'])
@require_auth
def search_long_term_memory(user_id):
    """Search long-term memory (Layer 3 - RAG)"""
    query = request.args.get('q', '')
    project_id = request.args.get('project_id')
    limit = int(request.args.get('limit', 5))
    
    if not query:
        return jsonify({
            "success": False,
            "error": "Từ khóa tìm kiếm không được để trống"
        }), 400
    
    from src import ai_memory
    results = ai_memory.search_long_term_memory(user_id, query, project_id, limit)
    
    return jsonify({
        "success": True,
        "results": results,
        "total": len(results)
    })

@chat_bp.route('/memory/long-term', methods=['GET'])
@require_auth
def get_long_term_memories(user_id):
    """Get all long-term memories (Layer 3)"""
    project_id = request.args.get('project_id')
    limit = int(request.args.get('limit', 50))
    
    from src import ai_memory
    memories = ai_memory.get_user_long_term_memories(user_id, project_id, limit)
    
    return jsonify({
        "success": True,
        "memories": memories,
        "total": len(memories)
    })

@chat_bp.route('/memory/<memory_id>', methods=['DELETE'])
@require_auth
def delete_memory(user_id, memory_id):
    """Delete a memory (only if not locked)"""
    from src import ai_memory
    success = ai_memory.delete_memory(memory_id, user_id)
    
    if success:
        return jsonify({
            "success": True,
            "message": "Đã xóa bộ nhớ"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Không thể xóa (bộ nhớ có thể đã bị khóa)"
        }), 403

@chat_bp.route('/memory/<memory_id>/lock', methods=['POST'])
@require_auth
def lock_memory(user_id, memory_id):
    """Lock a memory"""
    from src import ai_memory
    success = ai_memory.lock_memory(memory_id, user_id)
    
    if success:
        return jsonify({
            "success": True,
            "message": "Đã khóa bộ nhớ"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Không thể khóa bộ nhớ"
        }), 500

@chat_bp.route('/memory/<memory_id>/unlock', methods=['POST'])
@require_auth
def unlock_memory(user_id, memory_id):
    """Unlock a memory"""
    from src import ai_memory
    success = ai_memory.unlock_memory(memory_id, user_id)
    
    if success:
        return jsonify({
            "success": True,
            "message": "Đã mở khóa bộ nhớ"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Không thể mở khóa bộ nhớ"
        }), 500

@chat_bp.route('/memory/context', methods=['GET'])
@require_auth
def get_memory_context(user_id):
    """Get assembled memory context for AI (RAG)"""
    project_id = request.args.get('project_id')
    query = request.args.get('q', '')
    
    from src import ai_memory
    context = ai_memory.assemble_memory_context(user_id, project_id, query)
    
    return jsonify({
        "success": True,
        "context": context
    })

@chat_bp.route('/memory/consent', methods=['GET'])
@require_auth
def get_memory_consent(user_id):
    """Get user consent status"""
    from src import ai_memory
    consent = ai_memory.get_user_consent(user_id)
    
    return jsonify({
        "success": True,
        "consent": consent or {"long_term_storage": False}
    })

@chat_bp.route('/memory/consent', methods=['POST'])
@require_auth
def set_memory_consent(user_id):
    """Set user consent for long-term storage"""
    data = request.get_json() or {}
    long_term = data.get('long_term_storage', False)
    
    from src import ai_memory
    success = ai_memory.set_user_consent(user_id, long_term)
    
    if success:
        return jsonify({
            "success": True,
            "message": "Đã cập nhật cài đặt bộ nhớ"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Không thể cập nhật cài đặt"
        }), 500

@chat_bp.route('/memory/consent', methods=['DELETE'])
@require_auth
def revoke_memory_consent(user_id):
    """Revoke user consent"""
    from src import ai_memory
    success = ai_memory.revoke_consent(user_id)
    
    if success:
        return jsonify({
            "success": True,
            "message": "Đã hủy đồng ý lưu trữ dài hạn"
        })
    else:
        return jsonify({
            "success": False,
            "error": "Không thể hủy đồng ý"
        }), 500


# ============================================
# MCP Tools Endpoints
# ============================================

@chat_bp.route('/tools', methods=['GET'])
def get_tools():
    """Lấy danh sách tất cả các tool definitions"""
    from src import mcp_tools
    tools = mcp_tools.get_tool_definitions()
    
    return jsonify({
        "success": True,
        "tools": tools,
        "count": len(tools)
    })

@chat_bp.route('/tool-call', methods=['POST'])
@require_auth
def call_tool(user_id):
    """Gọi một tool cụ thể"""
    data = request.get_json() or {}
    tool_name = data.get('tool_name')
    parameters = data.get('parameters', {})
    
    if not tool_name:
        return jsonify({
            "success": False,
            "error": "Thiếu tool_name"
        }), 400
    
    from src import mcp_tools
    result = mcp_tools.call_tool(tool_name, user_id, parameters)
    
    return jsonify(result)

@chat_bp.route('/tools-prompt', methods=['GET'])
def get_tools_prompt():
    """Lấy system prompt hướng dẫn sử dụng tools"""
    from src import mcp_tools
    prompt = mcp_tools.get_tools_system_prompt()
    
    return jsonify({
        "success": True,
        "prompt": prompt
    })

@chat_bp.route('/tools-test', methods=['GET'])
@require_auth
def test_tools(user_id):
    """Test tất cả các tools (chỉ dùng cho dev)"""
    from src import mcp_tools
    results = mcp_tools.test_tools(user_id)
    
    return jsonify({
        "success": True,
        "results": results
    })


# ============================================
# AI AGENT Endpoints (NEW)
# ============================================

@chat_bp.route('/agent/tools', methods=['GET'])
def get_agent_tools():
    """Lấy danh sách extended tools cho Agent"""
    from src.agent_tools import get_extended_tool_definitions
    tools = get_extended_tool_definitions()
    
    return jsonify({
        "success": True,
        "tools": tools,
        "count": len(tools)
    })

@chat_bp.route('/agent/plan', methods=['POST'])
@require_auth
def agent_plan(user_id):
    """
    Planner: Lập kế hoạch tool execution dựa trên user message
    
    Request: {
        "message": "Dự án ABC sao rồi?",
        "session_id": "optional-session-id"
    }
    """
    data = request.get_json() or {}
    message = data.get('message', '')
    session_id = data.get('session_id')
    
    if not message:
        return jsonify({
            "success": False,
            "error": "Thiếu message"
        }), 400
    
    from src.agent_planner import AgentPlanner
    planner = AgentPlanner(user_id)
    plan = planner.plan(message, session_id)
    
    return jsonify({
        "success": True,
        "intent": plan.intent,
        "confidence": plan.confidence,
        "steps": [
            {
                "tool": s["tool"],
                "parameters": s["parameters"],
                "reason": s["reason"]
            }
            for s in plan.steps
        ]
    })

@chat_bp.route('/agent/execute', methods=['POST'])
@require_auth
def agent_execute(user_id):
    """
    Execute: Thực thi plan với tools đã lập kế hoạch
    
    Request: {
        "message": "Dự án ABC sao rồi?",
        "session_id": "optional-session-id",
        "auto_trigger": true/false
    }
    """
    data = request.get_json() or {}
    message = data.get('message', '')
    session_id = data.get('session_id')
    
    if not message:
        return jsonify({
            "success": False,
            "error": "Thiếu message"
        }), 400
    
    from src.agent_coordinator import AgentCoordinator
    coordinator = AgentCoordinator(user_id)
    
    # Process message through agent
    response = coordinator.process_message(message, session_id)
    
    return jsonify({
        "success": True,
        "message": response.message,
        "intent": response.intent,
        "confidence": response.confidence,
        "tools_used": response.tools_used,
        "suggestions": response.suggestions
    })

@chat_bp.route('/agent/trigger', methods=['GET'])
@require_auth
def agent_get_triggers(user_id):
    """
    Trigger: Lấy các trigger suggestions hiện tại
    """
    from src.agent_triggers import get_trigger_manager
    manager = get_trigger_manager()
    
    # Get user data
    from src import db_helper
    projects = db_helper.get_projects_by_user(user_id)
    notices = db_helper.get_pending_notices(user_id)
    
    results = manager.check_triggers({
        "projects": projects,
        "notices": notices
    })
    
    return jsonify({
        "success": True,
        "triggers": results,
        "count": len(results)
    })

@chat_bp.route('/agent/context', methods=['GET'])
@require_auth
def agent_get_context(user_id):
    """
    Context: Lấy assembled context cho Agent (từ memory layers)
    """
    project_id = request.args.get('project_id')
    query = request.args.get('q', '')
    
    from src.ai_memory import assemble_memory_context
    context = assemble_memory_context(user_id, project_id, query)
    
    return jsonify({
        "success": True,
        "context": context
    })

@chat_bp.route('/agent/prompt', methods=['GET'])
def get_agent_prompt():
    """Lấy system prompt mở rộng cho AI Agent"""
    from src.agent_tools import get_agent_tools_prompt
    prompt = get_agent_tools_prompt()
    
    return jsonify({
        "success": True,
        "prompt": prompt
    })


# Function to register blueprint with app
def register_chat_routes(app):
    """Register chat routes with Flask app"""
    app.register_blueprint(chat_bp)
    print("[ChatRoutes] Registered successfully")