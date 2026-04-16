# -*- coding: utf-8 -*-
"""
Chat Service Module - Business logic for AI Chat Long-term Memory
"""

import uuid
from datetime import datetime
from typing import Optional, List, Dict, Any

from src import chat_db

# Constants
DEFAULT_SESSION_TITLE = "Cuộc trò chuyện mới"
DEFAULT_CHAT_MODEL = "stepfun/step-3.5-flash:free"

# ============================================
# Session Service
# ============================================

def create_new_session(user_id: int, title: str = None, model: str = DEFAULT_CHAT_MODEL) -> Dict:
    """Create a new chat session"""
    session_id = str(uuid.uuid4())
    session_title = title or DEFAULT_SESSION_TITLE
    
    success = chat_db.create_session(session_id, user_id, session_title, model)
    
    if success:
        return {
            'id': session_id,
            'title': session_title,
            'user_id': user_id,
            'model': model,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
    return None

def get_user_sessions(user_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
    """Get all sessions for a user"""
    return chat_db.get_sessions(user_id, limit, offset)

def get_total_session_count(user_id: int) -> int:
    """Get total session count for a user"""
    return chat_db.get_session_count(user_id)

def get_session_by_id(session_id: str, user_id: int) -> Optional[Dict]:
    """Get a specific session"""
    return chat_db.get_session(session_id, user_id)

def update_title(session_id: str, user_id: int, title: str) -> bool:
    """Update session title"""
    return chat_db.update_session_title(session_id, user_id, title)

def delete_session_by_id(session_id: str, user_id: int) -> bool:
    """Delete a session"""
    return chat_db.delete_session(session_id, user_id)

# ============================================
# Message Service
# ============================================

def add_chat_message(session_id: str, role: str, content: str) -> Dict:
    """Add a message to a session and return the message"""
    message_id = str(uuid.uuid4())
    
    success = chat_db.add_message(session_id, message_id, role, content)
    
    if success:
        return {
            'id': message_id,
            'session_id': session_id,
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
    return None

def get_session_messages(session_id: str, user_id: int, limit: int = 100, offset: int = 0) -> List[Dict]:
    """Get all messages for a session (with user validation)"""
    # First verify the session belongs to the user
    session = chat_db.get_session(session_id, user_id)
    if not session:
        return []
    
    return chat_db.get_messages(session_id, limit, offset)

def get_recent_messages_for_ai(session_id: str, limit: int = 20) -> List[Dict]:
    """Get recent messages for AI context"""
    return chat_db.get_recent_messages(session_id, limit)

def delete_message_by_id(message_id: str, session_id: str, user_id: int) -> bool:
    """Delete a message (with validation)"""
    # Verify session ownership
    session = chat_db.get_session(session_id, user_id)
    if not session:
        return False
    
    return chat_db.delete_message(message_id, session_id)

# ============================================
# Summary Service (for AI Context)
# ============================================

def get_or_create_summary(session_id: str) -> str:
    """Get existing summary or return empty string"""
    summary = chat_db.get_summary(session_id)
    return summary or ""

def update_summary(session_id: str, new_content: str) -> bool:
    """Update summary with new content"""
    message_count = chat_db.get_message_count(session_id)
    return chat_db.save_summary(session_id, new_content, message_count)

def generate_auto_summary(messages: List[Dict]) -> str:
    """Generate automatic summary from messages (simple version)"""
    if not messages:
        return ""
    
    # Simple summary: first few messages topic
    first_user_msg = None
    for msg in messages:
        if msg.get('role') == 'user':
            first_user_msg = msg.get('content', '')[:100]
            break
    
    message_count = len(messages)
    
    if first_user_msg:
        return f"Cuộc trò chuyện về: {first_user_msg}... ({message_count} tin nhắn)"
    else:
        return f"Cuộc trò chuyện ({message_count} tin nhắn)"

# ============================================
# System State Service
# ============================================

def get_system_state(user_id: int) -> Optional[Dict]:
    """Get system state for a user"""
    return chat_db.get_ai_session(user_id)

def update_system_state(user_id: int, **kwargs) -> bool:
    """Update specific system state fields"""
    return chat_db.update_system_state(user_id, **kwargs)

def init_user_ai_session(user_id: int) -> bool:
    """Initialize AI session for user if not exists"""
    existing = chat_db.get_ai_session(user_id)
    if not existing:
        session_id = str(uuid.uuid4())
        return chat_db.save_ai_session(user_id, session_id)
    return True

# ============================================
# Context Builder (for AI)
# ============================================

def build_ai_context(session_id: str, user_id: int) -> Dict:
    """
    Build complete context for AI:
    - System State from ai_sessions
    - Summary from chat_summaries
    - Recent messages from chat_messages
    - Session count
    """
    # 1. Get System State
    system_state = get_system_state(user_id)
    
    # 2. Get Summary
    summary = get_or_create_summary(session_id)
    
    # 3. Get Recent Messages
    recent_messages = get_recent_messages_for_ai(session_id, limit=20)
    
    # 4. Get Session Count
    session_count = get_total_session_count(user_id)
    
    # 5. Format messages for AI (last 10 messages)
    formatted_history = []
    for msg in recent_messages[-10:]:
        formatted_history.append({
            'role': msg.get('role', 'user'),
            'content': msg.get('content', '')
        })
    
    return {
        'system_state': system_state or {},
        'summary': summary,
        'recent_messages': recent_messages,
        'formatted_history': formatted_history,
        'session_count': session_count
    }

def get_context_for_ai(session_id: str, user_id: int) -> str:
    """Get formatted context string for AI system prompt"""
    context = build_ai_context(session_id, user_id)
    
    parts = []
    
    # System State
    ss = context.get('system_state', {})
    if ss.get('current_project') or ss.get('current_step'):
        parts.append("## TRẠNG THÁI HỆ THỐNG")
        if ss.get('current_project'):
            parts.append(f"- Dự án hiện tại: {ss['current_project']}")
        if ss.get('current_step'):
            parts.append(f"- Bước hiện tại: {ss['current_step']}")
        if ss.get('last_action'):
            parts.append(f"- Hành động cuối: {ss['last_action']}")
    
    # Session Count
    session_count = context.get('session_count', 0)
    if session_count > 0:
        parts.append(f"\n## THÔNG TIN CUỘC TRÒ CHUYỆN")
        parts.append(f"- Bạn có {session_count} cuộc trò chuyện với AI")
    
    # Summary
    if context.get('summary'):
        parts.append("\n## TÓM TẮT CUỘC TRÒ CHUYỆN")
        parts.append(context['summary'])
    
    # Recent Messages (as backup context)
    if context.get('recent_messages'):
        parts.append("\n## TIN NHẮN GẦN ĐÂY")
        for msg in context['recent_messages'][-5:]:
            role = "User" if msg.get('role') == 'user' else "AI"
            content = msg.get('content', '')[:200]
            parts.append(f"- {role}: {content}")
    
    return "\n".join(parts) if parts else ""

# ============================================
# Search Service
# ============================================

def search_chat_history(user_id: int, query: str, limit: int = 50) -> List[Dict]:
    """Search across all user chat history (legacy function)"""
    return chat_db.search_messages(user_id, query, limit)


def search_for_ai_context(user_id: int, query: str, limit: int = 10) -> str:
    """
    Search for AI context - returns formatted context string for AI
    This function is used by AI to find relevant information from past sessions
    
    Args:
        user_id: The user's ID
        query: Search query (keywords from user's question)
        limit: Maximum number of results (default 10)
    
    Returns:
        Formatted context string for AI system prompt, or empty string if no results
    """
    results = chat_db.search_messages(user_id, query, limit)
    
    if not results:
        return ""
    
    # Format results as context
    context_parts = [
        "## THÔNG TIN TÌM THẤY TỪ CÁC CUỘC TRÒ CHUYỆN TRƯỚC"
    ]
    
    for i, result in enumerate(results[:limit]):
        session_title = result.get('title', 'Không có tiêu đề')
        content = result.get('content', '')
        role = result.get('role', 'user')
        timestamp = result.get('timestamp', '')
        highlight = result.get('highlight', content[:100])
        
        # Format: Session title + content
        context_parts.append(f"\n### {i+1}. {session_title} ({role}):")
        context_parts.append(f"{highlight}")
    
    # Add instruction for AI
    if context_parts:
        context_parts.append("\n---\n")
        context_parts.append("Lưu Ý: Thông tin trên được tìm thấy từ các cuộc trò chuyện trước đó. ")
        context_parts.append("Bạn có thể sử dụng để trả lời câu hỏi của user nếu liên quan.")
    
    return "\n".join(context_parts)



def detect_search_intent(user_message: str) -> tuple[bool, str]:
    """
    Detect if user's message implies a need to search history
    
    Args:
        user_message: The user's message
    
    Returns:
        (should_search, extracted_keywords)
    """
    message_lower = user_message.lower()
    
    # Keywords that trigger search
    search_triggers = [
        'trước đó', 'hôm qua', 'hôm nay', 'lần trước',
        'đã hỏi', 'đã nói', 'đã thảo luận',
        'xem lại', 'tìm lại', 'nhắc lại',
        'cho tôi hỏi', 'tôi đã hỏi', 'mấy hôm'
    ]
    
    should_search = any(trigger in message_lower for trigger in search_triggers)
    
    # Extract potential keywords (words after certain patterns)
    keywords = user_message
    
    # If explicit about past conversation, search entire message
    if should_search:
        # Clean up the message to get better keywords
        for trigger in search_triggers:
            if trigger in message_lower:
                idx = message_lower.find(trigger)
                if idx > 0:
                    # Use text after trigger as additional context
                    extra = user_message[idx:].strip()
                    if extra:
                        keywords = extra + ' ' + keywords[:idx].strip()
                break
    
    return should_search, keywords

# ============================================
# Export Service
# ============================================

def export_chat_session(session_id: str, user_id: int) -> Optional[Dict]:
    """Export a complete session"""
    return chat_db.export_session(session_id, user_id)

# ============================================
# Migration Service
# ============================================

def migrate_localStorage_messages(user_id: int, session_id: str, messages: List[Dict]) -> int:
    """Migrate messages from localStorage to server"""
    count = 0
    for msg in messages:
        role = msg.get('role', 'user')
        content = msg.get('content', '')
        if content:
            result = add_chat_message(session_id, role, content)
            if result:
                count += 1
    
    # Update summary after migration
    if count > 0:
        all_messages = chat_db.get_messages(session_id, limit=10000)
        summary = generate_auto_summary(all_messages)
        update_summary(session_id, summary)
    
    return count