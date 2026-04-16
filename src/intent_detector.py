# -*- coding: utf-8 -*-
"""
Intent Detector Module - Phát hiện user intent từ message
AI Agent sử dụng để xác định user muốn gì và chọn tools phù hợp
"""

from typing import Dict, List, Optional, Tuple
import re

# ============================================
# INTENT PATTERNS DEFINITIONS
# ============================================

# Các pattern để detect intent
INTENT_PATTERNS = {
    "project_query": {
        "keywords": [
            "dự án", "project", "tiến độ", "status", "ra sao", "thế nào",
            "đang làm gì", "làm đến đâu", "bao giờ xong", "deadline",
            "băng tải", "thiết kế", "bản vẽ", "sản phẩm"
        ],
        "tools": ["get_projects", "get_project_status", "search_projects"],
        "auto_trigger": True,
        "description": "User hỏi về dự án/công việc"
    },
    "customer_query": {
        "keywords": [
            "khách hàng", "customer", "KH", "ai đó", "đặt hàng",
            "client", "công ty", "doanh nghiệp", "người mua"
        ],
        "tools": ["get_customer_info", "search_customers"],
        "auto_trigger": True,
        "description": "User hỏi về khách hàng"
    },
    "history_query": {
        "keywords": [
            "lần trước", "trước đó", "hôm qua", "đã hỏi", "đã nói",
            "trước", "hôm trước", "tuần trước", "tháng trước",
            "nhắc lại", "nhớ không", "có nhớ không"
        ],
        "tools": ["search_chat_history", "get_user_sessions", "recall_memories"],
        "auto_trigger": True,
        "description": "User hỏi về lịch sử/nội dung đã thảo luận"
    },
    "system_state_query": {
        "keywords": [
            "hiện tại", "đang làm", "đang là", "hiện giờ",
            "now", "current", "đang ở đâu", "step hiện tại"
        ],
        "tools": ["get_system_state", "get_ai_context"],
        "auto_trigger": True,
        "description": "User hỏi về trạng thái hiện tại"
    },
    "pending_tasks": {
        "keywords": [
            "pending", "chờ", "còn gì", "chưa làm", "chưa xong",
            "việc gì", "task", "công việc", "job", "todo"
        ],
        "tools": ["get_pending_notices"],
        "auto_trigger": True,
        "description": "User hỏi về công việc đang chờ"
    },
    "session_management": {
        "keywords": [
            "cuộc trò chuyện mới", "tạo chat mới", "bắt đầu mới",
            "xóa cuộc trò chuyện", "xóa chat", "delete session",
            "export", "xuất", "lưu"
        ],
        "tools": ["create_session", "delete_session", "export_session"],
        "auto_trigger": True,
        "description": "User muốn quản lý cuộc trò chuyện"
    },
    "memory_storage": {
        "keywords": [
            "nhớ", "ghi nhớ", "lưu lại", "note", "nhắc tôi",
            "remember", "save", "ghi chú", "lưu ý"
        ],
        "tools": ["store_memory"],
        "auto_trigger": True,
        "description": "User muốn lưu thông tin vào bộ nhớ"
    },
    "help_request": {
        "keywords": [
            "giúp", "help", "hỗ trợ", "trợ giúp", "ai đó",
            "làm sao", "như thế nào", "cách nào", "chỉ tôi"
        ],
        "tools": ["get_system_state", "get_user_sessions"],
        "auto_trigger": True,
        "description": "User cần hỗ trợ/trợ giúp"
    },
    "create_code": {
        "keywords": [
            "tạo mã bản vẽ", "tạo mã", "tạo code", "sinh mã", "mã bản vẽ", "drawing code",
            "tao ma ban ve", "tao ma", "tao code", "sinh ma", "ma ban ve",
            "PLSX", "PSJT", "PWLJ", "PZZC", "PGZT", "PWCP",
            "LSX", "SJT", "WLJ", "ZZC", "GZT", "WCP", "ZWJ", "GZL",
            "BSX", "WLL", "GTX", "ZHT", "LHX", "băng tải", "流水线"
        ],
        "tools": ["create_code", "create_drawing_code"],
        "auto_trigger": True,
        "description": "User yêu cầu tạo mã bản vẽ mới"
    },
    "general_chat": {
        "keywords": [],  # Empty = fallback
        "tools": [],
        "auto_trigger": False,
        "description": "General conversation"
    }
}

# ============================================
# KEYWORD TO TOOL MAPPING
# ============================================

