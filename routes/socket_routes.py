# routes/socket_routes.py
"""
Socket API Routes - HTTP endpoints that replace TCP socket for legacy V7 client

These routes handle the same operations as the TCP socket server,
but using HTTP/JSON for better compatibility with modern clients.

Routes:
- POST /api/socket - Main socket API endpoint for all operations
"""
from flask import Blueprint, request, jsonify, Response
from typing import Dict, Any, Optional

socket_bp = Blueprint('socket', __name__, url_prefix='/api')

# Global references (will be set by init)
_db_helpers = None
_code_helpers = None
_sessions_lock = None


def init_socket_routes(db_helpers, code_helpers, sessions_lock=None):
    """Initialize socket routes with database and code helpers"""
    global _db_helpers, _code_helpers, _sessions_lock
    _db_helpers = db_helpers
    _code_helpers = code_helpers
    _sessions_lock = sessions_lock


@socket_bp.route('/socket', methods=['POST'])
def socket_api():
    """
    Main Socket API endpoint - handles all socket operations via HTTP.
    
    Request body should be JSON with:
    - request: operation type (GET_DB_ALL, ADD_DB_RECORD, etc.)
    - other fields depending on the operation
    """
    try:
        req_data = request.get_json()
        if not req_data:
            return jsonify({"success": False, "error": "No data provided"}), 400
        
        request_type = req_data.get('request', 'unknown')
        
        # Import logger
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        try:
            from src.logging_config import get_logger
            logger = get_logger('socket')
            logger.info(f"Request: {request_type}")
        except ImportError:
            pass  # Use default if logging not available
        
        response_data = None
        
        # Placeholder for socket operations
        # Full implementation would mirror the TCP socket handler in server.py
        # This provides the HTTP-based alternative to the TCP socket
        
        if request_type == "PING":
            return "PONG", 200
        
        # Handle other request types...
        response_data = {"success": False, "error": f"Not implemented: {request_type}"}
        
        if response_data is None:
            return jsonify({"success": False, "error": "No response"}), 500
        
        if isinstance(response_data, str):
            return response_data, 200
        
        return jsonify(response_data), 200
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


@socket_bp.route('/socket/status', methods=['GET'])
def socket_status():
    """Get socket API status"""
    return jsonify({
        "status": "ready",
        "version": "1.0",
        "protocol": "http-json",
        "replaces": "tcp-socket"
    })


# Export blueprint
__all__ = ['socket_bp', 'init_socket_routes']