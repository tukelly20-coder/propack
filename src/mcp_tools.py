# -*- coding: utf-8 -*-
"""
MCP Tools Module - Tools để AI truy vấn database
Model Context Protocol (MCP) tools cho AI Chat
"""

from typing import Dict, List, Any, Optional
from src import chat_service
from src import chat_db

# ============================================
# TOOL DEFINITIONS
# ============================================

def get_tool_definitions() -> List[Dict]:
    """
    Lấy danh sách tất cả các tool definitions
    Định dạng theo MCP specification
    """
    return [
        {
            "name": "get_user_sessions",
            "description": "Lấy danh sách các cuộc trò chuyện của user. Sử dụng khi user hỏi về các cuộc trò chuyện trước đó, lần trước, hoặc muốn xem lịch sử chat.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "Số lượng tối đa cuộc trò chuyện cần lấy"
                    },
                    "offset": {
                        "type": "integer", 
                        "default": 0,
                        "description": "Bắt đầu từ vị trí nào (cho phân trang)"
                    }
                }
            }
        },
        {
            "name": "get_session_messages",
            "description": "Lấy tin nhắn trong một cuộc trò chuyện cụ thể. Cần biết session_id.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "ID của cuộc trò chuyện"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 50,
                        "description": "Số lượng tin nhắn tối đa"
                    }
                },
                "required": ["session_id"]
            }
        },
        {
            "name": "search_chat_history",
            "description": "Tìm kiếm trong lịch sử chat. Sử dụng khi user hỏi về nội dung đã thảo luận trước đó, đã nói gì, đã hỏi về chủ đề gì đó.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Từ khóa tìm kiếm"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 5,
                        "description": "Số kết quả tối đa"
                    }
                },
                "required": ["query"]
            }
        },
        {
            "name": "get_system_state",
            "description": "Lấy trạng thái hiện tại của AI (dự án hiện tại, bước hiện tại, hành động cuối). Sử dụng khi cần biết user đang làm gì.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "update_system_state",
            "description": "Cập nhật trạng thái AI sau khi thực hiện hành động với user. Gọi sau khi hoàn thành một tác vụ.",
            "parameters": {
                "type": "object",
                "properties": {
                    "current_project": {
                        "type": "string",
                        "description": "Tên dự án hiện tại"
                    },
                    "current_step": {
                        "type": "string",
                        "description": "Bước hiện tại trong workflow"
                    },
                    "last_action": {
                        "type": "string",
                        "description": "Hành động vừa thực hiện"
                    }
                }
            }
        },
        {
            "name": "get_session_count",
            "description": "Đếm tổng số cuộc trò chuyện. Sử dụng khi user hỏi 'có bao nhiêu cuộc trò chuyện rồi?' hoặc 'đã chat bao nhiêu lần'.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        },
        {
            "name": "get_ai_context",
            "description": "Lấy context đầy đủ cho AI (system state + recent messages + summary). Sử dụng để lấy toàn bộ context của một phiên chat.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "ID của cuộc trò chuyện"
                    }
                },
                "required": ["session_id"]
            }
        },
        {
            "name": "get_session_details",
            "description": "Lấy chi tiết một cuộc trò chuyện bao gồm thông tin session, số tin nhắn, ngày tạo, ngày cập nhật. Sử dụng khi user muốn xem chi tiết một cuộc trò chuyện cụ thể.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "ID của cuộc trò chuyện cần lấy chi tiết"
                    }
                },
                "required": ["session_id"]
            }
        },
        {
            "name": "get_conversation_summary",
            "description": "Lấy tóm tắt nội dung của một cuộc trò chuyện. Sử dụng khi user hỏi 'cuộc trò chuyện này nói về gì?' hoặc muốn biết nội dung chính.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "ID của cuộc trò chuyện"
                    }
                },
                "required": ["session_id"]
            }
        },
        {
            "name": "compare_sessions",
            "description": "So sánh nội dung của nhiều cuộc trò chuyện. Sử dụng khi user muốn xem các cuộc trò chuyện khác nhau để tìm sự khác biệt hoặc liên quan.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_ids": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "Danh sách các ID của các cuộc trò chuyện cần so sánh"
                    }
                },
                "required": ["session_ids"]
            }
        },
        {
            "name": "create_session",
            "description": "Tạo một cuộc trò chuyện mới. Sử dụng khi user muốn bắt đầu một cuộc trò chuyện mới với AI.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Tiêu đề cho cuộc trò chuyện mới (tùy chọn)"
                    }
                }
            }
        },
        {
            "name": "delete_session",
            "description": "Xóa một cuộc trò chuyện. Sử dụng khi user muốn xóa một cuộc trò chuyện cụ thể.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "ID của cuộc trò chuyện cần xóa"
                    }
                },
                "required": ["session_id"]
            }
        },
        {
            "name": "export_session",
            "description": "Export toàn bộ nội dung cuộc trò chuyện ra JSON. Sử dụng khi user muốn lưu trữ hoặc xuất một cuộc trò chuyện.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "ID của cuộc trò chuyện cần export"
                    }
                },
                "required": ["session_id"]
            }
        },
        {
            "name": "save_summary",
            "description": "Lưu hoặc cập nhật tóm tắt cho một cuộc trò chuyện. Sử dụng sau khi có nội dung mới quan trọng cần ghi nhớ.",
            "parameters": {
                "type": "object",
                "properties": {
                    "session_id": {
                        "type": "string",
                        "description": "ID của cuộc trò chuyện"
                    },
                    "summary": {
                        "type": "string",
                        "description": "Nội dung tóm tắt cần lưu"
                    }
                },
                "required": ["session_id", "summary"]
            }
        },
        {
            "name": "create_drawing_code",
            "description": "Tạo mã bản vẽ mới cho dự án. Sử dụng khi user yêu cầu tạo mã bản vẽ, mã bản vẽ mới, hoặc cần mã cho sản phẩm.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Tên dự án hoặc sản phẩm (bắt buộc)"
                    },
                    "category": {
                        "type": "string",
                        "description": "Loại sản phẩm: WLJ (物料架), ZZC (周转车), GZT (工作台), WCP (无尘棚), LSX (流水线), ZWJ (转弯机), GZL (改造类), BSX (倍速线), WLL (围栏类), GTX (滚筒线), ZHT (展会图), LHX (老化线), SJT (散件图)"
                    },
                    "employee": {
                        "type": "string",
                        "description": "Mã nhân viên (3 chữ số, ví dụ: 001, 002, 003)"
                    }
                },
                "required": ["name", "category", "employee"]
            }
        }
    ]


