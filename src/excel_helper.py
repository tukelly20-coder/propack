# -*- coding: utf-8 -*-
"""
Excel Helper Module - Đọc và cache dữ liệu từ file Excel

Chức năng:
- Đọc file Excel chứa mapping cEngineerFigNo -> cInvCode
- Cache dữ liệu Excel vào memory để tránh đọc file nhiều lần
- Tìm kiếm cInvCode theo cEngineerFigNo
- Batch lookup cho nhiều mã cùng lúc
- Thread-safe caching

Author: Propack VP
"""

import threading
import os

# ========================================================================
# Thread-Safe Print
# ========================================================================

_print_lock = threading.Lock()

def safe_print(*args, **kwargs):
    """Thread-safe print"""
    try:
        with _print_lock:
            print(*args, **kwargs)
    except (ValueError, OSError):
        pass

# ========================================================================
# Excel Configuration & Cache
# ========================================================================

# Excel file path for parent code lookup (UNC network path)
EXCEL_PATH = r"\\192.168.2.165\越南vp共享文件夹\09-工程图纸 Bản vẽ Kỹ Thuật Công Trình\存货档案库.xlsx"

# Cache for Excel data (loaded once into memory)
CACHED_EXCEL_DATA = None

# Thread lock for cache access (ensure thread-safety)
excel_cache_lock = threading.Lock()

# ========================================================================
# Excel Data Loading Functions
# ========================================================================

def get_excel_data():
    """
    Đọc dữ liệu Excel vào memory (chỉ tải 1 lần).
    
    Returns:
        list: Danh sách các tuple (sheet_name, DataFrame) chứa dữ liệu Excel
              hoặc None nếu có lỗi
    """
    global CACHED_EXCEL_DATA
    
    with excel_cache_lock:
        if CACHED_EXCEL_DATA is not None:
            return CACHED_EXCEL_DATA
    
    try:
        import pandas as pd
        
        # Normalize UNC path
        excel_path = EXCEL_PATH.replace('/', '\\')
        if not excel_path.startswith('\\\\'):
            excel_path = '\\\\' + excel_path.lstrip('\\')
        
        safe_print(f"[Excel] Loading Excel into memory: {excel_path}")
        
        # Read all sheets
        xls = pd.ExcelFile(excel_path)
        data = []
        for sheet_name in xls.sheet_names:
            df = pd.read_excel(excel_path, sheet_name=sheet_name)
            # Only cache sheets with required columns
            if 'cEngineerFigNo' in df.columns and 'cInvCode' in df.columns:
                # Pre-process: convert to string and uppercase for faster lookup
                df['cEngineerFigNo'] = df['cEngineerFigNo'].astype(str).str.upper().str.strip()
                df['cInvCode'] = df['cInvCode'].astype(str).str.strip()
                data.append((sheet_name, df))
        
        safe_print(f"[Excel] Loaded {len(data)} sheets with data")
        
        with excel_cache_lock:
            CACHED_EXCEL_DATA = data
            return CACHED_EXCEL_DATA
    except Exception as e:
        safe_print(f"[Excel] Error loading Excel: {e}")
        return None


def clear_excel_cache():
    """
    Xóa cache Excel để buộc đọc lại file.
    
    Returns:
        bool: True nếu thành công
    """
    global CACHED_EXCEL_DATA
    with excel_cache_lock:
        CACHED_EXCEL_DATA = None
        return True


def get_cache_status():
    """
    Kiểm tra trạng thái cache Excel.
    
    Returns:
        dict: {
            'cached': bool,
            'sheets_count': int,
            'path': str
        }
    """
    global CACHED_EXCEL_DATA
    with excel_cache_lock:
        cached = CACHED_EXCEL_DATA is not None
        sheets_count = len(CACHED_EXCEL_DATA) if CACHED_EXCEL_DATA else 0
    
    return {
        'cached': cached,
        'sheets_count': sheets_count,
        'path': EXCEL_PATH
    }

# ========================================================================
# Excel Lookup Functions
# ========================================================================

def find_cinvcode_from_excel(engineer_fig_no: str, return_all: bool = False):
    """
    Tìm cInvCode tương ứng với cEngineerFigNo trong file Excel.
    
    Args:
        engineer_fig_no: Mã cEngineerFigNo cần tìm
        return_all: Nếu True, trả về tất cả các kết quả (list)
                    Nếu False, trả về kết quả đầu tiên (str)
    
    Returns:
        str: Mã cInvCode tìm được (nếu return_all=False)
        list: Danh sách các kết quả (nếu return_all=True)
        None: Không tìm thấy
    """
    excel_data = get_excel_data()
    if not excel_data:
        return [] if return_all else None
    
    search_code = str(engineer_fig_no).upper().strip()
    results = []
    
    # Try exact match first
    for sheet_name, df in excel_data:
        try:
            mask = df['cEngineerFigNo'] == search_code
            if mask.any():
                matches = df.loc[mask, 'cInvCode']
                for m in matches:
                    if m and str(m) != 'nan' and str(m).strip():
                        result = str(int(float(m))) if '.' in str(m) else str(m)
                        results.append({
                            'sheet': sheet_name,
                            'cInvCode': result
                        })
                        if not return_all:
                            return result
        except Exception as e:
            continue
    
    # Try partial match (startswith)
    for sheet_name, df in excel_data:
        try:
            mask = df['cEngineerFigNo'].str.startswith(search_code)
            if mask.any():
                matches = df.loc[mask, 'cInvCode']
                for m in matches:
                    if m and str(m) != 'nan' and str(m).strip():
                        result = str(int(float(m))) if '.' in str(m) else str(m)
                        # Avoid duplicates
                        if not any(r['cInvCode'] == result for r in results):
                            results.append({
                                'sheet': sheet_name,
                                'cInvCode': result
                            })
                            if not return_all:
                                return result
        except Exception as e:
            continue
    
    if return_all:
        return results
    return None