KEYWORD_TO_TOOL = {
    # Project-related
    "dự án": "get_projects",
    "project": "get_projects",
    "tiến độ": "get_project_status",
    "status": "get_project_status",
    "băng tải": "search_projects",
    "thiết kế": "get_project_status",
    
    # Customer-related
    "khách hàng": "get_customer_info",
    "customer": "get_customer_info",
    "KH": "get_customer_info",
    "đặt hàng": "get_customer_info",
    
    # History-related
    "lần trước": "search_chat_history",
    "trước đó": "search_chat_history",
    "hôm qua": "search_chat_history",
    "đã hỏi": "search_chat_history",
    "đã nói": "search_chat_history",
    "nhắc lại": "recall_memories",
    
    # System state
    "hiện tại": "get_system_state",
    "đang làm": "get_system_state",
    "đang là": "get_system_state",
    
    # Pending tasks
    "pending": "get_pending_notices",
    "chờ": "get_pending_notices",
    "còn gì": "get_pending_notices",
    "việc gì": "get_pending_notices",
    "công việc": "get_pending_notices",
    
    # Create code
    "tạo mã": "create_code",
    "tạo code": "create_code",
    "sinh mã": "create_code",
    "mã bản vẽ": "create_code",
    "PLSX": "create_code",
    "PSJT": "create_code",
    "PWLJ": "create_code",
    "băng tải": "create_code",
    
    # Memory
    "nhớ": "store_memory",
    "ghi nhớ": "store_memory",
    "lưu lại": "store_memory",
}


# ============================================
# INTENT DETECTOR CLASS
# ============================================

class IntentDetector:
    """
    Phát hiện intent từ user message
    """
    
    def __init__(self):
        self.patterns = INTENT_PATTERNS
        self.keyword_to_tool = KEYWORD_TO_TOOL
        
        # Build regex patterns for efficiency
        self._build_patterns()
    
    def _build_patterns(self):
        """Build regex patterns for keyword matching"""
        self._compiled_patterns = {}
        
        for intent_name, intent_data in self.patterns.items():
            keywords = intent_data.get("keywords", [])
            if keywords:
                # Build pattern from keywords
                pattern_str = "|".join(re.escape(kw) for kw in keywords)
                try:
                    self._compiled_patterns[intent_name] = re.compile(
                        pattern_str, re.IGNORECASE
                    )
                except re.error:
                    pass  # Skip invalid patterns
    
    def detect(self, message: str) -> Dict:
        """
        Phát hiện intent từ message
        
        Args:
            message: Tin nhắn của user
            
        Returns:
            Dict với keys: intent, confidence, tools, parameters
        """
        if not message:
            return {
                "intent": "general_chat",
                "confidence": 0.0,
                "tools": [],
                "parameters": {}
            }
        
        message_lower = message.lower()
        
        # Step 1: Check for exact intent patterns
        best_intent = None
        best_confidence = 0.0
        
        for intent_name, pattern in self._compiled_patterns.items():
            if pattern.search(message_lower):
                confidence = self._calculate_confidence(message_lower, intent_name)
                if confidence > best_confidence:
                    best_intent = intent_name
                    best_confidence = confidence
        
        # Step 2: If no pattern matched, check keyword-to-tool mapping
        if best_intent is None:
            detected_tools = self._detect_tools_from_keywords(message_lower)
            if detected_tools:
                best_intent = "general_chat"  # Fallback with tools
                best_confidence = 0.5
            else:
                best_intent = "general_chat"
                best_confidence = 0.3
        
        # Get intent data
        intent_data = self.patterns.get(best_intent, {})
        
        # Extract potential parameters from message
        parameters = self._extract_parameters(message)
        
        return {
            "intent": best_intent,
            "confidence": best_confidence,
            "tools": intent_data.get("tools", []),
            "auto_trigger": intent_data.get("auto_trigger", False),
            "description": intent_data.get("description", ""),
            "parameters": parameters,
            "detected_keywords": self._extract_keywords(message_lower)
        }
    
    def _calculate_confidence(self, message_lower: str, intent_name: str) -> float:
        """Calculate confidence score based on keyword density"""
        intent_data = self.patterns.get(intent_name, {})
        keywords = intent_data.get("keywords", [])
        
        if not keywords:
            return 0.0
        
        # Count matching keywords
        matches = sum(1 for kw in keywords if kw.lower() in message_lower)
        
        # Calculate ratio
        confidence = min(matches / len(keywords), 1.0)
        
        # Boost if message is short and contains keywords (high relevance)
        if len(message_lower.split()) < 20 and matches > 0:
            confidence = min(confidence + 0.2, 1.0)
        
        return confidence
    
    def _detect_tools_from_keywords(self, message_lower: str) -> List[str]:
        """Detect tools based on keywords in message"""
        tools = []
        
        for keyword, tool in self.keyword_to_tool.items():
            if keyword in message_lower and tool not in tools:
                tools.append(tool)
        
        return tools
    
    def _extract_parameters(self, message: str) -> Dict:
        """Extract potential parameters from message"""
        params = {}
        
        # Extract project name patterns
        project_patterns = [
            r"(?:dự án|project)[:\s]+([A-Za-z0-9\s]+?)(?:\s+sao|\s+thế|\s+ra|\s+đang|\s+còn|$)",
            r"(?:băng tải|thiết kế)[:\s]+([A-Za-z0-9\s]+?)(?:\s+sao|\s+thế|\s+ra|$)",
        ]
        
        for pattern in project_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                params["project_name"] = match.group(1).strip()
                break
        
        # Extract customer name patterns
        customer_patterns = [
            r"(?:khách hàng|KH|customer)[:\s]+([A-Za-z0-9\s]+?)(?:\s+đã|\s+đặt|\s+có|$)",
        ]
        
        for pattern in customer_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                params["customer_name"] = match.group(1).strip()
                break
        
        # Extract tracking ID
        id_patterns = [
            r"(?:tracking|ID)[:\s]*(\d+)",
            r"(?:mã|số)[:\s]*(\d+)",
        ]
        
        for pattern in id_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                params["tracking_id"] = int(match.group(1))
                break
        
        # Extract product_type/category for create_code
        product_type_patterns = [
            r"(LSX|SJT|WLJ|ZZC|GZT|WCP|ZWJ|GZL|BSX|WLL|GTX|ZHT|LHX)",
        ]
        
        for pattern in product_type_patterns:
            match = re.search(pattern, message, re.IGNORECASE)
            if match:
                params["product_type"] = match.group(1).upper()
                break
        
        return params
    
    def _extract_keywords(self, message_lower: str) -> List[str]:
        """Extract all matched keywords from message"""
        matched = []
        
        for intent_name, intent_data in self.patterns.items():
            keywords = intent_data.get("keywords", [])
            for kw in keywords:
                if kw.lower() in message_lower:
                    matched.append(kw)
        
        return list(set(matched))
    
    def get_tools_for_intent(self, intent: str) -> List[str]:
        """Get list of tools for a specific intent"""
        intent_data = self.patterns.get(intent, {})
        return intent_data.get("tools", [])
    
    def should_auto_trigger(self, intent: str) -> bool:
        """Check if intent should auto-trigger tool execution"""
        intent_data = self.patterns.get(intent, {})
        return intent_data.get("auto_trigger", False)