# ============================================
# TOOL IMPLEMENTATIONS
# ============================================

def call_tool(tool_name: str, user_id: int, parameters: Optional[Dict] = None) -> Dict:
    """
    Gọi một tool với parameters cho trước
    
    Args:
        tool_name: Tên tool cần gọi
        user_id: ID của user
        parameters: Parameters cho tool
    
    Returns:
        Kết quả từ tool
    """
    params = parameters or {}
    
    try:
        if tool_name == "get_user_sessions":
            limit = params.get("limit", 10)
            offset = params.get("offset", 0)
            sessions = chat_service.get_user_sessions(user_id, limit, offset)
            return {
                "success": True,
                "result": sessions,
                "count": len(sessions)
            }
        
        elif tool_name == "get_session_messages":
            session_id = params.get("session_id")
            limit = params.get("limit", 50)
            if not session_id:
                return {"success": False, "error": "Thiếu session_id"}
            messages = chat_service.get_session_messages(session_id, user_id, limit)
            return {
                "success": True,
                "result": messages,
                "count": len(messages)
            }
        
        elif tool_name == "search_chat_history":
            query = params.get("query", "")
            limit = params.get("limit", 5)
            if not query:
                return {"success": False, "error": "Thiếu query"}
            results = chat_service.search_chat_history(user_id, query, limit)
            return {
                "success": True,
                "result": results,
                "count": len(results)
            }
        
        elif tool_name == "get_system_state":
            state = chat_service.get_system_state(user_id)
            return {
                "success": True,
                "result": state or {}
            }
        
        elif tool_name == "update_system_state":
            current_project = params.get("current_project")
            current_step = params.get("current_step")
            last_action = params.get("last_action")
            
            update_data = {}
            if current_project is not None:
                update_data["current_project"] = current_project
            if current_step is not None:
                update_data["current_step"] = current_step
            if last_action is not None:
                update_data["last_action"] = last_action
            
            if not update_data:
                return {"success": False, "error": "Không có dữ liệu để cập nhật"}
            
            success = chat_service.update_system_state(user_id, **update_data)
            return {
                "success": success,
                "message": "Đã cập nhật system state" if success else "Không thể cập nhật"
            }
        
        elif tool_name == "get_session_count":
            count = chat_service.get_total_session_count(user_id)
            return {
                "success": True,
                "result": {"count": count},
                "count": count
            }
        
        elif tool_name == "get_ai_context":
            session_id = params.get("session_id")
            if not session_id:
                return {"success": False, "error": "Thiếu session_id"}
            context = chat_service.build_ai_context(session_id, user_id)
            return {
                "success": True,
                "result": context
            }
        
        elif tool_name == "get_session_details":
            session_id = params.get("session_id")
            if not session_id:
                return {"success": False, "error": "Thiếu session_id"}
            # Lấy session details bao gồm message count
            session = chat_service.get_session_by_id(session_id, user_id)
            if not session:
                return {"success": False, "error": "Không tìm thấy cuộc trò chuyện"}
            # Lấy số tin nhắn
            messages = chat_service.get_session_messages(session_id, user_id, limit=1)
            message_count = len(messages) if messages else 0
            # Lấy summary nếu có
            summary = chat_service.get_or_create_summary(session_id)
            return {
                "success": True,
                "result": {
                    "session": session,
                    "message_count": message_count,
                    "summary": summary
                }
            }
        
        elif tool_name == "get_conversation_summary":
            session_id = params.get("session_id")
            if not session_id:
                return {"success": False, "error": "Thiếu session_id"}
            # Verify session exists
            session = chat_service.get_session_by_id(session_id, user_id)
            if not session:
                return {"success": False, "error": "Không tìm thấy cuộc trò chuyện"}
            # Lấy summary
            summary = chat_service.get_or_create_summary(session_id)
            return {
                "success": True,
                "result": {
                    "session_id": session_id,
                    "title": session.get("title", ""),
                    "summary": summary,
                    "created_at": session.get("created_at", ""),
                    "updated_at": session.get("updated_at", "")
                }
            }
        
        elif tool_name == "compare_sessions":
            session_ids = params.get("session_ids", [])
            if not session_ids or len(session_ids) < 2:
                return {"success": False, "error": "Cần ít nhất 2 session_ids để so sánh"}
            results = []
            for sid in session_ids:
                session = chat_service.get_session_by_id(sid, user_id)
                if session:
                    summary = chat_service.get_or_create_summary(sid)
                    messages = chat_service.get_session_messages(sid, user_id, limit=1)
                    results.append({
                        "session_id": sid,
                        "title": session.get("title", ""),
                        "created_at": session.get("created_at", ""),
                        "message_count": len(messages),
                        "summary": summary
                    })
            return {
                "success": True,
                "result": results,
                "count": len(results)
            }
        
        elif tool_name == "create_session":
            title = params.get("title")
            new_session = chat_service.create_new_session(user_id, title)
            if new_session:
                return {
                    "success": True,
                    "result": new_session,
                    "message": "Đã tạo cuộc trò chuyện mới"
                }
            return {"success": False, "error": "Không thể tạo cuộc trò chuyện mới"}
        
        elif tool_name == "delete_session":
            session_id = params.get("session_id")
            if not session_id:
                return {"success": False, "error": "Thiếu session_id"}
            success = chat_service.delete_session_by_id(session_id, user_id)
            return {
                "success": success,
                "message": "Đã xóa cuộc trò chuyện" if success else "Không thể xóa cuộc trò chuyện"
            }
        
        elif tool_name == "export_session":
            session_id = params.get("session_id")
            if not session_id:
                return {"success": False, "error": "Thiếu session_id"}
            export_data = chat_service.export_chat_session(session_id, user_id)
            if export_data:
                return {
                    "success": True,
                    "result": export_data
                }
            return {"success": False, "error": "Không thể export cuộc trò chuyện"}
        
        elif tool_name == "save_summary":
            session_id = params.get("session_id")
            summary = params.get("summary")
            if not session_id or not summary:
                return {"success": False, "error": "Thiếu session_id hoặc summary"}
            # Verify session exists
            session = chat_service.get_session_by_id(session_id, user_id)
            if not session:
                return {"success": False, "error": "Không tìm thấy cuộc trò chuyện"}
            success = chat_service.update_summary(session_id, summary)
            return {
                "success": success,
                "message": "Đã lưu tóm tắt" if success else "Không thể lưu tóm tắt"
            }
        
        elif tool_name == "create_drawing_code":
            import requests
            import os
            
            name = params.get("name", "").strip()
            category = params.get("category", "").strip().upper()
            employee = params.get("employee", "").strip()
            
            # Validate required fields
            if not name:
                return {"success": False, "error": "Thiếu tên dự án/sản phẩm (name)"}
            if not category:
                return {"success": False, "error": "Thiếu loại sản phẩm (category)"}
            if not employee:
                return {"success": False, "error": "Thiếu mã nhân viên (employee)"}
            
            # Validate employee code (3 digits, not 000)
            if not (len(employee) == 3 and employee.isdigit() and employee != '000'):
                return {"success": False, "error": "Mã nhân viên phải là 3 chữ số và không phải 000"}
            
            # Validate category
            valid_categories = ["WLJ", "ZZC", "GZT", "WCP", "LSX", "ZWJ", "GZL", "SJT", "BSX", "WLL", "GTX", "ZHT", "LHX"]
            if category not in valid_categories:
                return {"success": False, "error": f"Loại sản phẩm không hợp lệ. Các loại hợp lệ: {', '.join(valid_categories)}"}
            
            # Get server URL from environment or use default
            server_url = os.environ.get('SERVER_URL', 'http://localhost:8001')
            
            try:
                response = requests.post(
                    f"{server_url}/api/codes/create",
                    json={
                        "name": name,
                        "category": category,
                        "employee": employee
                    },
                    timeout=30
                )
                
                if response.status_code == 200:
                    result = response.json()
                    if result.get("success"):
                        code = result.get("code", "")
                        return {
                            "success": True,
                            "result": {
                                "code": code,
                                "name": name,
                                "category": category,
                                "employee": employee
                            },
                            "message": f"Đã tạo mã bản vẽ: {code}"
                        }
                    else:
                        return {"success": False, "error": result.get("error", "Lỗi không xác định")}
                else:
                    return {"success": False, "error": f"Lỗi server: {response.status_code}"}
            
            except requests.exceptions.ConnectionError:
                return {"success": False, "error": "Không thể kết nối server. Vui lòng kiểm tra server đang chạy."}
            except requests.exceptions.Timeout:
                return {"success": False, "error": "Timeout khi kết nối server"}
            except Exception as e:
                return {"success": False, "error": f"Lỗi: {str(e)}"}
        
        else:
            return {"success": False, "error": f"Tool '{tool_name}' không tồn tại"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================
# SYSTEM PROMPT
# ============================================

def get_tools_system_prompt() -> str:
    """
    Lấy system prompt hướng dẫn AI cách sử dụng tools
    """
    return """
## TOOLS CHO PHÉP GỌI

Bạn có quyền gọi các tools sau để lấy thông tin từ database:

### QUERY TOOLS (Lấy dữ liệu)
1. **get_user_sessions** - Lấy danh sách cuộc trò chuyện
   - Gọi khi: User hỏi về "các cuộc trò chuyện trước đó", "lần trước", "xem lịch sử chat"
   
2. **get_session_details** - Lấy chi tiết một cuộc trò chuyện (MỚI)
   - Gọi khi: User muốn xem chi tiết cụ thể của một cuộc trò chuyện
   
3. **get_conversation_summary** - Lấy tóm tắt nội dung (MỚI)
   - Gọi khi: User hỏi "cuộc trò chuyện này nói về gì?"
   
4. **compare_sessions** - So sánh nhiều cuộc trò chuyện (MỚI)
   - Gọi khi: User muốn xem sự khác biệt giữa các cuộc trò chuyện
   
5. **search_chat_history** - Tìm kiếm nội dung đã chat
   - Gọi khi: User hỏi về nội dung đã thảo luận, "đã nói gì", "đã hỏi về", "nhắc lại"
   
6. **get_system_state** - Lấy trạng thái hiện tại
   - Gọi khi: Cần biết dự án, bước hiện tại của user
   
7. **get_session_count** - Đếm số cuộc trò chuyện
   - Gọi khi: User hỏi "có bao nhiêu cuộc trò chuyện rồi?", "đã chat bao nhiêu lần"

8. **get_ai_context** - Lấy context đầy đủ
   - Gọi khi: Cần lấy toàn bộ context của một phiên chat

### ACTION TOOLS (Cập nhật dữ liệu)
9. **update_system_state** - Cập nhật trạng thái AI
   - Gọi khi: Sau khi thực hiện hành động với user (tạo mã, xuất file, v.v.)

10. **create_session** - Tạo cuộc trò chuyện mới (MỚI)
    - Gọi khi: User muốn bắt đầu cuộc trò chuyện mới
    
11. **delete_session** - Xóa cuộc trò chuyện (MỚI)
    - Gọi khi: User muốn xóa một cuộc trò chuyện
    
12. **export_session** - Export cuộc trò chuyện (MỚI)
    - Gọi khi: User muốn lưu hoặc xuất nội dung cuộc trò chuyện
    
13. **save_summary** - Lưu tóm tắt (MỚI)
    - Gọi khi: Cần lưu tóm tắt quan trọng cho cuộc trò chuyện

14. **create_drawing_code** - Tạo mã bản vẽ mới (QUAN TRỌNG)
    - Gọi khi: User yêu cầu tạo mã bản vẽ, mã bản vẽ mới, hoặc cần mã cho sản phẩm
    - Parameters: name (tên dự án), category (loại sản phẩm), employee (mã nhân viên 3 chữ số)

## CÁCH SỬ DỤNG

Khi nhận được yêu cầu từ user mà cần tra cứu database:
1. Chọn tool phù hợp với yêu cầu
2. Gọi API với parameters thích hợp
3. Sử dụng kết quả để trả lời user

## VÍ DỤ

### Ví dụ 1 (đã có):
- User: "Cuộc trò chuyện trước về mã bản vẽ thế nào?" 
- Action: Gọi get_user_sessions({limit: 5})
- Trả lời: Dựa trên kết quả, tóm tắt các cuộc trò chuyện gần đây

### Ví dụ 2 (đã có):
- User: "Ta đã nói gì về dự án ABC?"
- Action: Gọi search_chat_history({query: "dự án ABC", limit: 5})
- Trả lời: Tìm và tóm tắt các nội dung liên quan

### Ví dụ 3 (đã có):
- User: "Có bao nhiêu cuộc trò chuyện rồi?"
- Action: Gọi get_session_count()
- Trả lời: "Bạn đã có X cuộc trò chuyện với tôi"

### Ví dụ 4 (MỚI):
- User: "Cuộc trò chuyện gần nhất nói về gì?"
- Action: Gọi get_user_sessions({limit: 1}), sau đó get_conversation_summary({session_id: ...})
- Trả lời: Tóm tắt nội dung cuộc trò chuyện gần nhất

### Ví dụ 5 (MỚI):
- User: "Tôi muốn xem chi tiết cuộc trò chuyện hôm qua"
- Action: Gọi get_user_sessions({limit: 5}), chọn session_id, gọi get_session_details({session_id: ...})
- Trả lời: Hiển thị chi tiết đầy đủ của cuộc trò chuyện

### Ví dụ 6 (MỚI):
- User: Tạo mã bản vẽ cho tôi
- Action: Sau khi tạo xong, gọi update_system_state({
    "current_project": "tạo mã bản vẽ",
    "current_step": "hoàn thành",
    "last_action": "đã tạo mã bản vẽ"
})

### Ví dụ 7 (MỚI):
- User: "Lưu lại cuộc trò chuyện này cho tôi"
- Action: Gọi export_session({session_id: ...})
- Trả lời: Trả về dữ liệu JSON của cuộc trò chuyện

### Ví dụ 8 (MỚI - TẠO MÃ BẢN VẼ):
- User: "Tạo mã bản vẽ cho dự án ABC, loại WLJ, nhân viên 001"
- Action: Gọi create_drawing_code({
    "name": "Dự án ABC",
    "category": "WLJ",
    "employee": "001"
})
- Trả lời: "Đã tạo mã bản vẽ: PWLJ001-0000-00-A0"

### Ví dụ 9 (MỚI - TẠO MÃ SJT):
- User: "Tạo mã bản vẽ SJT cho sản phẩm XYZ, nhân viên 003"
- Action: Gọi create_drawing_code({
    "name": "Sản phẩm XYZ",
    "category": "SJT",
    "employee": "003"
})
- Trả lời: "Đã tạo mã bản vẽ: PSJT003-0001-00-A0"

## DANH MỤC SẢN PHẨM (CHO TẠO MÃ BẢN VẼ)
- WLJ: 物料架 (Giá đựng vật liệu)
- ZZC: 周转车 (Xe trung chuyển)
- GZT: 工作台 (Bàn thao tác)
- WCP: 无尘棚 (Phòng sạch)
- LSX: 流水线 (Băng tải)
- ZWJ: 转弯机 (Băng tải chuyển hướng)
- GZL: 改造类 (Cải tạo)
- BSX: 倍速线 (Băng chuyền xích)
- WLL: 围栏类 (Hàng rào)
- GTX: 滚筒线 (Băng chuyền con lăn)
- ZHT: 展会图 (Bản vẽ mặt bằng)
- LHX: 老化线 (Băng chuyền lão hóa)
- SJT: 散件图 (Bản vẽ tách chi tiết)

## QUY TẮC MÃ BẢN VẼ
- SJT: PSJT{employee}-{serial}-00-A0 (ví dụ: PSJT001-0001-00-A0)
- Các loại khác: P{prefix}{number}-0000-00-A0 (ví dụ: PWLJ001-0000-00-A0)

**QUAN TRỌNG: Khi user yêu cầu tạo mã bản vẽ, bạn PHẢI gọi tool create_drawing_code thay vì chỉ trả lời text.**
"""


# ============================================
# TOOLS JSON (cho frontend)
# ============================================

def get_tools_json() -> str:
    """Lấy tools dạng JSON để gửi cho frontend"""
    import json
    return json.dumps(get_tool_definitions(), ensure_ascii=False, indent=2)


# ============================================
# TEST FUNCTIONS
# ============================================

def test_tools(user_id: int = 1) -> Dict:
    """
    Test tất cả các tools
    """
    results = {}
    
    # Test 1: get_user_sessions
    results["get_user_sessions"] = call_tool("get_user_sessions", user_id, {"limit": 5})
    
    # Test 2: get_session_count
    results["get_session_count"] = call_tool("get_session_count", user_id)
    
    # Test 3: get_system_state
    results["get_system_state"] = call_tool("get_system_state", user_id)
    
    # Test 4: search_chat_history
    results["search_chat_history"] = call_tool("search_chat_history", user_id, {"query": "test", "limit": 3})
    
    return results


# Export functions
__all__ = [
    "get_tool_definitions",
    "get_tools_json", 
    "get_tools_system_prompt",
    "call_tool",
    "test_tools"
]