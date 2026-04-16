# -*- coding: utf-8 -*-
"""
Agent Coordinator Module - Điều phối tất cả AI Agent components
Đây là main entry point cho AI Agent functionality
"""

from typing import Dict, List, Optional, Any
from src.agent_tools import (
    get_extended_tool_definitions,
    call_extended_tool,
    get_tool_registry,
    get_agent_tools_prompt
)
from src.intent_detector import (
    IntentDetector,
    detect_intent,
    get_intent_name,
    get_tools_for_message
)
from src.agent_planner import (
    AgentPlanner,
    ExecutionPlan,
    create_plan,
    execute_and_respond
)
from src.agent_triggers import (
    TriggerManager,
    get_trigger_manager,
    get_suggestions_for_user
)
from src import chat_service


# ============================================
# AGENT RESPONSE CLASS
# ============================================

class AgentResponse:
    """
    Response từ Agent - chứa tất cả thông tin cần thiết
    """
    
    def __init__(self):
        self.message: str = ""  # Final message to user
        self.intent: str = ""
        self.confidence: float = 0.0
        self.tools_used: List[str] = []
        self.tool_results: List[Dict] = []
        self.suggestions: List[str] = []
        self.trigger_results: List[Dict] = []
        self.context: Dict = {}
        self.is_agent_mode: bool = True
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "message": self.message,
            "intent": self.intent,
            "confidence": self.confidence,
            "tools_used": self.tools_used,
            "tool_results": self.tool_results,
            "suggestions": self.suggestions,
            "trigger_results": self.trigger_results,
            "context": self.context,
            "is_agent_mode": self.is_agent_mode
        }


# ============================================
# AGENT COORDINATOR CLASS
# ============================================

