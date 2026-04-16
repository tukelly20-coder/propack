# -*- coding: utf-8 -*-
"""
Agent Tools Module - Mở rộng MCP Tools với Project và Business logic
Bổ sung tools cho AI Agent: project queries, customer info, search
"""

from typing import Dict, List, Any, Optional
from src import mcp_tools
from src import db_helper
from src import chat_service

# ============================================
# EXTENDED TOOL DEFINITIONS
# ============================================

def get_extended_tool_definitions() -> List[Dict]:
    """
    Lấy danh sách tất cả các tool definitions (bao gồm cả tools mở rộng)
    """
    # Lấy base tools từ mcp_tools
    base_tools = mcp_tools.get_tool_definitions()
    
    # Thêm project và business tools
    extended_tools = base_tools + [
        # Project Tools
        {
            "name": "get_projects",
            "description": "Lấy danh sách các dự án của user (sales/engineer). Sử dụng khi user hỏi về 'dự án của tôi', 'các dự án đang làm', 'danh sách project'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Lọc theo trạng thái (tùy chọn): 'Pending', 'In Progress', 'Completed', 'Cancelled'"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "description": "Số lượng dự án tối đa"
                    }
                }
            }
        },
        {
            "name": "get_project_status",
            "description": "Lấy trạng thái chi tiết của một dự án cụ thể. Sử dụng khi user hỏi 'dự án X sao rồi', 'tiến độ dự án', 'project ABC đang ở đâu'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "project_name": {
                        "type": "string",
                        "description": "Tên dự án cần tra cứu"
                    },
                    "tracking_id": {
                        "type": "integer",
                        "description": "ID theo dõi của dự án (tùy chọn)"
                    }
                },
                "required": ["project_name"]
            }
        },
        {
            "name": "search_projects",
            "description": "Tìm kiếm dự án theo từ khóa. Sử dụng khi user muốn tìm một dự án cụ thể trong hệ thống.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Từ khóa tìm kiếm (tên dự án, khách hàng, tracking ID)"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "Số kết quả tối đa"
                    }
                },
                "required": ["query"]
            }
        },
        # Customer Tools
        {
            "name": "get_customer_info",
            "description": "Lấy thông tin chi tiết về một khách hàng. Sử dụng khi user hỏi về 'khách hàng X', 'thông tin KH', 'ai đặt hàng này'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "customer_name": {
                        "type": "string",
                        "description": "Tên khách hàng cần tra cứu"
                    }
                },
                "required": ["customer_name"]
            }
        },
        {
            "name": "search_customers",
            "description": "Tìm kiếm khách hàng theo từ khóa. Sử dụng khi user muốn tìm thông tin khách hàng trong hệ thống.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Từ khóa tìm kiếm (tên, số điện thoại, email)"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 10,
                        "description": "Số kết quả tối đa"
                    }
                },
                "required": ["query"]
            }
        },
        # Notice/Job Tools
        {
            "name": "get_pending_notices",
            "description": "Lấy danh sách các công việc/thông báo đang chờ xử lý. Sử dụng khi user hỏi 'còn việc gì chưa làm', 'pending tasks', 'công việc chờ'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "urgency": {
                        "type": "string",
                        "description": "Lọc theo mức độ khẩn (tùy chọn): 'Normal', 'Urgent', 'Very Urgent'"
                    },
                    "limit": {
                        "type": "integer",
                        "default": 20,
                        "description": "Số lượng tối đa"
                    }
                }
            }
        },
        {
            "name": "get_notice_details",
            "description": "Lấy chi tiết một công việc/thông báo cụ thể. Sử dụng khi user muốn xem chi tiết một công việc.",
            "parameters": {
                "type": "object",
                "properties": {
                    "tracking_id": {
                        "type": "integer",
                        "description": "ID theo dõi của công việc"
                    }
                },
                "required": ["tracking_id"]
            }
        },
        # Auto-reply suggestions
        {
            "name": "suggest_actions",
            "description": "Đề xuất các hành động có thể thực hiện dựa trên tình huống hiện tại. AI tự gọi khi cần đề xuất cho user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "context": {
                        "type": "string",
                        "description": "Mô tả tình huống hiện tại"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "ID dự án liên quan (tùy chọn)"
                    }
                },
                "required": ["context"]
            }
        },
        # Memory integration
        {
            "name": "store_memory",
            "description": "Lưu thông tin quan trọng vào bộ nhớ AI để nhớ cho các lần sau. Sử dụng khi user cung cấp thông tin cần nhớ.",
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "Nội dung cần lưu vào bộ nhớ"
                    },
                    "memory_type": {
                        "type": "string",
                        "default": "short_term",
                        "description": "Loại bộ nhớ: 'short_term' (ngắn hạn) hoặc 'long_term' (dài hạn)"
                    },
                    "project_id": {
                        "type": "string",
                        "description": "ID dự án liên quan (tùy chọn)"
                    }
                },
                "required": ["content"]
            }
        },
        {
            "name": "recall_memories",
            "description": "Tìm kiếm trong bộ nhớ AI để lấy thông tin đã lưu trước đó. Sử dụng khi cần nhắc lại thông tin từ các cuộc trò chuyện trước.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Từ khóa tìm kiếm trong bộ nhớ"
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
        # Code Tools
        {
            "name": "create_code",
            "description": "Tạo mã bản vẽ mới. Sử dụng khi user yêu cầu 'tạo mã bản vẽ', 'tạo code mới', 'PLSX', v.v.\n\nQUAN TRỌNG: Chấp nhận cả 'category' VÀ 'product_type' làm tham số.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Product/project name"},
                    "product_type": {"type": "string", "enum": ["SJT", "WLJ", "LSX", "ZZC", "ZWJ", "GZT", "WCP", "GZL", "BSX", "WLL", "GTX", "ZHT", "LHX"], "description": "Loại sản phẩm (SJT, WLJ, LSX, v.v.) - Dùng 'category' HOẶC 'product_type'"},
                    "category": {"type": "string", "enum": ["SJT", "WLJ", "LSX", "ZZC", "ZWJ", "GZT", "WCP", "GZL", "BSX", "WLL", "GTX", "ZHT", "LHX"], "description": "Loại sản phẩm (SJT, WLJ, LSX, v.v.) - Dùng 'category' HOẶC 'product_type'"},
                    "employee": {"type": "string", "pattern": "^[0-9]{3}$", "description": "Employee code (3 digits, required for SJT)"}
                },
                "required": ["category"]
            }
        },
        {
            "name": "create_drawing_code",
            "description": "ALIAS cho create_code. Tạo mã bản vẽ mới cho dự án. Sử dụng khi user yêu cầu 'tạo mã bản vẽ', 'sinh mã', 'tạo mã cho...'.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Tên dự án/sản phẩm"},
                    "product_type": {"type": "string", "enum": ["SJT", "WLJ", "LSX", "ZZC", "ZWJ", "GZT", "WCP", "GZL", "BSX", "WLL", "GTX", "ZHT", "LHX"], "description": "Loại sản phẩm (SJT, WLJ, LSX, v.v.)"},
                    "category": {"type": "string", "enum": ["SJT", "WLJ", "LSX", "ZZC", "ZWJ", "GZT", "WCP", "GZL", "BSX", "WLL", "GTX", "ZHT", "LHX"], "description": "Loại sản phẩm (SJT, WLJ, LSX, v.v.)"},
                    "employee": {"type": "string", "description": "Mã nhân viên (3 chữ số, chỉ cần cho SJT)"}
                }
            }
        }
    ]
    
    return extended_tools


