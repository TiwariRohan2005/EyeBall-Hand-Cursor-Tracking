from enum import Enum
import logging

logger = logging.getLogger(__name__)

class Permission(Enum):
    BOOK_VIEW = "BOOK_VIEW"
    BOOK_SEARCH = "BOOK_SEARCH"
    BOOK_ADD = "BOOK_ADD"
    BOOK_EDIT = "BOOK_EDIT"
    BOOK_DELETE = "BOOK_DELETE"
    
    BOOK_ISSUE = "BOOK_ISSUE"
    BOOK_RETURN = "BOOK_RETURN"
    
    EXPORT_FULL_REPORT = "EXPORT_FULL_REPORT"
    EXPORT_OWN_REPORT = "EXPORT_OWN_REPORT"
    VIEW_ALL_ANALYTICS = "VIEW_ALL_ANALYTICS"
    
    VIEW_OWN_TRANSACTIONS = "VIEW_OWN_TRANSACTIONS"
    VIEW_ALL_TRANSACTIONS = "VIEW_ALL_TRANSACTIONS"
    
    MANAGE_STAFF = "MANAGE_STAFF"
    SYSTEM_SETTINGS = "SYSTEM_SETTINGS"

class PermissionManager:
    """
    Centralized Permission Manager mapping application Roles to specific internal privileges.
    """
    # Owner has everything
    # Staff has a restricted set
    ROLE_PERMISSIONS = {
        "OWNER": set(Permission),
        "STAFF": {
            Permission.BOOK_VIEW,
            Permission.BOOK_SEARCH,
            Permission.BOOK_ISSUE,
            Permission.BOOK_RETURN,
            Permission.VIEW_OWN_TRANSACTIONS,
            Permission.EXPORT_OWN_REPORT
        }
    }
    
    @classmethod
    def has_permission(cls, role: str, permission: Permission) -> bool:
        if not role:
            return False
        role = role.upper()
        if role not in cls.ROLE_PERMISSIONS:
            return False
        return permission in cls.ROLE_PERMISSIONS[role]
        
    @classmethod
    def require_permission(cls, role: str, permission: Permission):
        if not cls.has_permission(role, permission):
            logger.warning(f"ACCESS_DENIED: Role '{role}' attempted protected action '{permission.value}'")
            raise PermissionError(f"Access Denied: You do not have permission for {permission.value}")
