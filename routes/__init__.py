# routes/__init__.py
"""
Flask Blueprints for modular route organization with API versioning

Structure:
- routes/auth_routes.py    - Login, logout, profile, session management
- routes/api_routes.py     - Projects, codes, notices APIs
- routes/ai_routes.py      - AI (Gemini, Ollama, OpenRouter) APIs
- routes/socket_routes.py  - Socket API (replaces TCP socket)
- routes/tool_routes.py    - Tool Open integration

API Versioning:
- /api/v1/* - Version 1 of the API
- /api/*    - Legacy endpoints (for backward compatibility)
"""
from flask import Blueprint

# Import individual route modules
from . import auth_routes
from . import api_routes
from . import ai_routes
from . import socket_routes
from . import tool_routes

# Export blueprints
auth_bp = auth_routes.auth_bp
api_bp = api_routes.api_bp
ai_bp = ai_routes.ai_bp
socket_bp = socket_routes.socket_bp
tool_bp = tool_routes.tool_bp


def register_all_blueprints(app, config=None):
    """
    Register all blueprints with the Flask app.
    
    Args:
        app: Flask application instance
        config: Optional configuration dict for route initialization
    
    Returns:
        Dictionary of registered blueprints
    """
    registered = {}
    
    # Register auth routes
    app.register_blueprint(auth_bp)
    registered['auth'] = auth_bp
    
    # Register API routes
    app.register_blueprint(api_bp)
    registered['api'] = api_bp
    
    # Register AI routes
    app.register_blueprint(ai_bp)
    registered['ai'] = ai_bp
    
    # Register socket routes
    app.register_blueprint(socket_bp)
    registered['socket'] = socket_bp
    
    # Register tool routes
    app.register_blueprint(tool_bp)
    registered['tool'] = tool_bp
    
    return registered


def register_v1_blueprints(app, config=None):
    """
    Register all blueprints under /api/v1 prefix for API versioning.
    
    Args:
        app: Flask application instance
        config: Optional configuration dict
    
    Returns:
        Dictionary of registered blueprints
    """
    registered = {}
    
    # Create a version 1 blueprint that prefixes all routes
    api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')
    
    @api_v1_bp.route('/health', methods=['GET'])
    def v1_health():
        """API v1 health check"""
        from flask import jsonify
        return jsonify({
            'status': 'ok',
            'version': 'v1',
            'endpoints': {
                'auth': '/auth',
                'projects': '/projects',
                'codes': '/codes',
                'notices': '/notices',
                'ai': '/ai'
            }
        })
    
    # Register the v1 blueprint
    app.register_blueprint(api_v1_bp)
    registered['api_v1'] = api_v1_bp
    
    return registered


# Export all blueprints
__all__ = [
    'auth_bp',
    'api_bp', 
    'ai_bp',
    'socket_bp',
    'tool_bp',
    'register_all_blueprints',
    'register_v1_blueprints'
]