# routes/tool_routes.py
"""
Tool Open Routes - Integration with Tool Open module for material code lookup

Routes:
- GET  /api/tool-status   - Check Tool Open status
- POST /api/tool-search   - Search for material codes
"""
from flask import Blueprint, request, jsonify, send_from_directory
import os
import sys

tool_bp = Blueprint('tool', __name__, url_prefix='/api')

# Global reference to material_core (will be set during init)
material_core = None
TOOL_OPEN_AVAILABLE = False


def init_tool_routes(material_core_module, available=False):
    """Initialize tool routes with material core reference"""
    global material_core, TOOL_OPEN_AVAILABLE
    material_core = material_core_module
    TOOL_OPEN_AVAILABLE = available


@tool_bp.route('/tool-status', methods=['GET'])
def tool_status():
    """
    Check Tool Open module status.
    
    Returns:
        - status: "ready" if Excel file exists, "error" otherwise
        - excel_path: Path to the Excel file
        - excel_exists: Boolean indicating if file exists
    """
    if not TOOL_OPEN_AVAILABLE or material_core is None:
        return jsonify({
            "status": "unavailable",
            "message": "Tool Open not loaded",
            "available": False
        })
    
    try:
        excel_path = material_core.normalize_unc_path(material_core.EXCEL_PATH)
        excel_exists = os.path.exists(excel_path)
        
        return jsonify({
            "status": "ready" if excel_exists else "error",
            "message": "Sẵn sàng" if excel_exists else "Không thể kết nối Excel",
            "excel_path": excel_path,
            "excel_exists": excel_exists,
            "available": True
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": str(e),
            "available": True
        })


@tool_bp.route('/tool-search', methods=['POST'])
def tool_search():
    """
    Search for material codes using Tool Open.
    
    Request body:
        - code: Material code or engineer figure number to search
        
    Returns:
        - type: "success", "multiple", or "error"
        - urls: List of file URLs if found
        - copied_code: Code that was copied to clipboard
        - message: Status message
    """
    if not TOOL_OPEN_AVAILABLE or material_core is None:
        return jsonify({
            "type": "error",
            "message": "Tool Open not available"
        })
    
    data = request.get_json()
    code = data.get('code', '').strip().strip('"').strip("'")
    
    if not code:
        return jsonify({
            "type": "error",
            "message": "Mã không được để trống!"
        })
    
    try:
        # Check if code is an engineer figure number
        if material_core.is_engineer_fig_no(code):
            # Search for cInvCode
            all_matches = material_core.find_cinvcode_from_excel(code, return_all=True)
            
            if not all_matches:
                return jsonify({
                    "type": "error",
                    "message": f"Không tìm thấy cInvCode cho: {code}"
                })
            
            # Single match - query material and copy to clipboard
            if len(all_matches) == 1:
                cinv_code = all_matches[0]['cInvCode']
                material_core.copy_to_clipboard(cinv_code)
                urls = material_core.query_material(cinv_code)
                
                if urls:
                    return jsonify({
                        "type": "success",
                        "urls": urls,
                        "folder_count": len(set(os.path.dirname(u) for u in urls)),
                        "copied_code": cinv_code,
                        "message": f"Tìm thấy {len(urls)} files"
                    })
            
            # Multiple matches - return all for user selection
            return jsonify({
                "type": "multiple",
                "matches": all_matches,
                "original_code": code,
                "message": f"Tìm thấy {len(all_matches)} kết quả"
            })
        
        # Regular material code - search directly
        urls = material_core.query_material(code)
        
        if urls:
            urls_text = "\n".join(urls)
            material_core.copy_to_clipboard(urls_text)
            
            return jsonify({
                "type": "success",
                "urls": urls,
                "folder_count": len(set(os.path.dirname(u) for u in urls)),
                "message": f"Tìm thấy {len(urls)} files"
            })
        
        return jsonify({
            "type": "error",
            "message": f"Không tìm thấy dữ liệu cho mã: {code}"
        })
        
    except Exception as e:
        return jsonify({
            "type": "error",
            "message": str(e)
        })


@tool_bp.route('/tool/browse', methods=['GET'])
def tool_browse():
    """
    Browse available tool features.
    
    Returns list of available features and their endpoints.
    """
    return jsonify({
        "available_features": [
            {
                "name": "Material Search",
                "endpoint": "/api/tool-search",
                "method": "POST",
                "description": "Search for material codes and file locations"
            },
            {
                "name": "Status Check",
                "endpoint": "/api/tool-status",
                "method": "GET",
                "description": "Check Tool Open module status and Excel connectivity"
            }
        ],
        "status": "ready" if TOOL_OPEN_AVAILABLE else "unavailable"
    })


# Export blueprint
__all__ = ['tool_bp', 'init_tool_routes']