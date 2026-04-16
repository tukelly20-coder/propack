# -*- coding: utf-8 -*-
"""
Notice Routes - Endpoints cho Notice/Pending Tab
Tách ra từ server.py (dòng 907-1006)
"""
from flask import request, jsonify


def register_routes(app, db_functions):
    """
    Register notice-related routes.
    
    Args:
        app: Flask application instance
        db_functions: Dictionary containing database helper functions
    """
    get_pending_notices = db_functions.get('get_pending_notices')
    get_pending_count = db_functions.get('get_pending_count')
    get_all_notices_for_engineer = db_functions.get('get_all_notices_for_engineer')
    accept_job = db_functions.get('accept_job')
    
    @app.route('/api/notices/pending', methods=['GET'])
    def api_notices_pending():
        """Lấy danh sách thông báo chờ xử lý"""
        user_id_str = request.args.get('user_id')
        user_id = int(user_id_str) if user_id_str and user_id_str.isdigit() else None
        
        try:
            notices = get_pending_notices(user_id)
            return jsonify({
                "success": True,
                "data": notices,
                "total": len(notices)
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    @app.route('/api/notices/count', methods=['GET'])
    def api_notices_count():
        """Lấy số lượng thông báo chờ"""
        user_id_str = request.args.get('user_id')
        user_id = int(user_id_str) if user_id_str and user_id_str.isdigit() else None
        
        try:
            count = get_pending_count(user_id)
            return jsonify({
                "success": True,
                "count": count
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    @app.route('/api/notices/engineer', methods=['GET'])
    def api_notices_engineer():
        """Lấy tất cả thông báo cho kỹ sư (pending + accepted)"""
        engineer_name = request.args.get('engineer_name')
        
        if not engineer_name:
            return jsonify({
                "success": False,
                "error": "Thiếu tên kỹ sư"
            }), 400
        
        try:
            notices = get_all_notices_for_engineer(engineer_name)
            return jsonify({
                "success": True,
                "data": notices,
                "total": len(notices)
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500


    @app.route('/api/notices/accept', methods=['POST'])
    def api_notices_accept():
        """Kỹ sư nhận job"""
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Dữ liệu không hợp lệ"
            }), 400
        
        tracking_id = data.get('tracking_id')
        engineer_name = data.get('engineer_name')
        
        if not tracking_id or not engineer_name:
            return jsonify({
                "success": False,
                "error": "Thiếu tracking_id hoặc engineer_name"
            }), 400
        
        try:
            success = accept_job(tracking_id, engineer_name)
            if success:
                return jsonify({
                    "success": True,
                    "message": f"Đã nhận job {tracking_id}"
                })
            else:
                return jsonify({
                    "success": False,
                    "error": "Không thể nhận job"
                }), 400
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500