# -*- coding: utf-8 -*-
"""
Agent Triggers Module - Auto-trigger system cho AI Agent
Tự động kích hoạt suggestions khi có điều kiện thỏa mãn
"""

from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from datetime import datetime, timedelta

# ============================================
# TRIGGER DEFINITIONS
# ============================================

@dataclass
class Trigger:
    """Trigger definition"""
    name: str
    condition: Callable[[Dict], bool]
    action: str
    message_template: str
    priority: int = 0  # Higher = more important


# ============================================
# BUILT-IN TRIGGER CONDITIONS
# ============================================

def project_pending_condition(project: Dict) -> bool:
    """Check if project is pending for too long"""
    status = project.get("Status", "").lower()
    if "pending" in status or "chờ" in status:
        # Check if there's a created date to calculate days
        created_date = project.get("Created Date")
        if created_date:
            try:
                # Simple date parsing (assuming format DD/MM/YYYY or similar)
                if isinstance(created_date, str):
                    # Try to parse date
                    from datetime import datetime
                    try:
                        dt = datetime.strptime(created_date, "%d/%m/%Y")
                        days_pending = (datetime.now() - dt).days
                        return days_pending > 3
                    except:
                        pass
            except:
                pass
    return False


def no_engineer_condition(project: Dict) -> bool:
    """Check if project has no engineer assigned"""
    engineer = project.get("Engineer", "")
    return not engineer or engineer.strip() == ""


def urgent_project_condition(project: Dict) -> bool:
    """Check if project is urgent"""
    urgency = project.get("Urgency", "").lower()
    return "urgent" in urgency or "khẩn" in urgency


def overdue_condition(project: Dict) -> bool:
    """Check if project is overdue past desired time"""
    desired_time = project.get("Desired Time")
    if desired_time:
        try:
            if isinstance(desired_time, str):
                from datetime import datetime
                try:
                    dt = datetime.strptime(desired_time, "%d/%m/%Y")
                    return dt < datetime.now()
                except:
                    pass
        except:
            pass
    return False


def pending_notices_condition(notice: Dict) -> bool:
    """Check if there are pending notices"""
    status = notice.get("Status", "").lower()
    return "pending" in status or "chờ" in status


# ============================================
# BUILT-IN TRIGGERS
# ============================================

TRIGGERS = [
    # Project Triggers
    Trigger(
        name="project_pending_long",
        condition=project_pending_condition,
        action="suggest_check_project",
        message_template="⚠️ Dự án '{project_name}' đang pending {days} ngày. Cần kiểm tra tiến độ?",
        priority=10
    ),
    Trigger(
        name="no_engineer_assigned",
        condition=no_engineer_condition,
        action="suggest_assign_engineer",
        message_template="📋 Dự án '{project_name}' chưa có người phụ trách. Cần assign engineer?",
        priority=9
    ),
    Trigger(
        name="urgent_project",
        condition=urgent_project_condition,
        action="alert_urgent",
        message_template="🔥 Dự án '{project_name}' có mức độ khẩn cấp cao. Cần ưu tiên xử lý!",
        priority=8
    ),
    Trigger(
        name="project_overdue",
        condition=overdue_condition,
        action="alert_overdue",
        message_template="⏰ Dự án '{project_name}' đã quá hạn mong muốn. Cần xử lý gấp!",
        priority=7
    ),
    # Notice Triggers
    Trigger(
        name="pending_notices_exist",
        condition=pending_notices_condition,
        action="show_pending_notices",
        message_template="📝 Có {count} công việc đang chờ xử lý.",
        priority=5
    ),
]


# ============================================
# TRIGGER MANAGER CLASS
# ============================================

