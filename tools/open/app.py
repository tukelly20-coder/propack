# -*- coding: utf-8 -*-
"""
Flask Server cho Mở mã liệu Web App
Exposes API từ module core để frontend HTML có thể gọi
"""
import sys
import os
import json
import importlib.util
from flask import Flask, request, jsonify, render_template, send_from_directory
from flask_cors import CORS
import threading
import io

# Thread-safe print function to handle closed stdout
_print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    """Thread-safe print that handles closed stdout"""
    try:
        with _print_lock:
            print(*args, **kwargs)
    except (ValueError, OSError):
        # stdout is closed, silently ignore
        pass

# Fix Unicode output for Windows console - with error handling
if sys.platform == 'win32':
    try:
        # Only wrap if not already wrapped and if buffer exists
        if hasattr(sys.stdout, 'buffer') and not isinstance(sys.stdout, io.TextIOWrapper):
            sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        if hasattr(sys.stderr, 'buffer') and not isinstance(sys.stderr, io.TextIOWrapper):
            sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

# ========================================================================
# Import module core an toàn
# ========================================================================
core_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Mở mã liệu 打开链接VP.py")
spec = importlib.util.spec_from_file_location("material_core", core_path)
core = importlib.util.module_from_spec(spec)
sys.modules["material_core"] = core
spec.loader.exec_module(core)

# ========================================================================
# Flask App Setup
# ========================================================================
app = Flask(__name__,
            template_folder='templates',
            static_folder='static')
CORS(app)  # Cho phép cross-origin requests

# Settings file path
SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "user_settings.json")

