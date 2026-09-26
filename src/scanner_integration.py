import os

import requests
from flask import Response, jsonify, request, send_from_directory


def register_scanner_routes(app, base_dir):
    scanner_frontend_dist = os.path.abspath(
        os.path.join(base_dir, '..', 'folderscaner', 'frontend', 'dist')
    )
    scanner_backend_url = os.getenv('SCANNER_BACKEND_URL', 'http://127.0.0.1:18001').rstrip('/')

    @app.route('/scanner/')
    @app.route('/scanner/<path:filename>')
    def serve_scanner(filename='index.html'):
        """Serve the Folder Scanner React build under the unified 8001 port."""
        if not os.path.isdir(scanner_frontend_dist):
            return (
                "Folder Scanner UI has not been built yet. Run Start_Pro_Scanner.py "
                "or npm run build inside folderscaner/frontend.",
                503,
            )

        requested = os.path.join(scanner_frontend_dist, filename)
        if os.path.isfile(requested):
            return send_from_directory(scanner_frontend_dist, filename)
        return send_from_directory(scanner_frontend_dist, 'index.html')

    @app.route('/scanner-api', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
    @app.route('/scanner-api/<path:path>', methods=['GET', 'POST', 'PUT', 'PATCH', 'DELETE', 'OPTIONS'])
    def proxy_scanner_api(path):
        """Proxy Scanner API requests to the internal FastAPI backend."""
        backend_path = '/health' if path == 'health' else f'/api/{path}'.rstrip('/')
        target_url = f"{scanner_backend_url}{backend_path}"
        if request.query_string:
            target_url = f"{target_url}?{request.query_string.decode('utf-8', errors='ignore')}"

        headers = {
            key: value
            for key, value in request.headers.items()
            if key.lower() not in {'host', 'content-length', 'connection'}
        }

        try:
            upstream = requests.request(
                request.method,
                target_url,
                headers=headers,
                data=request.get_data(),
                timeout=30,
            )
        except requests.RequestException as exc:
            return jsonify({
                "error": "scanner_backend_unavailable",
                "message": str(exc),
                "target": scanner_backend_url,
            }), 502

        excluded_headers = {'content-encoding', 'content-length', 'transfer-encoding', 'connection'}
        response_headers = [
            (key, value)
            for key, value in upstream.headers.items()
            if key.lower() not in excluded_headers
        ]
        return Response(upstream.content, status=upstream.status_code, headers=response_headers)

    @app.route('/scanner-ws/<path:path>')
    def scanner_ws_not_available(path):
        return jsonify({
            "error": "scanner_websocket_requires_asgi_proxy",
            "message": (
                "Scanner HTTP APIs are available on /scanner-api. Realtime websocket "
                "is disabled in the Flask-only unified port mode."
            ),
        }), 426
