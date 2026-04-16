# -*- coding: utf-8 -*-
"""
Chat Database Module - SQLite operations for AI Chat Long-term Memory
"""

import sqlite3
import os
import json
import sys
from datetime import datetime
from typing import Optional, List, Dict, Any

# Database file path - use appropriate location for PyInstaller
def _get_app_dir():
    """Get application directory - works with both script and PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

CHAT_DB_PATH = os.path.join(_get_app_dir(), 'chat_sessions.db')

# Lock for thread safety
_db_lock = None

def _get_lock():
    """Get or create the database lock"""
    global _db_lock
    if _db_lock is None:
        import threading
        _db_lock = threading.Lock()
    return _db_lock

def get_connection():
    """Get SQLite database connection"""
    conn = sqlite3.connect(CHAT_DB_PATH, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def init_chat_db():
    """Initialize chat database with tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Create chat_sessions table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            model TEXT DEFAULT 'stepfun/step-3.5-flash:free',
            is_deleted INTEGER DEFAULT 0
        )
    ''')
    
    # Create chat_messages table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_messages (
            id TEXT PRIMARY KEY,
            session_id TEXT NOT NULL,
            role TEXT NOT NULL CHECK(role IN ('user', 'ai')),
            content TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
        )
    ''')
    
    # Create chat_summaries table (for AI context)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS chat_summaries (
            session_id TEXT PRIMARY KEY,
            summary TEXT NOT NULL,
            message_count INTEGER DEFAULT 0,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL,
            FOREIGN KEY (session_id) REFERENCES chat_sessions(id)
        )
    ''')
    
    # Create ai_sessions table (System State)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS ai_sessions (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            current_project TEXT,
            current_step TEXT,
            last_action TEXT,
            last_action_time TEXT,
            metadata TEXT,
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )
    ''')
    
    # Create indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_user ON chat_sessions(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_sessions_updated ON chat_sessions(updated_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_messages_session ON chat_messages(session_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ai_sessions_user ON ai_sessions(user_id)')
    
    conn.commit()
    conn.close()
    print("[ChatDB] Database initialized successfully")

# ============================================
# Session Operations
# ============================================

def create_session(session_id: str, user_id: int, title: str = "New Chat", model: str = "stepfun/step-3.5-flash:free") -> bool:
    """Create a new chat session"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    try:
        cursor.execute('''
            INSERT INTO chat_sessions (id, user_id, title, created_at, updated_at, model, is_deleted)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        ''', (session_id, user_id, title, now, now, model))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"[ChatDB] Error creating session: {e}")
        return False
    finally:
        conn.close()

def get_sessions(user_id: int, limit: int = 50, offset: int = 0) -> List[Dict]:
    """Get all chat sessions for a user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, user_id, title, created_at, updated_at, model
        FROM chat_sessions
        WHERE user_id = ? AND is_deleted = 0
        ORDER BY updated_at DESC
        LIMIT ? OFFSET ?
    ''', (user_id, limit, offset))
    
    sessions = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return sessions

def get_session_count(user_id: int) -> int:
    """Get total session count for a user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) as count FROM chat_sessions WHERE user_id = ? AND is_deleted = 0
    ''', (user_id,))
    
    result = cursor.fetchone()
    conn.close()
    return result['count'] if result else 0

def get_session(session_id: str, user_id: int) -> Optional[Dict]:
    """Get a specific chat session"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, user_id, title, created_at, updated_at, model
        FROM chat_sessions
        WHERE id = ? AND user_id = ? AND is_deleted = 0
    ''', (session_id, user_id))
    
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None

def update_session_title(session_id: str, user_id: int, title: str) -> bool:
    """Update session title"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    try:
        cursor.execute('''
            UPDATE chat_sessions
            SET title = ?, updated_at = ?
            WHERE id = ? AND user_id = ? AND is_deleted = 0
        ''', (title, now, session_id, user_id))
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"[ChatDB] Error updating session: {e}")
        return False
    finally:
        conn.close()

def delete_session(session_id: str, user_id: int) -> bool:
    """Soft delete a session"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    try:
        cursor.execute('''
            UPDATE chat_sessions
            SET is_deleted = 1, updated_at = ?
            WHERE id = ? AND user_id = ?
        ''', (now, session_id, user_id))
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"[ChatDB] Error deleting session: {e}")
        return False
    finally:
        conn.close()

def update_session_time(session_id: str):
    """Update session updated_at timestamp"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    try:
        cursor.execute('''
            UPDATE chat_sessions
            SET updated_at = ?
            WHERE id = ?
        ''', (now, session_id))
        
        conn.commit()
    finally:
        conn.close()

