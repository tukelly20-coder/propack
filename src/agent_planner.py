# -*- coding: utf-8 -*-
"""
Agent Planner Module - Lập kế hoạch tool execution cho AI Agent
AI Agent sử dụng để xác định sequence của tool calls
"""

from typing import Dict, List, Optional, Any
from src.intent_detector import IntentDetector, detect_intent
from src.agent_tools import get_tool_registry, call_extended_tool
from src import chat_service


# ============================================
# PLANNER RESULT CLASS
# ============================================

class ExecutionPlan:
    """
    Kết quả lập kế hoạch - chứa danh sách tools cần gọi và thứ tự
    """
    
    def __init__(self):
        self.steps: List[Dict] = []
        self.intent: str = ""
        self.confidence: float = 0.0
        self.context: Dict = {}
        self.execution_results: List[Dict] = []
        self.is_executed: bool = False
    
    def add_step(self, tool_name: str, parameters: Dict = None, reason: str = ""):
        """Thêm một bước vào plan"""
        self.steps.append({
            "tool": tool_name,
            "parameters": parameters or {},
            "reason": reason,
            "executed": False,
            "result": None,
            "error": None
        })
    
    def mark_executed(self, step_index: int, result: Dict):
        """Đánh dấu bước đã thực thi"""
        if step_index < len(self.steps):
            self.steps[step_index]["executed"] = True
            self.steps[step_index]["result"] = result
    
    def get_next_step(self) -> Optional[Dict]:
        """Lấy bước tiếp theo chưa thực thi"""
        for step in self.steps:
            if not step["executed"]:
                return step
        return None
    
    def is_complete(self) -> bool:
        """Kiểm tra xem plan đã hoàn thành chưa"""
        return all(step["executed"] for step in self.steps)
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            "intent": self.intent,
            "confidence": self.confidence,
            "steps": self.steps,
            "context": self.context,
            "is_complete": self.is_complete()
        }


# ============================================
# AGENT PLANNER CLASS
# ============================================

