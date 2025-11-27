"""
Templates de correos electrónicos para HPS System
Sistema modular de templates por archivo
"""

from .reminder import ReminderTemplate
from .new_user_notification import NewUserNotificationTemplate
from .hps_form import HPSFormTemplate
from .user_credentials import UserCredentialsTemplate
from .hps_approved import HPSApprovedTemplate
from .hps_rejected import HPSRejectedTemplate

__all__ = [
    'ReminderTemplate',
    'NewUserNotificationTemplate',
    'HPSFormTemplate',
    'UserCredentialsTemplate',
    'HPSApprovedTemplate',
    'HPSRejectedTemplate'
]