def find_parent_codes_batch(codes: list):
    """
    Tìm parent codes cho nhiều mã cùng lúc.
    
    Args:
        codes: List of codes cần tìm parent
    
    Returns:
        dict: Mapping {code: parent_code}
    """
    results = {}
    
    # Pre-load Excel if not already loaded
    excel_data = get_excel_data()
    if not excel_data:
        return results
    
    for code in codes:
        parent_code = find_cinvcode_from_excel(code)
        if parent_code:
            results[code] = parent_code
    
    return results


def check_excel_connection():
    """
    Kiểm tra kết nối đến file Excel.
    
    Returns:
        dict: {
            'connected': bool,
            'path': str,
            'error': str or None
        }
    """
    try:
        excel_path = EXCEL_PATH.replace('/', '\\')
        if not excel_path.startswith('\\\\'):
            excel_path = '\\\\' + excel_path.lstrip('\\')
        
        exists = os.path.exists(excel_path)
        
        return {
            'connected': exists,
            'path': excel_path,
            'error': None if exists else "File not found"
        }
    except Exception as e:
        return {
            'connected': False,
            'path': EXCEL_PATH,
            'error': str(e)
        }


# ========================================================================
# Flask Routes Registration
# ========================================================================

def register_routes(app):
    """
    Đăng ký các routes liên quan đến Excel với Flask app.
    
    Args:
        app: Flask application instance
    """
    from flask import request, jsonify
    
    @app.route('/api/codes/search-parent', methods=['GET'])
    def api_codes_search_parent():
        """Tìm parent code cho một mã"""
        code = request.args.get('code', '').strip()
        
        if not code:
            return jsonify({"success": False, "error": "Mã không được để trống"}), 400
        
        try:
            parent_code = find_cinvcode_from_excel(code)
            
            if parent_code:
                return jsonify({
                    "success": True,
                    "parent_code": parent_code
                })
            else:
                return jsonify({
                    "success": False,
                    "parent_code": None,
                    "message": "Không tìm thấy mã mẹ"
                })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Lỗi khi tìm kiếm Mã mẹ: {str(e)}"
            }), 500
    
    @app.route('/api/codes/search-parent-batch', methods=['GET'])
    def api_codes_search_parent_batch():
        """Tìm parent codes cho nhiều mã (GET)"""
        codes_param = request.args.get('codes', '')
        codes = [c.strip() for c in codes_param.split(',') if c.strip()]
        
        if not codes:
            return jsonify({"success": False, "error": "Danh sách mã trống"}), 400
        
        try:
            import time
            start_time = time.time()
            
            results = find_parent_codes_batch(codes)
            
            elapsed = time.time() - start_time
            
            return jsonify({
                "success": True,
                "results": results,
                "count": len(results),
                "total_requested": len(codes),
                "elapsed_seconds": round(elapsed, 3)
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Lỗi khi tìm kiếm batch: {str(e)}"
            }), 500
    
    @app.route('/api/codes/search-parent-batch-post', methods=['POST'])
    def api_codes_search_parent_batch_post():
        """Tìm parent codes cho nhiều mã (POST)"""
        data = request.get_json()
        codes = data.get('codes', [])
        
        if not codes or not isinstance(codes, list):
            return jsonify({"success": False, "error": "Danh sách mã trống"}), 400
        
        try:
            import time
            start_time = time.time()
            
            results = find_parent_codes_batch(codes)
            
            elapsed = time.time() - start_time
            
            return jsonify({
                "success": True,
                "results": results,
                "count": len(results),
                "total_requested": len(codes),
                "elapsed_seconds": round(elapsed, 3)
            })
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Lỗi khi tìm kiếm batch: {str(e)}"
            }), 500
    
    @app.route('/api/excel/status', methods=['GET'])
    def api_excel_status():
        """Kiểm tra trạng thái Excel cache"""
        status = get_cache_status()
        return jsonify({
            "success": True,
            **status
        })
    
    @app.route('/api/excel/connection', methods=['GET'])
    def api_excel_connection():
        """Kiểm tra kết nối đến file Excel"""
        result = check_excel_connection()
        return jsonify({
            "success": result['connected'],
            **result
        })
    
    @app.route('/api/excel/clear-cache', methods=['POST'])
    def api_excel_clear_cache():
        """Xóa cache Excel"""
        clear_excel_cache()
        return jsonify({
            "success": True,
            "message": "Đã xóa cache Excel"
        })


# ========================================================================
# Module Exports
# ========================================================================

__all__ = [
    # Configuration
    'EXCEL_PATH',
    'CACHED_EXCEL_DATA',
    'excel_cache_lock',
    
    # Functions
    'safe_print',
    'get_excel_data',
    'clear_excel_cache',
    'get_cache_status',
    'find_cinvcode_from_excel',
    'find_parent_codes_batch',
    'check_excel_connection',
    
    # Routes
    'register_routes'
]