# ============================================
# EXTENDED TOOL IMPLEMENTATIONS
# ============================================

def call_extended_tool(tool_name: str, user_id: int, parameters: Optional[Dict] = None) -> Dict:
    """
    Gọi một tool mở rộng với parameters cho trước
    
    Args:
        tool_name: Tên tool cần gọi
        user_id: ID của user
        parameters: Parameters cho tool
    
    Returns:
        Kết quả từ tool
    """
    params = parameters or {}
    
    # Kiểm tra xem có phải tool gốc không, nếu có gọi mcp_tools
    base_tools = [t["name"] for t in mcp_tools.get_tool_definitions()]
    if tool_name in base_tools:
        return mcp_tools.call_tool(tool_name, user_id, params)
    
    try:
        # Project Tools
        if tool_name == "get_projects":
            status = params.get("status")
            limit = params.get("limit", 20)
            projects = db_helper.get_projects_by_user(user_id)
            
            # Filter by status if provided
            if status:
                projects = [p for p in projects if p.get("Status") == status]
            
            return {
                "success": True,
                "result": projects[:limit],
                "count": len(projects[:limit])
            }
        
        elif tool_name == "get_project_status":
            project_name = params.get("project_name")
            tracking_id = params.get("tracking_id")
            
            if tracking_id:
                # Search by tracking ID
                project = db_helper.get_record_by_tracking_id(tracking_id)
            elif project_name:
                # Search by project name
                projects = db_helper.get_projects_by_user(user_id)
                project = None
                for p in projects:
                    if project_name.lower() in p.get("Project Name", "").lower():
                        project = p
                        break
            else:
                return {"success": False, "error": "Cần cung cấp project_name hoặc tracking_id"}
            
            if project:
                return {
                    "success": True,
                    "result": {
                        "tracking_id": project.get("Tracking ID"),
                        "project_name": project.get("Project Name"),
                        "customer": project.get("Customer"),
                        "status": project.get("Status"),
                        "urgency": project.get("Urgency"),
                        "engineer": project.get("Engineer"),
                        "created_date": project.get("Created Date"),
                        "desired_time": project.get("Desired Time"),
                        "description": project.get("Description")
                    }
                }
            return {"success": False, "error": "Không tìm thấy dự án"}
        
        elif tool_name == "search_projects":
            query = params.get("query", "")
            limit = params.get("limit", 10)
            
            if not query:
                return {"success": False, "error": "Thiếu query"}
            
            # Search in all projects
            all_projects = db_helper.get_projects_by_user(user_id)
            
            # Simple search by name/customer
            results = [
                p for p in all_projects
                if query.lower() in p.get("Project Name", "").lower() or
                   query.lower() in p.get("Customer", "").lower() or
                   query.lower() in str(p.get("Tracking ID", "")).lower()
            ]
            
            return {
                "success": True,
                "result": results[:limit],
                "count": len(results[:limit])
            }
        
        # Customer Tools
        elif tool_name == "get_customer_info":
            customer_name = params.get("customer_name")
            
            if not customer_name:
                return {"success": False, "error": "Thiếu customer_name"}
            
            # Search in projects for customer
            projects = db_helper.get_projects_by_user(user_id)
            customer_projects = [p for p in projects if p.get("Customer", "").lower() == customer_name.lower()]
            
            if customer_projects:
                return {
                    "success": True,
                    "result": {
                        "customer_name": customer_name,
                        "total_projects": len(customer_projects),
                        "recent_projects": [
                            {
                                "tracking_id": p.get("Tracking ID"),
                                "project_name": p.get("Project Name"),
                                "status": p.get("Status"),
                                "created_date": p.get("Created Date")
                            }
                            for p in customer_projects[:5]
                        ]
                    }
                }
            return {"success": False, "error": "Không tìm thấy khách hàng"}
        
        elif tool_name == "search_customers":
            query = params.get("query", "")
            limit = params.get("limit", 10)
            
            if not query:
                return {"success": False, "error": "Thiếu query"}
            
            # Search customers from db_helper
            customers = db_helper.search_customers(query)
            
            return {
                "success": True,
                "result": customers[:limit],
                "count": len(customers[:limit])
            }
        
        # Notice/Job Tools
        elif tool_name == "get_pending_notices":
            urgency = params.get("urgency")
            limit = params.get("limit", 20)
            
            notices = db_helper.get_pending_notices(user_id)
            
            # Filter by urgency if provided
            if urgency:
                notices = [n for n in notices if n.get("Urgency") == urgency]
            
            return {
                "success": True,
                "result": notices[:limit],
                "count": len(notices[:limit])
            }
        
        elif tool_name == "get_notice_details":
            tracking_id = params.get("tracking_id")
            
            if not tracking_id:
                return {"success": False, "error": "Thiếu tracking_id"}
            
            notice = db_helper.get_record_by_tracking_id(tracking_id)
            
            if notice:
                return {
                    "success": True,
                    "result": notice
                }
            return {"success": False, "error": "Không tìm thấy công việc"}
        
        # Auto-reply suggestions
        elif tool_name == "suggest_actions":
            context = params.get("context", "")
            project_id = params.get("project_id")
            
            # Simple rule-based suggestions
            suggestions = []
            
            if "pending" in context.lower() or "chờ" in context.lower():
                suggestions.append({
                    "action": "check_pending",
                    "description": "Kiểm tra các công việc đang chờ",
                    "api": "get_pending_notices"
                })
            
            if "dự án" in context.lower() or "project" in context.lower():
                suggestions.append({
                    "action": "check_project_status",
                    "description": "Xem trạng thái dự án",
                    "api": "get_project_status"
                })
            
            if "khách hàng" in context.lower() or "customer" in context.lower():
                suggestions.append({
                    "action": "search_customer",
                    "description": "Tìm kiếm thông tin khách hàng",
                    "api": "search_customers"
                })
            
            return {
                "success": True,
                "result": {
                    "context": context,
                    "suggestions": suggestions if suggestions else [
                        {"action": "general", "description": "Tiếp tục cuộc trò chuyện bình thường"}
                    ]
                }
            }
        
        # Memory integration
        elif tool_name == "store_memory":
            content = params.get("content")
            memory_type = params.get("memory_type", "short_term")
            project_id = params.get("project_id")
            
            if not content:
                return {"success": False, "error": "Thiếu content"}
            
            # Store to appropriate memory layer
            if memory_type == "long_term":
                from src import ai_memory
                result = ai_memory.add_long_term_memory(
                    user_id=user_id,
                    content=content,
                    project_id=project_id
                )
            else:
                from src import ai_memory
                result = ai_memory.add_short_term_memory(
                    user_id=user_id,
                    content=content,
                    project_id=project_id
                )
            
            return {
                "success": True,
                "result": {"memory_id": result, "type": memory_type},
                "message": f"Đã lưu vào bộ nhớ {memory_type}"
            }
        
        elif tool_name == "recall_memories":
            query = params.get("query", "")
            limit = params.get("limit", 5)
            
            if not query:
                return {"success": False, "error": "Thiếu query"}
            
            from src import ai_memory
            memories = ai_memory.search_long_term_memory(user_id, query, limit=limit)
            
            return {
                "success": True,
                "result": memories,
                "count": len(memories)
            }
        
        # Code Tools
        elif tool_name in ["create_code", "create_drawing_code"]:
            name = params.get("name", "")
            # Support both 'category' and 'product_type'
            category = params.get("category") or params.get("product_type")
            employee = params.get("employee", "")
            
            if not category:
                return {"success": False, "error": "Thiếu category (loại sản phẩm)"}
            
            # Validate category
            valid_categories = ["SJT", "WLJ", "LSX", "ZZC", "ZWJ", "GZT", "WCP", "GZL", "BSX", "WLL", "GTX", "ZHT", "LHX"]
            if category not in valid_categories:
                return {"success": False, "error": f"Category không hợp lệ. Chọn một trong: {', '.join(valid_categories)}"}
            
            # Validate employee for SJT
            if category == "SJT" and not employee:
                return {"success": False, "error": "Category SJT cần employee (mã nhân viên 3 chữ số)"}
            
            if employee and (len(employee) != 3 or not employee.isdigit()):
                return {"success": False, "error": "Employee phải là 3 chữ số"}
            
            # Import server functions
            from server import generate_code, used_codes, save_data_data, history
            import datetime
            
            code = generate_code(used_codes, category, employee)
            if code:
                if category != "SJT":
                    if category not in used_codes:
                        used_codes[category] = set()
                    used_codes[category].add(code)
                history.append({
                    'name': name,
                    'employee': employee,
                    'category': category,
                    'code': code,
                    'time': datetime.datetime.now().isoformat(),
                    'parent_code': ''
                })
                save_data_data(used_codes, history)
                return {"success": True, "code": code, "message": f"Đã tạo mã {code}"}
            return {"success": False, "error": "Không còn mã available cho hạng mục này"}
        
        else:
            return {"success": False, "error": f"Tool '{tool_name}' không tồn tại"}
    
    except Exception as e:
        return {"success": False, "error": str(e)}


