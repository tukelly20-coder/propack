# -*- coding: utf-8 -*-
"""
CORS Helper Module - Giảm duplicate code cho CORS và OPTIONS handling
Cung cấp decorator @cross_origin và helper function để wrap response với CORS headers

Usage:
    from src.cors_helper import cross_origin
    
    @cross_origin()
    def your_endpoint():
        return jsonify(...)
"""

from functools import wraps
from flask import make_response, request


# Default CORS headers
DEFAULT_CORS_ORIGIN = '*'
DEFAULT_CORS_METHODS = 'POST, GET, OPTIONS'
DEFAULT_CORS_HEADERS = 'Content-Type, Authorization'

# Các headers CORS thường dùng
CORS_HEADERS = {
    'Access-Control-Allow-Origin': DEFAULT_CORS_ORIGIN,
    'Access-Control-Allow-Methods': DEFAULT_CORS_METHODS,
    'Access-Control-Allow-Headers': DEFAULT_CORS_HEADERS,
    'Access-Control-Max-Age': '3600',  # Cache preflight request trong 1 giờ
}


def cross_origin(
    origin: str = DEFAULT_CORS_ORIGIN,
    methods: str = DEFAULT_CORS_METHODS,
    headers: str = DEFAULT_CORS_HEADERS,
    max_age: int = 3600
):
    """
    Decorator để tự động thêm CORS headers vào Flask endpoint.
    
    Args:
        origin: Giá trị Access-Control-Allow-Origin (default: '*')
        methods: Giá trị Access-Control-Allow-Methods (default: 'POST, GET, OPTIONS')
        headers: Giá trị Access-Control-Allow-Headers (default: 'Content-Type, Authorization')
        max_age: Giá trị Access-Control-Max-Age cho preflight cache (default: 3600 seconds)
    
    Returns:
        Decorator function
    
    Usage:
        @cross_origin()
        def your_endpoint():
            return jsonify(...)
        
        @cross_origin(methods='GET, POST, PUT, DELETE', headers='Content-Type, Authorization, X-Custom-Header')
        def another_endpoint():
            return jsonify(...)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Xử lý preflight OPTIONS request
            if request.method == 'OPTIONS':
                response = make_response('')
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Methods'] = methods
                response.headers['Access-Control-Allow-Headers'] = headers
                response.headers['Access-Control-Max-Age'] = str(max_age)
                return response
            
            # Gọi function gốc và thêm CORS headers vào response
            response = f(*args, **kwargs)
            
            # Nếu response là Response object, thêm headers trực tiếp
            if hasattr(response, 'headers'):
                response.headers['Access-Control-Allow-Origin'] = origin
                response.headers['Access-Control-Allow-Methods'] = methods
                response.headers['Access-Control-Allow-Headers'] = headers
            
            return response
        
        return decorated_function
    return decorator


def add_cors_headers(response):
    """
    Helper function để thêm CORS headers vào response object.
    
    Args:
        response: Flask response object hoặc tuple (data, status_code)
    
    Returns:
        Response object với CORS headers đã được thêm
    
    Usage:
        response = make_response(jsonify(...))
        return add_cors_headers(response)
    """
    response.headers['Access-Control-Allow-Origin'] = DEFAULT_CORS_ORIGIN
    response.headers['Access-Control-Allow-Methods'] = DEFAULT_CORS_METHODS
    response.headers['Access-Control-Allow-Headers'] = DEFAULT_CORS_HEADERS
    response.headers['Access-Control-Max-Age'] = '3600'
    return response


def options_response(message: str = '', status_code: int = 200):
    """
    Tạo response cho OPTIONS request với CORS headers.
    
    Args:
        message: Message trong response body (default: '')
        status_code: HTTP status code (default: 200)
    
    Returns:
        Flask Response object với CORS headers
    
    Usage:
        @app.route('/api/endpoint', methods=['OPTIONS'])
        def endpoint_options():
            return options_response()
    """
    response = make_response(message, status_code)
    response.headers['Access-Control-Allow-Origin'] = DEFAULT_CORS_ORIGIN
    response.headers['Access-Control-Allow-Methods'] = DEFAULT_CORS_METHODS
    response.headers['Access-Control-Allow-Headers'] = DEFAULT_CORS_HEADERS
    response.headers['Access-Control-Max-Age'] = '3600'
    return response


def cors_response(data, status_code: int = 200, message: str = 'success', **extra_headers):
    """
    Tạo response chuẩn với CORS headers (dùng cho API responses).
    
    Args:
        data: Data trả về (dict, list, hoặc giá trị khác)
        status_code: HTTP status code (default: 200)
        message: Message mô tả (default: 'success')
        **extra_headers: Các headers bổ sung nếu cần
    
    Returns:
        Flask Response object với CORS headers và JSON body
    
    Usage:
        return cors_response({'key': 'value'}, message='Operation completed')
    """
    from flask import jsonify
    
    response = make_response(jsonify({
        'status': status_code,
        'message': message,
        'data': data
    }), status_code)
    
    # Thêm CORS headers
    response.headers['Access-Control-Allow-Origin'] = DEFAULT_CORS_ORIGIN
    response.headers['Access-Control-Allow-Methods'] = DEFAULT_CORS_METHODS
    response.headers['Access-Control-Allow-Headers'] = DEFAULT_CORS_HEADERS
    
    # Thêm các headers bổ sung
    for key, value in extra_headers.items():
        response.headers[key] = value
    
    return response


def error_response(message: str, status_code: int = 400, **extra_headers):
    """
    Tạo error response với CORS headers.
    
    Args:
        message: Error message
        status_code: HTTP status code (default: 400)
        **extra_headers: Các headers bổ sung nếu cần
    
    Returns:
        Flask Response object với CORS headers và error JSON body
    """
    from flask import jsonify
    
    response = make_response(jsonify({
        'status': status_code,
        'message': message,
        'error': True
    }), status_code)
    
    # Thêm CORS headers
    response.headers['Access-Control-Allow-Origin'] = DEFAULT_CORS_ORIGIN
    response.headers['Access-Control-Allow-Methods'] = DEFAULT_CORS_METHODS
    response.headers['Access-Control-Allow-Headers'] = DEFAULT_CORS_HEADERS
    
    # Thêm các headers bổ sung
    for key, value in extra_headers.items():
        response.headers[key] = value
    
    return response


# Export các hàm và constants để dễ import
__all__ = [
    'cross_origin',
    'add_cors_headers',
    'options_response',
    'cors_response',
    'error_response',
    'DEFAULT_CORS_ORIGIN',
    'DEFAULT_CORS_METHODS',
    'DEFAULT_CORS_HEADERS',
    'CORS_HEADERS',
]