# ============================================
# HELPER FUNCTIONS
# ============================================

def detect_intent(message: str) -> Dict:
    """
    Convenience function để detect intent
    """
    detector = IntentDetector()
    return detector.detect(message)


def get_intent_name(message: str) -> str:
    """
    Convenience function để get intent name only
    """
    detector = IntentDetector()
    result = detector.detect(message)
    return result.get("intent", "general_chat")


def get_tools_for_message(message: str) -> List[str]:
    """
    Convenience function để get tools cho một message
    """
    detector = IntentDetector()
    result = detector.detect(message)
    return result.get("tools", [])


# ============================================
# TEST
# ============================================

def test_intent_detector():
    """Test intent detector with sample messages"""
    test_cases = [
        "Dự án băng tải ABC sao rồi?",
        "Khách hàng XYZ đã đặt những dự án nào?",
        "Lần trước ta nói gì về mã bản vẽ?",
        "Hiện tại đang làm gì?",
        "Còn công việc gì chưa làm không?",
        "Nhớ rằng tôi thích màu xanh",
        "Tạo cuộc trò chuyện mới cho tôi",
        "Giúp tôi với",
        "Xin chào"
    ]
    
    detector = IntentDetector()
    
    print("=== Intent Detection Test ===")
    for msg in test_cases:
        result = detector.detect(msg)
        print(f"\nMessage: {msg}")
        print(f"  Intent: {result['intent']}")
        print(f"  Confidence: {result['confidence']:.2f}")
        print(f"  Tools: {result['tools']}")
        print(f"  Auto-trigger: {result['auto_trigger']}")
        print(f"  Parameters: {result['parameters']}")


# Export
__all__ = [
    "IntentDetector",
    "INTENT_PATTERNS",
    "KEYWORD_TO_TOOL",
    "detect_intent",
    "get_intent_name",
    "get_tools_for_message",
    "test_intent_detector"
]