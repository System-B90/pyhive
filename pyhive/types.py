"""Type definitions for PyHive."""

from __future__ import annotations

from pyhive.src.types.assignment import Assignment
from pyhive.src.types.assignment_response import AssignmentResponse
from pyhive.src.types.assignment_response_content import AssignmentResponseContent
from pyhive.src.types.autocheck_status import AutoCheckStatus
from pyhive.src.types.class_ import Class
from pyhive.src.types.enums.action_enum import ActionEnum
from pyhive.src.types.enums.assignment_response_type_enum import (
    AssignmentResponseTypeEnum,
)
from pyhive.src.types.enums.assignment_status_enum import AssignmentStatusEnum
from pyhive.src.types.enums.class_type_enum import ClassTypeEnum
from pyhive.src.types.enums.clearance_enum import ClearanceEnum
from pyhive.src.types.enums.event_type_enum import EventTypeEnum
from pyhive.src.types.enums.exercise_patbas_enum import PatbasEnum
from pyhive.src.types.enums.exercise_preview_types import ExercisePreviewTypes
from pyhive.src.types.enums.form_field_type_enum import FormFieldTypeEnum
from pyhive.src.types.enums.gender_enum import GenderEnum
from pyhive.src.types.enums.help_response_type_enum import HelpResponseTypeEnum
from pyhive.src.types.enums.help_status_enum import HelpStatusEnum
from pyhive.src.types.enums.help_type_enum import HelpTypeEnum
from pyhive.src.types.enums.queue_rule_enum import QueueRuleEnum
from pyhive.src.types.enums.status_enum import StatusEnum
from pyhive.src.types.enums.sync_status_enum import SyncStatusEnum
from pyhive.src.types.enums.visibility_enum import VisibilityEnum
from pyhive.src.types.event import Event
from pyhive.src.types.event_attendees_type_0_item import EventAttendeesType0Item
from pyhive.src.types.event_color import EventColor
from pyhive.src.types.exercise import Exercise
from pyhive.src.types.form_field import FormField
from pyhive.src.types.help_ import Help
from pyhive.src.types.help_response import HelpResponse
from pyhive.src.types.help_response_segel_nested import HelpResponseSegelNested
from pyhive.src.types.module import Module
from pyhive.src.types.notification_nested import NotificationNested
from pyhive.src.types.program import Program
from pyhive.src.types.queue import Queue
from pyhive.src.types.queue_item import QueueItem
from pyhive.src.types.subject import Subject
from pyhive.src.types.tag import Tag
from pyhive.src.types.user import User

__all__ = [
    "ActionEnum",
    "Assignment",
    "AssignmentResponse",
    "AssignmentResponseContent",
    "AssignmentResponseTypeEnum",
    "AssignmentStatusEnum",
    "AutoCheckStatus",
    "Class",
    "ClassTypeEnum",
    "ClearanceEnum",
    "Event",
    "EventAttendeesType0Item",
    "EventColor",
    "EventTypeEnum",
    "Exercise",
    "ExercisePreviewTypes",
    "FormField",
    "FormFieldTypeEnum",
    "GenderEnum",
    "Help",
    "HelpResponse",
    "HelpResponseSegelNested",
    "HelpResponseTypeEnum",
    "HelpStatusEnum",
    "HelpTypeEnum",
    "Module",
    "NotificationNested",
    "PatbasEnum",
    "Program",
    "Queue",
    "QueueItem",
    "QueueRuleEnum",
    "StatusEnum",
    "Subject",
    "SyncStatusEnum",
    "Tag",
    "User",
    "VisibilityEnum",
]