# ========================================================================
# Helper Functions
# ========================================================================
def load_settings():
    """Đọc cài đặt và lịch sử tìm kiếm từ file JSON"""
    try:
        if os.path.exists(SETTINGS_FILE):
            with open(SETTINGS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('search_history', [])
    except Exception:
        pass
    return []

def save_settings(history):
    """Lưu lịch sử tìm kiếm vào file JSON"""
    try:
        data = {'search_history': history}
        with open(SETTINGS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        safe_print(f"[WARN] Khong the luu cau hinh: {e}")

# ========================================================================
# Routes
# ========================================================================

@app.route('/')
def index():
    """Trang chủ - Hiển thị giao diện HTML"""
    return render_template('index.html')

@app.route('/favicon.ico')
def favicon():
    """Phục vụ file favicon.ico"""
    return send_from_directory(os.path.dirname(os.path.abspath(__file__)), 'favicon.ico', mimetype='image/x-icon')

# ========================================================================
# API Endpoints
# ========================================================================

@app.route('/api/status', methods=['GET'])
def get_status():
    """Kiểm tra trạng thái kết nối"""
    try:
        # Thử kiểm tra kết nối Excel
        excel_path = core.normalize_unc_path(core.EXCEL_PATH)
        excel_exists = os.path.exists(excel_path)
        
        return jsonify({
            "status": "ready" if excel_exists else "error",
            "message": "San sang" if excel_exists else "Khong the ket noi Excel",
            "excel_path": excel_path,
            "excel_exists": excel_exists
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e)
        })

@app.route('/api/search', methods=['POST'])
def search_material():
    """Tìm kiếm mã liệu"""
    data = request.get_json()
    code = data.get('code', '').strip().strip('"').strip("'")
    
    if not code:
        return jsonify({
            "type": "error",
            "message": "Ma khong duoc de trong!"
        })
    
    # Thêm vào lịch sử
    history = load_settings()
    if code in history:
        history.remove(code)
    history.insert(0, code)
    history = history[:20]  # Giới hạn 20 mã
    save_settings(history)
    
    # Kiểm tra định dạng cEngineerFigNo
    if core.is_engineer_fig_no(code):
        all_matches = core.find_cinvcode_from_excel(code, return_all=True)
        
        if not all_matches:
            return jsonify({
                "type": "error",
                "message": f"Khong tim thay cInvCode cho: {code}"
            })
        
        if len(all_matches) == 1:
            # Chỉ có 1 kết quả -> tự động query với cInvCode
            cinv_code = all_matches[0]['cInvCode']
            core.copy_to_clipboard(cinv_code)
            
            # Gọi API
            urls = core.query_material(cinv_code)
            
            if urls:
                return jsonify({
                    "type": "success",
                    "urls": urls,
                    "folder_count": len(set(os.path.dirname(u) for u in urls)),
                    "copied_code": cinv_code,
                    "message": f"Tim thay {len(urls)} files"
                })
            else:
                # Thử fallback
                fallback_path = f"{core.FALLBACK_BASE_PATH}\\{cinv_code}.jpg"
                if os.path.exists(fallback_path):
                    return jsonify({
                        "type": "success",
                        "urls": [fallback_path],
                        "folder_count": 1,
                        "message": "Tim thay file du phong"
                    })
                return jsonify({
                    "type": "error",
                    "message": "Khong tim thay du lieu"
                })
        else:
            # Nhiều kết quả -> trả về danh sách để user chọn
            return jsonify({
                "type": "multiple",
                "matches": all_matches,
                "original_code": code,
                "message": f"Tim thay {len(all_matches)} ket qua"
            })
    
    # Query trực tiếp với code (cInvCode)
    urls = core.query_material(code)
    
    if urls:
        # Copy URLs to clipboard
        urls_text = "\n".join(urls)
        core.copy_to_clipboard(urls_text)
        
        return jsonify({
            "type": "success",
            "urls": urls,
            "folder_count": len(set(os.path.dirname(u) for u in urls)),
            "message": f"Tim thay {len(urls)} files"
        })
    else:
        # Thử fallback
        fallback_path = f"{core.FALLBACK_BASE_PATH}\\{code}.jpg"
        if os.path.exists(fallback_path):
            core.copy_to_clipboard(fallback_path)
            return jsonify({
                "type": "success",
                "urls": [fallback_path],
                "folder_count": 1,
                "message": "Tim thay file du phong"
            })
        
        return jsonify({
            "type": "error",
            "message": f"Khong tim thay du lieu cho ma: {code}"
        })

@app.route('/api/search-multiple', methods=['POST'])
def search_multiple():
    """Tìm kiếm nhiều mã cInvCode cùng lúc"""
    data = request.get_json()
    cinv_codes = data.get('codes', [])
    
    if not cinv_codes:
        return jsonify({
            "type": "error",
            "message": "Danh sach ma trong"
        })
    
    all_urls = []
    
    for cinv_code in cinv_codes:
        urls = core.query_material(cinv_code)
        if urls:
            all_urls.extend(urls)
    
    if all_urls:
        urls_text = "\n".join(all_urls)
        core.copy_to_clipboard(urls_text)
        
        folders = set(os.path.dirname(u) for u in all_urls)
        
        return jsonify({
            "type": "success",
            "urls": all_urls,
            "folder_count": len(folders),
            "message": f"Tim thay {len(all_urls)} files trong {len(folders)} folders"
        })
    
    return jsonify({
        "type": "error",
        "message": "Khong tim thay file nao"
    })

@app.route('/api/history', methods=['GET'])
def get_history():
    """Lấy lịch sử tìm kiếm"""
    history = load_settings()
    return jsonify({"history": history})

@app.route('/api/history', methods=['POST'])
def update_history():
    """Cập nhật lịch sử tìm kiếm"""
    data = request.get_json()
    history = data.get('history', [])
    save_settings(history[:20])
    return jsonify({"success": True})

@app.route('/api/copy', methods=['POST'])
def copy_to_clipboard():
    """Copy text vào clipboard (giả lập - browser sẽ tự xử lý)"""
    data = request.get_json()
    text = data.get('text', '')
    # Trả về text để frontend tự copy
    return jsonify({"text": text, "success": True})

@app.route('/api/get-parent-code', methods=['POST'])
def get_parent_code():
    """
    Tìm cInvCode (mã mẹ) từ mã đầu vào.
    Chỉ trả về cInvCode tìm được, không thực hiện thêm hành động nào khác.
    """
    data = request.get_json()
    code = data.get('code', '').strip().strip('"').strip("'")
    
    if not code:
        return jsonify({
            "success": False,
            "message": "Mã không được để trống!"
        })
    
    try:
        # Kiểm tra nếu là dạng cEngineerFigNo
        if core.is_engineer_fig_no(code):
            # Tìm cInvCode từ Excel
            cinv_code = core.find_cinvcode_from_excel(code, return_all=False)
            
            if cinv_code:
                return jsonify({
                    "success": True,
                    "parent_code": cinv_code,
                    "message": f"Tìm thấy mã mẹ: {cinv_code}"
                })
            else:
                return jsonify({
                    "success": False,
                    "message": f"Không tìm thấy cInvCode cho mã: {code}"
                })
        else:
            # Nếu không phải dạng cEngineerFigNo, thử xem mã này có phải là cInvCode không
            # Tìm tất cả các cEngineerFigNo mapping đến mã cInvCode này
            all_matches = core.find_cinvcode_from_excel(code, return_all=True)
            
            # all_matches sẽ chứa danh sách các cEngineerFigNo mapping đến cInvCode
            # Nhưng thực tế hàm find_cinvcode_from_excel tìm theo cEngineerFigNo, không phải cInvCode
            # Nên chúng ta không tìm được quan hệ ngược
            
            # Giải pháp: Kiểm tra xem mã này có trong Excel không (dưới dạng cInvCode)
            # Nếu mã bắt đầu bằng '10', đây có thể là mã mẹ
            if code.startswith('10'):
                # Mã bắt đầu bằng 10 - có thể là mã mẹ
                return jsonify({
                    "success": True,
                    "parent_code": code,
                    "message": f"Mã {code} có thể là mã mẹ"
                })
            
            return jsonify({
                "success": False,
                "message": f"Mã {code} không đúng định dạng cEngineerFigNo"
            })
            
    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Lỗi khi tìm kiếm: {str(e)}"
        })

# ========================================================================
# Chạy Server
# ========================================================================

if __name__ == '__main__':
    safe_print("=" * 50)
    safe_print("Mo ma lieu Web Server")
    safe_print("=" * 50)
    safe_print("Truy cap: http://localhost:5000")
    safe_print("API: http://localhost:5000/api/*")
    safe_print("=" * 50)
    
    try:
        app.run(host='0.0.0.0', port=5000, debug=True, threaded=True, use_reloader=False)
    except ValueError as e:
        if 'I/O operation on closed file' in str(e):
            safe_print("Flask server stopped (stdout closed)")
        else:
            safe_print(f"Flask server error: {e}")
    except OSError as e:
        if 'WinError 10048' in str(e) or 'Address already in use' in str(e):
            safe_print("Port 5000 already in use")
        else:
            safe_print(f"Flask server error: {e}")
    except Exception as e:
        safe_print(f"Flask server error: {e}")