class AgentCoordinator:
    """
    Điều phối tất cả AI Agent components
    """
    
    def __init__(self, user_id: int = 1):
        self.user_id = user_id
        self.intent_detector = IntentDetector()
        self.planner = AgentPlanner(user_id)
        self.trigger_manager = get_trigger_manager()
        self.tool_registry = get_tool_registry()
        
        # Settings
        self.auto_trigger_enabled = True
        self.max_tools_per_request = 5
    
    def process_message(self, message: str, session_id: str = None, 
                       enable_agent_mode: bool = True) -> AgentResponse:
        """
        Process user message và return AgentResponse
        
        Args:
            message: Tin nhắn của user
            session_id: ID của session chat
            enable_agent_mode: Bật/tắt agent mode
            
        Returns:
            AgentResponse object
        """
        response = AgentResponse()
        response.is_agent_mode = enable_agent_mode
        
        if not enable_agent_mode:
            # Non-agent mode: just return message as-is
            response.message = message
            return response
        
        # Step 1: Detect intent
        intent_result = self.intent_detector.detect(message)
        response.intent = intent_result["intent"]
        response.confidence = intent_result["confidence"]
        response.context = intent_result.get("parameters", {})
        
        # Step 2: Check if should auto-trigger
        should_auto_trigger = (
            self.auto_trigger_enabled and 
            self.trigger_manager.should_auto_trigger(response.intent)
        )
        
        # Step 3: Create and execute plan
        plan = self.planner.plan(message, session_id, response.context)
        
        # Only execute if there are tools to call
        if plan.steps:
            plan = self.planner.execute_plan(plan)
            response.tools_used = [s["tool"] for s in plan.steps]
            response.tool_results = plan.execution_results
            
            # Step 4: Build response from tool results
            response.message = self._build_response_from_results(
                message, response.tool_results
            )
        
        # Step 5: Add trigger suggestions if enabled
        if should_auto_trigger:
            suggestions = self._get_trigger_suggestions()
            response.suggestions = suggestions
        
        # If no tools executed, use message as-is
        if not response.message:
            response.message = message
        
        return response
    
    def execute_tools(self, tools: List[Dict]) -> List[Dict]:
        """
        Execute a list of tools
        
        Args:
            tools: List of tool calls, each with 'name' and 'parameters'
            
        Returns:
            List of results
        """
        results = []
        
        for tool_call in tools:
            tool_name = tool_call.get("name")
            parameters = tool_call.get("parameters", {})
            
            result = call_extended_tool(tool_name, self.user_id, parameters)
            results.append(result)
        
        return results
    
    def get_tools_definitions(self) -> List[Dict]:
        """Get all available tools"""
        return get_extended_tool_definitions()
    
    def get_tools_prompt(self) -> str:
        """Get system prompt for tools"""
        return get_agent_tools_prompt()
    
    def check_triggers(self) -> List[Dict]:
        """Check all triggers and return results"""
        from src import db_helper
        
        projects = db_helper.get_projects_by_user(self.user_id)
        notices = db_helper.get_pending_notices(self.user_id)
        
        return self.trigger_manager.check_triggers({
            "projects": projects,
            "notices": notices
        })
    
    def _build_response_from_results(self, original_message: str, 
                                     results: List[Dict]) -> str:
        """Build user-facing message from tool results"""
        if not results:
            return ""
        
        response_parts = []
        
        for result in results:
            if not result.get("success"):
                continue
            
            data = result.get("result")
            tool_name = result.get("tool_name", "unknown")
            
            if not data:
                continue
            
            # Format based on tool type
            if tool_name == "get_projects":
                if isinstance(data, list) and len(data) > 0:
                    response_parts.append(self._format_projects(data))
                    
            elif tool_name == "get_project_status":
                if isinstance(data, dict):
                    response_parts.append(self._format_project_status(data))
                    
            elif tool_name == "search_projects":
                if isinstance(data, list) and len(data) > 0:
                    response_parts.append(self._format_search_results(data, "dự án"))
                else:
                    response_parts.append("Không tìm thấy dự án nào phù hợp.")
                    
            elif tool_name == "get_customer_info":
                if isinstance(data, dict):
                    response_parts.append(self._format_customer_info(data))
                    
            elif tool_name == "search_customers":
                if isinstance(data, list) and len(data) > 0:
                    response_parts.append(self._format_search_results(data, "khách hàng"))
                else:
                    response_parts.append("Không tìm thấy khách hàng nào phù hợp.")
                    
            elif tool_name == "get_pending_notices":
                if isinstance(data, list) and len(data) > 0:
                    response_parts.append(self._format_notices(data))
                else:
                    response_parts.append("Không có công việc nào đang chờ.")
                    
            elif tool_name == "search_chat_history":
                if isinstance(data, list) and len(data) > 0:
                    response_parts.append(self._format_chat_history(data))
                else:
                    response_parts.append("Không tìm thấy nội dung liên quan trong lịch sử.")
        
        return "\n\n".join(response_parts) if response_parts else ""
    
    def _format_projects(self, projects: List[Dict]) -> str:
        """Format projects list"""
        lines = ["📋 Danh sách dự án:"]
        for p in projects[:5]:
            name = p.get("Project Name", "Unknown")
            status = p.get("Status", "")
            lines.append(f"  • {name} - {status}")
        
        if len(projects) > 5:
            lines.append(f"  ... và {len(projects) - 5} dự án khác")
        
        return "\n".join(lines)
    
    def _format_project_status(self, project: Dict) -> str:
        """Format single project status"""
        name = project.get("project_name", project.get("Project Name", "Unknown"))
        status = project.get("status", project.get("Status", ""))
        engineer = project.get("engineer", project.get("Engineer", ""))
        
        lines = [f"📊 Thông tin dự án: {name}"]
        lines.append(f"  Trạng thái: {status}")
        
        if engineer:
            lines.append(f"  Engineer: {engineer}")
        
        return "\n".join(lines)
    
    def _format_customer_info(self, customer: Dict) -> str:
        """Format customer info"""
        name = customer.get("customer_name", "Unknown")
        count = customer.get("total_projects", 0)
        
        lines = [f"👤 Thông tin khách hàng: {name}"]
        lines.append(f"  Tổng số dự án: {count}")
        
        recent = customer.get("recent_projects", [])
        if recent:
            lines.append("  Dự án gần đây:")
            for p in recent[:3]:
                lines.append(f"    • {p.get('project_name', '')} - {p.get('status', '')}")
        
        return "\n".join(lines)
    
    def _format_notices(self, notices: List[Dict]) -> str:
        """Format notices list"""
        lines = [f"📝 Công việc đang chờ ({len(notices)}):"]
        for n in notices[:5]:
            name = n.get("Project Name", "Unknown")
            status = n.get("Status", "")
            lines.append(f"  • {name} - {status}")
        
        return "\n".join(lines)
    
    def _format_search_results(self, results: List[Dict], item_type: str) -> str:
        """Format search results"""
        lines = [f"🔍 Kết quả tìm kiếm {item_type}: "]
        for r in results[:5]:
            name = r.get("Project Name", r.get("Customer", "Unknown"))
            lines.append(f"  • {name}")
        
        if len(results) > 5:
            lines.append(f"  ... và {len(results) - 5} kết quả khác")
        
        return "\n".join(lines)
    
    def _format_chat_history(self, results: List[Dict]) -> str:
        """Format chat history search results"""
        lines = ["📜 Kết quả tìm kiếm trong lịch sử:"]
        for r in results[:3]:
            content = r.get("content", r.get("message", ""))[:100]
            session_title = r.get("session_title", "")
            if session_title:
                lines.append(f"  • [{session_title}] {content}...")
            else:
                lines.append(f"  • {content}...")
        
        return "\n".join(lines)
    
    def _get_trigger_suggestions(self) -> List[str]:
        """Get trigger suggestions for user"""
        try:
            return get_suggestions_for_user(self.user_id, limit=3)
        except:
            return []


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