class AgentPlanner:
    """
    Planner cho AI Agent - Lập kế hoạch tool execution
    """
    
    def __init__(self, user_id: int = 1):
        self.user_id = user_id
        self.intent_detector = IntentDetector()
        self.tool_registry = get_tool_registry()
        
        # Max tools per plan to prevent abuse
        self.max_tools = 5
        
        # Timeout for tool execution (seconds)
        self.tool_timeout = 10
    
    def plan(self, user_message: str, session_id: str = None, context: Dict = None) -> ExecutionPlan:
        """
        Lập kế hoạch thực thi tools dựa trên user message
        
        Args:
            user_message: Tin nhắn của user
            session_id: ID của session chat
            context: Additional context (optional)
            
        Returns:
            ExecutionPlan object
        """
        plan = ExecutionPlan()
        
        # Step 1: Detect intent
        intent_result = self.intent_detector.detect(user_message)
        plan.intent = intent_result["intent"]
        plan.confidence = intent_result["confidence"]
        plan.context = context or {}
        
        # Add detected parameters to context
        if intent_result.get("parameters"):
            plan.context.update(intent_result["parameters"])
        
        # Step 2: Get tools for this intent
        tools = intent_result.get("tools", [])
        
        # If no tools from intent, try keyword detection
        if not tools:
            detected_tools = self._detect_tools_from_message(user_message)
            tools = detected_tools[:self.max_tools]
        
        # Step 3: Filter and prioritize tools
        tools = self._filter_tools(tools, intent_result)
        
        # Step 4: Create execution steps
        for tool_name in tools:
            tool_def = self.tool_registry.get_tool(tool_name)
            if tool_def:
                # Extract parameters from message
                params = self._extract_tool_parameters(tool_name, user_message, plan.context)
                reason = f"Intent: {intent_result.get('description', '')}"
                plan.add_step(tool_name, params, reason)
        
        return plan
    
    def execute_plan(self, plan: ExecutionPlan) -> ExecutionPlan:
        """
        Thực thi plan và trả về kết quả
        
        Args:
            plan: ExecutionPlan object
            
        Returns:
            ExecutionPlan với results
        """
        if plan.is_executed:
            return plan
        
        # Execute each step sequentially
        for i, step in enumerate(plan.steps):
            tool_name = step["tool"]
            params = step["parameters"]
            
            try:
                result = call_extended_tool(tool_name, self.user_id, params)
                plan.mark_executed(i, result)
                plan.execution_results.append(result)
                
                # Extract context from results for next step
                if result.get("success") and result.get("result"):
                    self._update_context_from_result(plan, result)
                    
            except Exception as e:
                error_result = {"success": False, "error": str(e)}
                plan.mark_executed(i, error_result)
                plan.execution_results.append(error_result)
        
        plan.is_executed = True
        return plan
    
    def execute_single_tool(self, tool_name: str, parameters: Dict = None) -> Dict:
        """
        Thực thi một tool duy nhất
        
        Args:
            tool_name: Tên tool
            parameters: Parameters
            
        Returns:
            Kết quả từ tool
        """
        return call_extended_tool(tool_name, self.user_id, parameters)
    
    def _detect_tools_from_message(self, message: str) -> List[str]:
        """Detect tools from message using keyword mapping"""
        from src.intent_detector import KEYWORD_TO_TOOL
        
        message_lower = message.lower()
        tools = []
        
        for keyword, tool in KEYWORD_TO_TOOL.items():
            if keyword in message_lower and tool not in tools:
                tools.append(tool)
        
        return tools
    
    def _filter_tools(self, tools: List[str], intent_result: Dict) -> List[str]:
        """Filter tools based on intent and confidence"""
        if not tools:
            return []
        
        # If high confidence, take top 2-3 tools
        if intent_result.get("confidence", 0) > 0.7:
            return tools[:3]
        
        # If medium confidence, take top 1-2 tools
        elif intent_result.get("confidence", 0) > 0.4:
            return tools[:2]
        
        # Otherwise, take just the first tool
        return tools[:1]
    
    def _extract_tool_parameters(self, tool_name: str, message: str, context: Dict) -> Dict:
        """Extract parameters for a specific tool from message"""
        params = {}
        
        # Use context parameters if available
        if context:
            if "project_name" in context:
                params["project_name"] = context["project_name"]
            if "customer_name" in context:
                params["customer_name"] = context["customer_name"]
            if "tracking_id" in context:
                params["tracking_id"] = context["tracking_id"]
        
        # Add default parameters based on tool
        if tool_name in ["get_projects", "get_pending_notices"]:
            params["limit"] = 10
        
        # Create code tool - extract product_type
        elif tool_name in ["create_code", "create_drawing_code"]:
            if "product_type" in context:
                params["product_type"] = context["product_type"]
            if "category" in context:
                params["category"] = context["category"]
        
        elif tool_name == "search_projects":
            # Try to extract query from message
            query = self._extract_search_query(message)
            if query:
                params["query"] = query
        
        elif tool_name == "search_customers":
            query = self._extract_search_query(message)
            if query:
                params["query"] = query
        
        elif tool_name == "search_chat_history":
            query = self._extract_search_query(message)
            if query:
                params["query"] = query
                params["limit"] = 5
        
        return params
    
    def _extract_search_query(self, message: str) -> Optional[str]:
        """Extract search query from message"""
        import re
        
        # Common patterns for search queries
        patterns = [
            r"tìm\s+(?:dự án|khách hàng|project|customer)?\s*(.+?)(?:\s+được\s+không|\s+$|$)",
            r"xem\s+(.+?)(?:\s+sao|\s+thế|$)",
            r"về\s+(.+?)(?:\s+thế nào|\s+ra sao|$)",
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return None
    
    def _update_context_from_result(self, plan: ExecutionPlan, result: Dict):
        """Update plan context from tool execution result"""
        # Extract useful info from result for subsequent steps
        if result.get("success") and result.get("result"):
            result_data = result["result"]
            
            # If result is a list, get first item
            if isinstance(result_data, list) and len(result_data) > 0:
                first_item = result_data[0]
                if isinstance(first_item, dict):
                    # Extract tracking_id if available
                    if "Tracking ID" in first_item:
                        plan.context["tracking_id"] = first_item["Tracking ID"]
                    if "session_id" in first_item:
                        plan.context["session_id"] = first_item["session_id"]


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

def create_plan(user_message: str, user_id: int = 1, session_id: str = None) -> ExecutionPlan:
    """Create execution plan from user message"""
    planner = AgentPlanner(user_id)
    return planner.plan(user_message, session_id)


def execute_and_respond(user_message: str, user_id: int = 1) -> Dict:
    """
    Convenience function: Detect intent, execute tools, return response
    
    Returns:
        Dict với keys: response, tools_used, results
    """
    planner = AgentPlanner(user_id)
    
    # Create and execute plan
    plan = planner.plan(user_message)
    plan = planner.execute_plan(plan)
    
    # Build response
    response_parts = []
    
    for step in plan.steps:
        if step["executed"] and step["result"]:
            result = step["result"]
            if result.get("success"):
                response_parts.append({
                    "tool": step["tool"],
                    "data": result.get("result")
                })
    
    return {
        "intent": plan.intent,
        "confidence": plan.confidence,
        "response": response_parts,
        "tools_used": [s["tool"] for s in plan.steps],
        "is_complete": plan.is_complete()
    }


# ============================================
# TEST
# ============================================

def test_planner():
    """Test agent planner"""
    test_messages = [
        "Dự án băng tải ABC sao rồi?",
        "Khách hàng XYZ đã đặt những dự án nào?",
        "Lần trước ta nói gì về mã bản vẽ?",
        "Còn công việc gì chưa làm không?",
        "Xin chào"
    ]
    
    planner = AgentPlanner(user_id=1)
    
    print("=== Agent Planner Test ===")
    for msg in test_messages:
        print(f"\n--- Message: {msg} ---")
        
        # Plan
        plan = planner.plan(msg)
        print(f"Intent: {plan.intent} (confidence: {plan.confidence:.2f})")
        print(f"Steps planned: {[s['tool'] for s in plan.steps]}")
        
        # Execute
        plan = planner.execute_plan(plan)
        print(f"Executed: {plan.is_complete()}")
        
        # Results
        for i, step in enumerate(plan.steps):
            result = step["result"]
            if result:
                status = "✓" if result.get("success") else "✗"
                print(f"  {status} {step['tool']}: {str(result)[:100]}")


# Export
__all__ = [
    "ExecutionPlan",
    "AgentPlanner",
    "create_plan",
    "execute_and_respond",
    "test_planner"
]