# ============================================
# Message Operations
# ============================================

def add_message(session_id: str, message_id: str, role: str, content: str) -> bool:
    """Add a message to a session"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    try:
        cursor.execute('''
            INSERT INTO chat_messages (id, session_id, role, content, timestamp)
            VALUES (?, ?, ?, ?, ?)
        ''', (message_id, session_id, role, content, now))
        
        # Update session timestamp
        cursor.execute('''
            UPDATE chat_sessions SET updated_at = ? WHERE id = ?
        ''', (now, session_id))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"[ChatDB] Error adding message: {e}")
        return False
    finally:
        conn.close()

def get_messages(session_id: str, limit: int = 100, offset: int = 0) -> List[Dict]:
    """Get messages for a session"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, session_id, role, content, timestamp
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY timestamp ASC
        LIMIT ? OFFSET ?
    ''', (session_id, limit, offset))
    
    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return messages

def get_recent_messages(session_id: str, limit: int = 20) -> List[Dict]:
    """Get recent messages for a session (for AI context)"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, session_id, role, content, timestamp
        FROM chat_messages
        WHERE session_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    ''', (session_id, limit))
    
    messages = [dict(row) for row in cursor.fetchall()]
    # Reverse to get chronological order
    messages.reverse()
    conn.close()
    return messages

def delete_message(message_id: str, session_id: str) -> bool:
    """Delete a specific message"""
    conn = get_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            DELETE FROM chat_messages
            WHERE id = ? AND session_id = ?
        ''', (message_id, session_id))
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"[ChatDB] Error deleting message: {e}")
        return False
    finally:
        conn.close()

def get_message_count(session_id: str) -> int:
    """Get total message count for a session"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT COUNT(*) as count FROM chat_messages WHERE session_id = ?
    ''', (session_id,))
    
    result = cursor.fetchone()
    conn.close()
    return result['count'] if result else 0

# ============================================
# Summary Operations
# ============================================

