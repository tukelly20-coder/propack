# -*- coding: utf-8 -*-
"""
Log Routes - Endpoint cho Log submission với hỗ trợ upload files
Tách ra từ server.py (dòng 785-855)
"""
from flask import request, jsonify
import datetime
import os

# Import file handler utilities
from utils.file_handler import (
    save_multiple_files,
    ensure_upload_folder,
    format_file_size,
    get_file_type
)


def register_routes(app, session_state):
    """
    Register log submission routes.
    
    Args:
        app: Flask application instance
        session_state: Dictionary containing session management state
            - sessions: session storage dictionary
            - sessions_lock: threading lock for sessions
    """
    sessions = session_state.get('sessions')
    sessions_lock = session_state.get('sessions_lock')
    
    @app.route('/api/logs', methods=['POST'])
    def api_logs():
        """
        Gửi log từ web client với hỗ trợ upload files
        
        Accepts multipart/form-data với các fields:
        - content: Nội dung log (required)
        - type: Loại log (general, error, debug, login)
        - device_info_json: Thông tin thiết bị (JSON string)
        - attachments: Files đính kèm (multiple)
        """
        # Kiểm tra content
        log_content = request.form.get('content', '')
        log_type = request.form.get('type', 'general')
        
        if not log_content:
            return jsonify({"success": False, "error": "Nội dung log trống"}), 400
        
        # Parse device info
        device_info_str = request.form.get('device_info_json', '{}')
        try:
            import json
            device_info = json.loads(device_info_str)
        except:
            device_info = {}
        
        # Get username if authenticated
        username = "anonymous"
        auth_header = request.headers.get('Authorization', '')
        if auth_header.startswith('Bearer '):
            token = auth_header[7:]
            with sessions_lock:
                session_data = sessions.get(token)
                if session_data:
                    username = session_data.get('user', {}).get('username', 'anonymous')
        
        # Get client IP
        client_ip = request.remote_addr
        
        # Create log folder name
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        log_folder = f"web_log_{timestamp}"
        
        # Ensure upload folder exists
        ensure_upload_folder(log_folder)
        
        # Get uploaded files
        files = request.files.getlist('attachments')
        
        # Save files
        saved_files = []
        if files:
            for file in files:
                if file and file.filename:
                    from utils.file_handler import save_uploaded_file
                    result = save_uploaded_file(file, log_folder)
                    if result.get('success'):
                        saved_files.append(result)
        
        # Build device info section
        device_info_section = ""
        if device_info:
            screen_width = device_info.get('screenWidth', 0)
            screen_height = device_info.get('screenHeight', 0)
            device_info_section = f"""=== Thông tin thiết bị ===
Browser: {device_info.get('browserName', 'unknown')} {device_info.get('browserVersion', '')}
OS: {device_info.get('platform', 'unknown')}
Device: {device_info.get('deviceType', 'unknown')}
Screen: {screen_width}x{screen_height}
Language: {device_info.get('language', 'unknown')}
Timezone: {device_info.get('timezone', 'unknown')}
User Agent: {device_info.get('userAgent', '')[:100]}...
Online: {device_info.get('onLine', False)}
Cookie Enabled: {device_info.get('cookieEnabled', False)}

"""
        
        # Build attachments section
        attachments_section = ""
        if saved_files:
            attachments_section = "=== Files đính kèm ===\n"
            for f in saved_files:
                file_type_icon = "🖼️" if f['type'] == 'image' else "🎬"
                attachments_section += f"{file_type_icon} {f['filename']} ({format_file_size(f['size'])})\n"
            attachments_section += "\n"
        
        # Build log entry
        log_entry = f"""=== Web Log Submission ===
Thời gian: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Người dùng: {username}
Loại log: {log_type}
Client IP: {client_ip}
{device_info_section}=== Nội dung ===
{log_content}

{attachments_section}"""
        
        try:
            # Save log file in the same folder as attachments
            log_path = os.path.join('uploads', 'logs', log_folder, 'log.txt')
            with open(log_path, 'w', encoding='utf-8') as f:
                f.write(log_entry)
            
            # Build response
            response_data = {
                "success": True, 
                "message": "Log và files đã được lưu thành công",
                "folder": log_folder,
                "log_file": "log.txt",
                "files_count": len(saved_files),
                "files": [
                    {
                        "filename": f['filename'],
                        "type": f['type'],
                        "size": f['size'],
                        "size_formatted": format_file_size(f['size'])
                    }
                    for f in saved_files
                ]
            }
            
            return jsonify(response_data)
            
        except Exception as e:
            return jsonify({"success": False, "error": f"Lỗi khi lưu log: {str(e)}"}), 500
    
    @app.route('/api/logs/files/<path:filename>', methods=['GET'])
    def api_get_log_file(filename):
        """
        Serve uploaded files for viewing/downloading
        
        Args:
            filename: Relative path from uploads/logs/ (e.g., "web_log_20260330_083329/image.jpg")
        """
        from flask import send_from_directory
        
        # Security: prevent path traversal
        filename = os.path.basename(filename)
        
        upload_dir = os.path.abspath('uploads/logs')
        file_path = os.path.join(upload_dir, filename)
        
        # Ensure file is within upload directory
        if not file_path.startswith(upload_dir):
            return jsonify({"error": "Access denied"}), 403
        
        if not os.path.exists(file_path):
            return jsonify({"error": "File not found"}), 404
        
        # Determine mimetype
        ext = filename.rsplit('.', 1)[-1].lower() if '.' in filename else ''
        mimetype = None
        if ext in ['jpg', 'jpeg']:
            mimetype = 'image/jpeg'
        elif ext in ['png']:
            mimetype = 'image/png'
        elif ext in ['gif']:
            mimetype = 'image/gif'
        elif ext in ['webp']:
            mimetype = 'image/webp'
        elif ext in ['mp4']:
            mimetype = 'video/mp4'
        elif ext in ['webm']:
            mimetype = 'video/webm'
        elif ext in ['mov']:
            mimetype = 'video/quicktime'
        
        return send_from_directory(upload_dir, filename, as_attachment=False)
    
    @app.route('/api/logs', methods=['GET'])
    def api_list_logs():
        """
        Lấy danh sách các logs đã lưu (cho admin/debug)
        """
        from utils.file_handler import get_all_upload_subfolders, get_files_in_subfolder
        
        subfolders = get_all_upload_subfolders()
        
        logs = []
        for folder in subfolders[:50]:  # Limit to 50 most recent
            files_info = get_files_in_subfolder(folder)
            has_log = any(f['filename'] == 'log.txt' for f in files_info)
            if has_log:
                logs.append({
                    'folder': folder,
                    'files': [
                        {
                            'filename': f['filename'],
                            'type': f['type'],
                            'size': f['size'],
                            'size_formatted': format_file_size(f['size'])
                        }
                        for f in files_info
                    ]
                })
        
        return jsonify({
            "success": True,
            "count": len(logs),
            "logs": logs
        })