# ============================================
# TOOL REGISTRY
# ============================================

class ToolRegistry:
    """
    Central Registry để quản lý tất cả tools
    """
    
    def __init__(self):
        self._tools = None
        self._tool_map = None
    
    @property
    def tools(self):
        if self._tools is None:
            self._tools = get_extended_tool_definitions()
        return self._tools
    
    @property
    def tool_map(self):
        if self._tool_map is None:
            self._tool_map = {t["name"]: t for t in self.tools}
        return self._tool_map
    
    def get_tool(self, name: str) -> Optional[Dict]:
        """Lấy tool definition by name"""
        return self.tool_map.get(name)
    
    def get_tools_by_category(self, category: str) -> List[Dict]:
        """Lấy tools theo category"""
        # Map category to keywords in description
        category_map = {
            "project": ["dự án", "project"],
            "customer": ["khách hàng", "customer"],
            "chat": ["trò chuyện", "chat", "session"],
            "memory": ["nhớ", "memory", "bộ nhớ"],
            "notice": ["công việc", "notice", "thông báo"]
        }
        
        keywords = category_map.get(category, [category])
        return [
            t for t in self.tools
            if any(kw in t.get("description", "").lower() for kw in keywords)
        ]
    
    def execute(self, tool_name: str, user_id: int, parameters: Optional[Dict] = None) -> Dict:
        """Execute a tool"""
        return call_extended_tool(tool_name, user_id, parameters)


