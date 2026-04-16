# -*- coding: utf-8 -*-
"""
AI Memory Module - Vector-based long-term memory for AI
Provides: Session cache, Short-term store, Vector DB + RAG
"""

import sqlite3
import os
import json
import sys
import uuid
import hashlib
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from collections import OrderedDict

# Database file path - use appropriate location for PyInstaller
def _get_app_dir():
    """Get application directory - works with both script and PyInstaller"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        return os.path.dirname(sys.executable)
    else:
        # Running as script
        return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

MEMORY_DB_PATH = os.path.join(_get_app_dir(), 'ai_memory.db')

# Configuration
CONFIG = {
    'session_cache_size': 100,  # Max messages in session cache
    'short_term_ttl_days': 7,   # Short-term memory TTL
    'vector_top_k': 5,          # Number of results to retrieve
    'embedding_dim': 1536,      # OpenAI ada-002 dimension
}

# In-memory session cache (Layer 1)
_session_cache: OrderedDict = OrderedDict()
_cache_lock = None

def _get_cache_lock():
    """Get or create cache lock"""
    global _cache_lock
    if _cache_lock is None:
        import threading
        _cache_lock = threading.Lock()
    return _cache_lock

def get_memory_connection():
    """Get SQLite memory database connection"""
    conn = sqlite3.connect(MEMORY_DB_PATH, check_same_thread=False, timeout=30)
    conn.row_factory = sqlite3.Row
    return conn

def init_ai_memory():
    """Initialize AI Memory database with tables"""
    conn = get_memory_connection()
    cursor = conn.cursor()
    
    # Layer 2: Short-term memory (with TTL)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS short_term_memory (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            project_id TEXT,
            session_id TEXT,
            content TEXT NOT NULL,
            metadata TEXT,
            created_at TEXT NOT NULL,
            expires_at TEXT,
            is_locked INTEGER DEFAULT 0
        )
    ''')
    
    # Layer 3: Long-term memory (Vector store - simplified without actual vectors)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS long_term_memory (
            id TEXT PRIMARY KEY,
            user_id INTEGER NOT NULL,
            project_id TEXT,
            role TEXT,
            content TEXT NOT NULL,
            content_hash TEXT,
            metadata TEXT,
            embedding_id TEXT,
            created_at TEXT NOT NULL,
            is_locked INTEGER DEFAULT 0
        )
    ''')
    
    # Memory metadata
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory_metadata (
            id TEXT PRIMARY KEY,
            memory_id TEXT NOT NULL,
            key TEXT NOT NULL,
            value TEXT,
            created_at TEXT NOT NULL
        )
    ''')
    
    # User consent for long-term storage
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS memory_consents (
            user_id INTEGER PRIMARY KEY,
            long_term_storage INTEGER DEFAULT 0,
            consent_date TEXT,
            revoked_date TEXT
        )
    ''')
    
    # Indexes
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stm_user ON short_term_memory(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_stm_expires ON short_term_memory(expires_at)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ltm_user ON long_term_memory(user_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ltm_project ON long_term_memory(project_id)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_ltm_hash ON long_term_memory(content_hash)')
    cursor.execute('CREATE INDEX IF NOT EXISTS idx_meta_memory ON memory_metadata(memory_id)')
    
    conn.commit()
    conn.close()
    print("[AIMemory] Database initialized successfully")

# ============================================
# Layer 1: Session Cache (In-memory)
# ============================================

def add_to_session_cache(session_id: str, role: str, content: str) -> None:
    """Add message to session cache (Layer 1)"""
    with _get_cache_lock():
        cache_key = f"session_{session_id}"
        
        if cache_key not in _session_cache:
            _session_cache[cache_key] = OrderedDict()
        
        # Add message
        msg_id = str(uuid.uuid4())
        _session_cache[cache_key][msg_id] = {
            'id': msg_id,
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        
        # Limit cache size
        if len(_session_cache[cache_key]) > CONFIG['session_cache_size']:
            # Remove oldest
            _session_cache[cache_key].popitem(last=False)

def get_session_cache(session_id: str, limit: int = 20) -> List[Dict]:
    """Get messages from session cache"""
    with _get_cache_lock():
        cache_key = f"session_{session_id}"
        if cache_key not in _session_cache:
            return []
        
        messages = list(_session_cache[cache_key].values())
        # Return most recent
        return messages[-limit:] if len(messages) > limit else messages

def clear_session_cache(session_id: str) -> None:
    """Clear session cache"""
    with _get_cache_lock():
        cache_key = f"session_{session_id}"
        if cache_key in _session_cache:
            del _session_cache[cache_key]

# ============================================
# Layer 2: Short-term Memory (DB + TTL)
# ============================================

def add_short_term_memory(user_id: int, content: str, project_id: str = None, 
                          session_id: str = None, metadata: dict = None) -> str:
    """Add to short-term memory with TTL"""
    conn = get_memory_connection()
    cursor = conn.cursor()
    
    memory_id = str(uuid.uuid4())
    now = datetime.now()
    expires = now + timedelta(days=CONFIG['short_term_ttl_days'])
    
    cursor.execute('''
        INSERT INTO short_term_memory (id, user_id, project_id, session_id, content, metadata, created_at, expires_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (memory_id, user_id, project_id, session_id, content, json.dumps(metadata) if metadata else None,
          now.isoformat(), expires.isoformat()))
    
    conn.commit()
    conn.close()
    
    return memory_id

def get_short_term_memory(user_id: int, project_id: str = None, limit: int = 10) -> List[Dict]:
    """Get short-term memories for user/project"""
    conn = get_memory_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    if project_id:
        cursor.execute('''
            SELECT * FROM short_term_memory
            WHERE user_id = ? AND project_id = ? AND expires_at > ? AND is_locked = 0
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, project_id, now, limit))
    else:
        cursor.execute('''
            SELECT * FROM short_term_memory
            WHERE user_id = ? AND expires_at > ? AND is_locked = 0
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, now, limit))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    # Parse metadata
    for r in results:
        if r.get('metadata'):
            r['metadata'] = json.loads(r['metadata'])
    
    return results

def clean_expired_short_term() -> int:
    """Clean expired short-term memories"""
    conn = get_memory_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    cursor.execute('DELETE FROM short_term_memory WHERE expires_at <= ?', (now,))
    
    deleted = cursor.rowcount
    conn.commit()
    conn.close()
    
    return deleted

# ============================================
# Layer 3: Long-term Memory (Vector DB + RAG)
# ============================================

def add_long_term_memory(user_id: int, content: str, role: str = None, 
                         project_id: str = None, metadata: dict = None,
                         embedding_id: str = None) -> str:
    """Add to long-term memory (requires embedding)"""
    conn = get_memory_connection()
    cursor = conn.cursor()
    
    memory_id = str(uuid.uuid4())
    content_hash = hashlib.sha256(content.encode()).hexdigest()
    now = datetime.now().isoformat()
    
    # Check if content already exists (deduplication)
    cursor.execute('SELECT id FROM long_term_memory WHERE content_hash = ? AND user_id = ?', 
                  (content_hash, user_id))
    if cursor.fetchone():
        conn.close()
        return None  # Already exists
    
    cursor.execute('''
        INSERT INTO long_term_memory (id, user_id, project_id, role, content, content_hash, metadata, embedding_id, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (memory_id, user_id, project_id, role, content, content_hash, 
          json.dumps(metadata) if metadata else None, embedding_id, now))
    
    conn.commit()
    conn.close()
    
    return memory_id

def search_long_term_memory(user_id: int, query: str, project_id: str = None, 
                            limit: int = 5) -> List[Dict]:
    """
    Search long-term memory (simplified RAG without actual embeddings)
    Uses content matching + keyword scoring
    """
    conn = get_memory_connection()
    cursor = conn.cursor()
    
    # Prepare search terms
    query_lower = query.lower()
    query_words = set(query_lower.split())
    
    if project_id:
        cursor.execute('''
            SELECT * FROM long_term_memory
            WHERE user_id = ? AND project_id = ? AND is_locked = 0
            ORDER BY created_at DESC
        ''', (user_id, project_id))
    else:
        cursor.execute('''
            SELECT * FROM long_term_memory
            WHERE user_id = ? AND is_locked = 0
            ORDER BY created_at DESC
        ''', (user_id,))
    
    results = []
    for row in cursor.fetchall():
        memory = dict(row)
        content_lower = memory['content'].lower()
        
        # Calculate relevance score
        score = 0
        
        # Exact match bonus
        if query_lower in content_lower:
            score += 0.5
        
        # Keyword match
        content_words = set(content_lower.split())
        word_overlap = len(query_words & content_words)
        score += min(word_overlap * 0.1, 0.3)
        
        # Recent bonus
        created = datetime.fromisoformat(memory['created_at'])
        days_ago = (datetime.now() - created).days
        if days_ago < 7:
            score += 0.2
        elif days_ago < 30:
            score += 0.1
        
        if score > 0:
            memory['relevance_score'] = min(score, 1.0)
            memory['metadata'] = json.loads(memory['metadata']) if memory.get('metadata') else None
            results.append(memory)
    
    conn.close()
    
    # Sort by score and limit
    results.sort(key=lambda x: x['relevance_score'], reverse=True)
    return results[:limit]

def get_user_long_term_memories(user_id: int, project_id: str = None, limit: int = 50) -> List[Dict]:
    """Get all long-term memories for user"""
    conn = get_memory_connection()
    cursor = conn.cursor()
    
    if project_id:
        cursor.execute('''
            SELECT * FROM long_term_memory
            WHERE user_id = ? AND project_id = ? AND is_locked = 0
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, project_id, limit))
    else:
        cursor.execute('''
            SELECT * FROM long_term_memory
            WHERE user_id = ? AND is_locked = 0
            ORDER BY created_at DESC
            LIMIT ?
        ''', (user_id, limit))
    
    results = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    for r in results:
        if r.get('metadata'):
            r['metadata'] = json.loads(r['metadata'])
    
    return results

# ============================================
# Memory Management (Lock/Unlock/Delete)
# ============================================

def lock_memory(memory_id: str, user_id: int) -> bool:
    """Lock a memory (prevent deletion)"""
    conn = get_memory_connection()
    cursor = conn.cursor()
    
    # Try short-term first
    cursor.execute('UPDATE short_term_memory SET is_locked = 1 WHERE id = ? AND user_id = ?', 
                   (memory_id, user_id))
    if cursor.rowcount > 0:
        conn.commit()
        conn.close()
        return True
    
    # Try long-term
    cursor.execute('UPDATE long_term_memory SET is_locked = 1 WHERE id = ? AND user_id = ?', 
                   (memory_id, user_id))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def unlock_memory(memory_id: str, user_id: int) -> bool:
    """Unlock a memory"""
    conn = get_memory_connection()
    cursor = conn.cursor()
    
    cursor.execute('UPDATE short_term_memory SET is_locked = 0 WHERE id = ? AND user_id = ?', 
                   (memory_id, user_id))
    if cursor.rowcount > 0:
        conn.commit()
        conn.close()
        return True
    
    cursor.execute('UPDATE long_term_memory SET is_locked = 0 WHERE id = ? AND user_id = ?', 
                   (memory_id, user_id))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

def delete_memory(memory_id: str, user_id: int) -> bool:
    """Delete a memory (only if not locked)"""
    conn = get_memory_connection()
    cursor = conn.cursor()
    
    # Short-term
    cursor.execute('DELETE FROM short_term_memory WHERE id = ? AND user_id = ? AND is_locked = 0', 
                   (memory_id, user_id))
    if cursor.rowcount > 0:
        conn.commit()
        conn.close()
        return True
    
    # Long-term
    cursor.execute('DELETE FROM long_term_memory WHERE id = ? AND user_id = ? AND is_locked = 0', 
                   (memory_id, user_id))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

# ============================================
# User Consent Management
# ============================================

def set_user_consent(user_id: int, long_term_storage: bool) -> bool:
    """Set user consent for long-term storage"""
    conn = get_memory_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT OR REPLACE INTO memory_consents (user_id, long_term_storage, consent_date, revoked_date)
        VALUES (?, ?, ?, NULL)
    ''', (user_id, 1 if long_term_storage else 0, now))
    
    conn.commit()
    conn.close()
    return True

def get_user_consent(user_id: int) -> Optional[Dict]:
    """Get user consent status"""
    conn = get_memory_connection()
    cursor = conn.cursor()
    
    cursor.execute('SELECT * FROM memory_consents WHERE user_id = ?', (user_id,))
    row = cursor.fetchone()
    conn.close()
    
    return dict(row) if row else None

def revoke_consent(user_id: int) -> bool:
    """Revoke user consent (memory will remain but no new long-term storage)"""
    conn = get_memory_connection()
    cursor = conn.cursor()
    
    now = datetime.now().isoformat()
    cursor.execute('''
        UPDATE memory_consents SET long_term_storage = 0, revoked_date = ?
        WHERE user_id = ?
    ''', (now, user_id))
    
    success = cursor.rowcount > 0
    conn.commit()
    conn.close()
    
    return success

# ============================================
# RAG Context Assembly
# ============================================

def assemble_memory_context(user_id: int, project_id: str = None, query: str = None) -> str:
    """
    Assemble memory context for AI prompt
    Combines: session cache + short-term + long-term (RAG)
    """
    parts = []
    
    # Layer 1: Session context (if query provided)
    # Note: Session cache is handled separately by chat_service
    
    # Layer 2: Short-term memory
    short_term = get_short_term_memory(user_id, project_id, limit=5)
    if short_term:
        parts.append("## BỘ NHỚ NGẮN HẠN")
        for mem in short_term:
            content = mem['content'][:200]
            parts.append(f"- {content}")
    
    # Layer 3: Long-term memory (RAG)
    if query:
        long_term = search_long_term_memory(user_id, query, project_id, limit=CONFIG['vector_top_k'])
        if long_term:
            parts.append("\n## BỘ NHỚ DÀI HẠN (Liên quan)")
            for i, mem in enumerate(long_term, 1):
                content = mem['content'][:300]
                role = mem.get('role', '')
                parts.append(f"{i}. [{role}] {content}")
    
    return "\n".join(parts) if parts else ""

# ============================================
# Initialization
# ============================================

# Initialize on import
init_ai_memory()