def get_summary(session_id: str) -> Optional[str]:
    """Get summary for a session"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT summary FROM chat_summaries WHERE session_id = ?
    ''', (session_id,))
    
    row = cursor.fetchone()
    conn.close()
    return row['summary'] if row else None

def save_summary(session_id: str, summary: str, message_count: int) -> bool:
    """Save or update summary for a session"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    try:
        cursor.execute('''
            INSERT OR REPLACE INTO chat_summaries (session_id, summary, message_count, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, summary, message_count, now, now))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"[ChatDB] Error saving summary: {e}")
        return False
    finally:
        conn.close()

# ============================================
# AI Session / System State Operations
# ============================================

def get_ai_session(user_id: int) -> Optional[Dict]:
    """Get AI session (System State) for a user"""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT id, user_id, current_project, current_step, last_action, last_action_time, metadata, created_at, updated_at
        FROM ai_sessions
        WHERE user_id = ?
    ''', (user_id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if row:
        result = dict(row)
        if result.get('metadata'):
            result['metadata'] = json.loads(result['metadata'])
        return result
    return None

def save_ai_session(user_id: int, session_id: str, current_project: str = None, 
                    current_step: str = None, last_action: str = None, metadata: dict = None) -> bool:
    """Save or update AI session (System State)"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    try:
        # Get existing session to preserve data
        existing = get_ai_session(user_id)
        
        if existing:
            # Update existing
            cursor.execute('''
                UPDATE ai_sessions
                SET current_project = ?, current_step = ?, last_action = ?, 
                    last_action_time = ?, metadata = ?, updated_at = ?
                WHERE user_id = ?
            ''', (
                current_project if current_project is not None else existing.get('current_project'),
                current_step if current_step is not None else existing.get('current_step'),
                last_action if last_action is not None else existing.get('last_action'),
                now if last_action else existing.get('last_action_time'),
                json.dumps(metadata) if metadata else existing.get('metadata'),
                now,
                user_id
            ))
        else:
            # Insert new
            cursor.execute('''
                INSERT INTO ai_sessions (id, user_id, current_project, current_step, last_action, last_action_time, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                user_id,
                current_project,
                current_step,
                last_action,
                now if last_action else now,
                json.dumps(metadata) if metadata else None,
                now,
                now
            ))
        
        conn.commit()
        return True
    except Exception as e:
        print(f"[ChatDB] Error saving AI session: {e}")
        return False
    finally:
        conn.close()

def update_system_state(user_id: int, **kwargs) -> bool:
    """Update specific fields in system state"""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().isoformat()
    
    try:
        existing = get_ai_session(user_id)
        if not existing:
            # FIX: Auto-create AI session for new users instead of returning False
            # This fixes 500 error when user has no AI session yet
            import uuid
            session_id = str(uuid.uuid4())
            
            cursor.execute('''
                INSERT INTO ai_sessions (id, user_id, current_project, current_step, last_action, last_action_time, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                session_id,
                user_id,
                kwargs.get('current_project'),
                kwargs.get('current_step'),
                kwargs.get('last_action'),
                now if kwargs.get('last_action') else None,
                json.dumps(kwargs.get('metadata')) if kwargs.get('metadata') else None,
                now,
                now
            ))
            conn.commit()
            return True
        
        updates = []
        values = []
        
        for key in ['current_project', 'current_step', 'last_action']:
            if key in kwargs:
                updates.append(f"{key} = ?")
                values.append(kwargs[key])
        
        if 'metadata' in kwargs:
            updates.append("metadata = ?")
            values.append(json.dumps(kwargs['metadata']))
        
        if 'last_action' in kwargs:
            updates.append("last_action_time = ?")
            values.append(now)
        
        updates.append("updated_at = ?")
        values.append(now)
        values.append(user_id)
        
        query = f"UPDATE ai_sessions SET {', '.join(updates)} WHERE user_id = ?"
        cursor.execute(query, values)
        
        conn.commit()
        return cursor.rowcount > 0
    except Exception as e:
        print(f"[ChatDB] Error updating system state: {e}")
        return False
    finally:
        conn.close()

# ============================================
# Search Operations
# ============================================

def search_messages(user_id: int, query: str, limit: int = 50) -> List[Dict]:
    """
    Search messages across all user sessions
    Enhanced version with relevance scoring and metadata
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # FIX: Escape LIKE special characters to prevent pattern matching abuse
    # This prevents queries like "%test%" from matching everything
    escaped_query = query.replace('\\', '\\\\').replace('%', '\\%').replace('_', '\\_')
    search_pattern = f'%{escaped_query}%'
    
    cursor.execute('''
        SELECT m.id, m.session_id, m.role, m.content, m.timestamp, s.title
        FROM chat_messages m
        JOIN chat_sessions s ON m.session_id = s.id
        WHERE s.user_id = ? AND s.is_deleted = 0 AND m.content LIKE ? ESCAPE '\\'
        ORDER BY m.timestamp DESC
        LIMIT ?
    ''', (user_id, search_pattern, limit))
    
    raw_results = cursor.fetchall()
    conn.close()
    
    # Process results with relevance scoring
    results = []
    query_lower = query.lower()
    
    for row in raw_results:
        result = dict(row)
        content_lower = result['content'].lower()
        
        # Calculate relevance score
        relevance = 0.5  # base score
        if query_lower in content_lower:
            relevance += 0.3
            # Bonus for exact match at start
            if content_lower.startswith(query_lower):
                relevance += 0.2
            # Bonus for containing both user and AI messages about the topic
        
        # Extract highlight (50 chars before and after match)
        content = result['content']
        idx = content.lower().find(query_lower)
        if idx >= 0:
            start = max(0, idx - 30)
            end = min(len(content), idx + len(query) + 30)
            highlight = content[start:end]
            if start > 0:
                highlight = '...' + highlight
            if end < len(content):
                highlight += '...'
            result['highlight'] = highlight
        else:
            result['highlight'] = content[:60] + '...' if len(content) > 60 else content
        
        result['relevance_score'] = min(relevance, 1.0)
        results.append(result)
    
    # Sort by relevance score
    results.sort(key=lambda x: x['relevance_score'], reverse=True)
    
    return results

# ============================================
# Export Operations
# ============================================

def export_session(session_id: str, user_id: int) -> Optional[Dict]:
    """Export a full session with messages"""
    session = get_session(session_id, user_id)
    if not session:
        return None
    
    messages = get_messages(session_id, limit=10000)
    summary = get_summary(session_id)
    
    return {
        'session': session,
        'messages': messages,
        'summary': summary
    }

# Initialize database on import
init_chat_db()