# Singleton instance
_tool_registry = None

def get_tool_registry() -> ToolRegistry:
    """Get singleton ToolRegistry instance"""
    global _tool_registry
    if _tool_registry is None:
        _tool_registry = ToolRegistry()
    return _tool_registry


# ============================================
# AGENT SYSTEM PROMPT UPDATE
# ============================================

def get_agent_tools_prompt() -> str:
    """
    Lấy system prompt mở rộng cho AI Agent
    """
    return f"""
{mcp_tools.get_tools_system_prompt()}

---

## PROJECT & BUSINESS TOOLS (MỚI)

### PROJECT TOOLS
14. **get_projects** - Lấy danh sách dự án của user
    - Gọi khi: User hỏi "dự án của tôi", "các dự án đang làm", "danh sách project"
    
15. **get_project_status** - Lấy trạng thái chi tiết của dự án
    - Gọi khi: User hỏi "dự án X sao rồi", "tiến độ dự án", "project ABC đang ở đâu"
    
16. **search_projects** - Tìm kiếm dự án
    - Gọi khi: User muốn tìm một dự án cụ thể

### CUSTOMER TOOLS
17. **get_customer_info** - Lấy thông tin khách hàng
    - Gọi khi: User hỏi về "khách hàng X", "thông tin KH", "ai đặt hàng này"
    
18. **search_customers** - Tìm kiếm khách hàng
    - Gọi khi: User muốn tìm thông tin khách hàng

### JOB/NOTICE TOOLS
19. **get_pending_notices** - Lấy danh sách công việc đang chờ
    - Gọi khi: User hỏi "còn việc gì chưa làm", "pending tasks"
    
20. **get_notice_details** - Lấy chi tiết một công việc
    - Gọi khi: User muốn xem chi tiết một công việc cụ thể

### SUGGESTION TOOLS
21. **suggest_actions** - Đề xuất hành động
    - Gọi khi: AI cần đề xuất hành động cho user

### MEMORY TOOLS
22. **store_memory** - Lưu thông tin vào bộ nhớ
    - Gọi khi: User cung cấp thông tin quan trọng cần nhớ
    
23. **recall_memories** - Tìm kiếm trong bộ nhớ
    - Gọi khi: Cần nhắc lại thông tin từ các cuộc trò chuyện trước

### CODE TOOLS
24. **create_code** - Tạo mã bản vẽ mới
    - Gọi khi: User yêu cầu 'tạo mã bản vẽ', 'tạo code mới', 'PLSX', 'PSJT', v.v.
    - IMPORTANT: Use parameter name `category` (NOT `loai_san_pham`, NOT `product_type`)
    - Category values: SJT, WLJ, LSX, ZZC, ZWJ, GZT, WCP, GZL, BSX, WLL, GTX, ZHT, LHX
    - Employee: Required for SJT (3 digits), optional for other categories

---

## AGENT CAPABILITIES (MỚI)

Bạn là một AI Agent thông minh có khả năng:

1. **Tự động tra cứu**: Khi user hỏi về dự án, khách hàng, công việc → tự gọi tools tương ứng
2. **Tự đề xuất**: Sau khi trả lời, đề xuất các hành động tiếp theo
3. **Ghi nhớ**: Lưu thông tin quan trọng vào bộ nhớ để nhớ cho các lần sau
4. **Tìm kiếm bộ nhớ**: Khi cần, tìm trong bộ nhớ để lấy thông tin đã lưu

## VÍ DỤ AGENT

### Ví dụ 1:
- User: "Dự án băng tải ABC sao rồi?"
- Action: 
  1. Gọi get_project_status({{"project_name": "băng tải ABC"}})
  2. Kết hợp kết quả để trả lời
  3. Gọi suggest_actions({{"context": "hỏi về tiến độ dự án"}})
- Trả lời: "Dự án băng tải ABC đang trong giai đoạn thiết kế, dự kiến hoàn thành..."

### Ví dụ 2:
- User: "Khách hàng XYZ đã đặt những dự án nào?"
- Action: 
  1. Gọi get_customer_info({{"customer_name": "XYZ"}})
- Trả lời: "Khách hàng XYZ có X dự án, bao gồm..."

### Ví dụ 3:
- User: "Nhớ rằng tôi thích màu xanh cho các sản phẩm băng tải"
- Action:
  1. Gọi store_memory({{"content": "User thích màu xanh cho băng tải", "memory_type": "long_term"}})
- Trả lời: "Đã nhớ! Lần sau khi thiết kế băng tải cho bạn, tôi sẽ ưu tiên màu xanh."

### Ví dụ 4:
- User: "Lần trước tôi nói gì về màu sắc?"
- Action:
  1. Gọi recall_memories({{"query": "màu sắc"}})
- Trả lời: "Lần trước bạn nói bạn thích màu xanh cho các sản phẩm băng tải."

### Ví dụ 5 (CODE TOOL):
- User: "Tạo mã bản vẽ mới cho băng tải LSX"
- Action:
  1. Gọi create_code({"category": "LSX", "name": "băng tải mới"})
  - Hoặc: create_drawing_code({"product_type": "LSX"})
- Trả lời: "Đã tạo mã PLSX001-0000-00-A0 cho băng tải của bạn."

### Ví dụ 6 (CODE TOOL):
- User: "Tạo mã bản vẽ SJT cho nhân viên 001"
- Action:
  1. Gọi create_code({"category": "SJT", "employee": "001", "name": "dự án XYZ"})
  - Hoặc: create_drawing_code({"product_type": "SJT", "employee": "001"})
- Trả lời: "Đã tạo mã PSJT001-0001-00-A0 cho dự án XYZ."

### Ví dụ 7 (PRODUCT_TYPE):
- User: "dùng tool tạo mã bản vẽ cho tôi LSX"
- Action:
  1. Gọi create_drawing_code({"product_type": "LSX"})
  - Hoặc: create_code({"product_type": "LSX"})
- Trả lời: "Đã tạo mã PLSX001-0000-00-A0."

### LƯU Ý QUAN TRỌNG CHO CODE TOOL:
- Có THỂ dùng `category` HOẶC `product_type` (cả hai đều được chấp nhận)
- KHÔNG BAO GIỜ dùng `loai_san_pham` hoặc `type`
- Tool name có thể là `create_code` HOẶC `create_drawing_code` (cả hai đều được chấp nhận)
- Ví dụ: {"product_type": "LSX"} = {"category": "LSX"}
"""


# ============================================
# EXPORT
# ============================================

__all__ = [
    "get_extended_tool_definitions",
    "call_extended_tool",
    "ToolRegistry",
    "get_tool_registry",
    "get_agent_tools_prompt"
]