class TriggerManager:
    """
    Quản lý các triggers - kiểm tra conditions và đề xuất actions
    """
    
    def __init__(self):
        self.triggers = TRIGGERS.copy()
        self.custom_triggers: List[Trigger] = []
        
        # Cache kết quả trigger
        self._last_check_time = None
        self._cached_results = []
    
    @property
    def all_triggers(self) -> List[Trigger]:
        """Get all triggers (built-in + custom)"""
        return self.triggers + self.custom_triggers
    
    def add_trigger(self, trigger: Trigger):
        """Thêm custom trigger"""
        self.custom_triggers.append(trigger)
    
    def remove_trigger(self, name: str) -> bool:
        """Remove custom trigger by name"""
        for i, t in enumerate(self.custom_triggers):
            if t.name == name:
                self.custom_triggers.pop(i)
                return True
        return False
    
    def check_triggers(self, data: Dict) -> List[Dict]:
        """
        Kiểm tra tất cả triggers và trả về các suggestions
        
        Args:
            data: Dictionary chứa 'projects', 'notices', 'etc'
            
        Returns:
            List of trigger results
        """
        results = []
        
        # Check projects
        projects = data.get("projects", [])
        for project in projects:
            for trigger in self.all_triggers:
                try:
                    if trigger.condition(project):
                        message = self._format_message(trigger.message_template, project)
                        results.append({
                            "trigger": trigger.name,
                            "action": trigger.action,
                            "message": message,
                            "priority": trigger.priority,
                            "data": project
                        })
                except Exception:
                    pass  # Skip if condition check fails
        
        # Check notices
        notices = data.get("notices", [])
        for notice in notices:
            for trigger in self.all_triggers:
                try:
                    if trigger.condition(notice):
                        message = self._format_message(trigger.message_template, notice)
                        results.append({
                            "trigger": trigger.name,
                            "action": trigger.action,
                            "message": message,
                            "priority": trigger.priority,
                            "data": notice
                        })
                except Exception:
                    pass
        
        # Sort by priority (highest first)
        results.sort(key=lambda x: x.get("priority", 0), reverse=True)
        
        # Cache results
        self._cached_results = results
        self._last_check_time = datetime.now()
        
        return results
    
    def get_suggestions(self, data: Dict, max_results: int = 3) -> List[str]:
        """
        Lấy danh sách suggestions dạng text
        
        Args:
            data: Data để check
            max_results: Số lượng suggestions tối đa
            
        Returns:
            List of suggestion messages
        """
        results = self.check_triggers(data)
        return [r["message"] for r in results[:max_results]]
    
    def should_auto_trigger(self, intent: str) -> bool:
        """
        Kiểm tra xem intent có nên auto-trigger không
        
        Args:
            intent: Intent name
            
        Returns:
            True nếu nên auto-trigger
        """
        # Auto-trigger for these intents
        auto_trigger_intents = [
            "project_query",
            "customer_query", 
            "pending_tasks",
            "system_state_query"
        ]
        return intent in auto_trigger_intents
    
    def _format_message(self, template: str, data: Dict) -> str:
        """Format message template với data"""
        message = template
        
        # Replace placeholders
        placeholders = {
            "project_name": data.get("Project Name", data.get("project_name", "Unknown")),
            "tracking_id": data.get("Tracking ID", data.get("tracking_id", "")),
            "customer": data.get("Customer", data.get("customer", "")),
            "status": data.get("Status", data.get("status", "")),
            "urgency": data.get("Urgency", data.get("urgency", "")),
            "days": data.get("days_pending", ""),
            "count": data.get("count", "")
        }
        
        for key, value in placeholders.items():
            placeholder = f"{{{key}}}"
            message = message.replace(placeholder, str(value))
        
        return message
    
    def get_trigger_actions(self, results: List[Dict]) -> List[Dict]:
        """Get action handlers cho trigger results"""
        actions = []
        
        action_handlers = {
            "suggest_check_project": {
                "label": "Kiểm tra tiến độ",
                "api": "get_project_status",
                "param_field": "tracking_id"
            },
            "suggest_assign_engineer": {
                "label": "Assign Engineer",
                "api": "assign_engineer",
                "param_field": "tracking_id"
            },
            "alert_urgent": {
                "label": "Xem chi tiết",
                "api": "get_notice_details",
                "param_field": "tracking_id"
            },
            "alert_overdue": {
                "label": "Xử lý ngay",
                "api": "get_notice_details",
                "param_field": "tracking_id"
            },
            "show_pending_notices": {
                "label": "Xem danh sách",
                "api": "get_pending_notices",
                "param_field": None
            }
        }
        
        for result in results:
            action_name = result.get("action")
            if action_name in action_handlers:
                handler = action_handlers[action_name]
                params = {}
                
                if handler["param_field"]:
                    data = result.get("data", {})
                    if handler["param_field"] in data:
                        params["tracking_id"] = data[handler["param_field"]]
                
                actions.append({
                    "trigger": result.get("trigger"),
                    "label": handler["label"],
                    "api": handler["api"],
                    "params": params
                })
        
        return actions


# ============================================
# CONVENIENCE FUNCTIONS
# ============================================

# Singleton instance
_trigger_manager = None

def get_trigger_manager() -> TriggerManager:
    """Get singleton TriggerManager instance"""
    global _trigger_manager
    if _trigger_manager is None:
        _trigger_manager = TriggerManager()
    return _trigger_manager


def check_project_triggers(projects: List[Dict]) -> List[Dict]:
    """Check triggers for projects"""
    manager = get_trigger_manager()
    return manager.check_triggers({"projects": projects})


def check_notice_triggers(notices: List[Dict]) -> List[Dict]:
    """Check triggers for notices"""
    manager = get_trigger_manager()
    return manager.check_triggers({"notices": notices})


def get_suggestions_for_user(user_id: int, limit: int = 3) -> List[str]:
    """Get suggestions cho user (convenience function)"""
    from src import db_helper
    
    manager = get_trigger_manager()
    
    # Get user data
    projects = db_helper.get_projects_by_user(user_id)
    notices = db_helper.get_pending_notices(user_id)
    
    return manager.get_suggestions({
        "projects": projects,
        "notices": notices
    }, limit)


# ============================================
# TEST
# ============================================

def test_triggers():
    """Test trigger system"""
    test_projects = [
        {
            "Tracking ID": 1,
            "Project Name": "Băng tải ABC",
            "Status": "Pending",
            "Engineer": "",
            "Urgency": "Normal",
            "Created Date": "20/03/2026"
        },
        {
            "Tracking ID": 2,
            "Project Name": "Băng tải XYZ",
            "Status": "In Progress",
            "Engineer": "Nguyễn Văn A",
            "Urgency": "Urgent",
            "Created Date": "25/03/2026"
        },
        {
            "Tracking ID": 3,
            "Project Name": "Hệ thống Nhật Bản",
            "Status": "In Progress",
            "Engineer": "Trần Văn B",
            "Urgency": "Very Urgent",
            "Created Date": "15/03/2026"
        }
    ]
    
    manager = TriggerManager()
    
    print("=== Trigger System Test ===")
    results = manager.check_triggers({"projects": test_projects})
    
    print(f"\nFound {len(results)} triggers:")
    for r in results:
        print(f"  [{r['priority']}] {r['message']}")
    
    print("\n=== Suggestions ===")
    suggestions = manager.get_suggestions({"projects": test_projects}, max_results=3)
    for s in suggestions:
        print(f"  • {s}")


# Export
__all__ = [
    "Trigger",
    "TriggerManager",
    "get_trigger_manager",
    "check_project_triggers",
    "check_notice_triggers",
    "get_suggestions_for_user",
    "test_triggers"
]