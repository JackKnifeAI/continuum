"""
CONTINUUM Compliance and Audit System

Enterprise-grade compliance for SOC2, GDPR, and HIPAA with complete audit trails.
"""

from .audit.logger import AuditLogger, AuditEventType
from .audit.events import AuditLogEntry, Actor, Resource, Action, Outcome
from .gdpr.data_subject import DataSubjectRights
from .gdpr.consent import ConsentManager
from .encryption.field_level import FieldLevelEncryption
from .access_control.rbac import RBACManager

__all__ = [
    "AuditLogger",
    "AuditEventType",
    "AuditLogEntry",
    "Actor",
    "Resource",
    "Action",
    "Outcome",
    "DataSubjectRights",
    "ConsentManager",
    "FieldLevelEncryption",
    "RBACManager",
]

__version__ = "1.0.0"
