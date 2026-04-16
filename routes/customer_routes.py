# -*- coding: utf-8 -*-
"""
Customer Routes - Endpoints cho Customer API
Tách ra từ server.py (dòng 864-900)
"""
from flask import request, jsonify
import sqlite3


def register_routes(app):
    """
    Register customer-related routes.
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/api/customers', methods=['GET'])
    def api_customers():
        """Lấy danh sách khách hàng cho dropdown"""
        try:
            conn = sqlite3.connect('DB.db')
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            
            # Lấy tất cả customers với các trường cần thiết
            cursor.execute('''
                SELECT code, name, phonetic, english_name 
                FROM customers 
                WHERE code IS NOT NULL AND code != ''
                ORDER BY code
            ''')
            results = cursor.fetchall()
            conn.close()
            
            customers = []
            for row in results:
                customers.append({
                    'code': row['code'] or '',
                    'name': row['name'] or '',
                    'phonetic': row['phonetic'] or '',
                    'english_name': row['english_name'] or ''
                })
            
            return jsonify({
                "success": True,
                "data": customers,
                "total": len(customers)
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": str(e)
            }), 500