# Singleton instance
_agent_coordinator = None

def get_agent_coordinator(user_id: int = 1) -> AgentCoordinator:
    """Get singleton AgentCoordinator instance"""
    global _agent_coordinator
    if _agent_coordinator is None:
        _agent_coordinator = AgentCoordinator(user_id)
    else:
        _agent_coordinator.user_id = user_id
    return _agent_coordinator


def process_agent_message(message: str, user_id: int = 1, 
                          session_id: str = None) -> Dict:
    """
    Convenience function để process message qua Agent
    
    Returns:
        Dict với response, intent, tools_used, suggestions
    """
    coordinator = get_agent_coordinator(user_id)
    response = coordinator.process_message(message, session_id)
    return response.to_dict()


def get_agent_tools() -> List[Dict]:
    """Get all available tools for Agent"""
    coordinator = get_agent_coordinator()
    return coordinator.get_tools_definitions()


def get_agent_system_prompt() -> str:
    """Get system prompt for Agent"""
    coordinator = get_agent_coordinator()
    return coordinator.get_tools_prompt()


# ============================================
# TEST
# ============================================

def test_agent_coordinator():
    """Test Agent Coordinator"""
    coordinator = AgentCoordinator(user_id=1)
    
    test_messages = [
        "Dự án băng tải ABC sao rồi?",
        "Khách hàng XYZ đã đặt những dự án nào?",
        "Còn công việc gì chưa làm không?",
        "Xin chào"
    ]
    
    print("=== Agent Coordinator Test ===")
    for msg in test_messages:
        print(f"\n--- Message: {msg} ---")
        
        response = coordinator.process_message(msg)
        
        print(f"Intent: {response.intent}")
        print(f"Confidence: {response.confidence:.2f}")
        print(f"Tools used: {response.tools_used}")
        print(f"Message: {response.message[:200]}...")
        print(f"Suggestions: {response.suggestions[:2]}")


# Export
__all__ = [
    "AgentResponse",
    "AgentCoordinator",
    "get_agent_coordinator",
    "process_agent_message",
    "get_agent_tools",
    "get_agent_system_prompt",
    "test_agent_coordinator"
]