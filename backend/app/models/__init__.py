from app.db.base import Base
from app.models.organization import Organization
from app.models.user import User
from app.models.role import Role, Permission, role_permissions
from app.models.audit import AuditLog

# Phase 2 Core Models
from app.models.customer import Customer, Contact
from app.models.product import Product
from app.models.pipeline import Pipeline, PipelineStage
from app.models.project import Project, ProjectStageHistory
from app.models.follow_up import FollowUp
from app.models.payment import Payment
from app.models.note import Note
from app.models.document import DocumentMetadata
# Phase 3 Platform Configurability & Automation Models
from app.models.custom_field import CustomField, CustomFieldValue
from app.models.saved_view import SavedView
from app.models.workflow import WorkflowDefinition, WorkflowExecution
from app.models.notification import Notification
from app.models.approval import ApprovalRequest, ApprovalDecision
# Phase 4 Production Hardening Models
from app.models.job import Job

__all__ = [
    "Base",
    "Organization",
    "User",
    "Role",
    "Permission",
    "role_permissions",
    "AuditLog",
    # Phase 2
    "Customer",
    "Contact",
    "Product",
    "Pipeline",
    "PipelineStage",
    "Project",
    "ProjectStageHistory",
    "FollowUp",
    "Payment",
    "Note",
    "DocumentMetadata",
    "Activity",
    # Phase 3
    "CustomField",
    "CustomFieldValue",
    "SavedView",
    "WorkflowDefinition",
    "WorkflowExecution",
    "Notification",
    "ApprovalRequest",
    "ApprovalDecision",
    # Phase 4
    "Job",
]
