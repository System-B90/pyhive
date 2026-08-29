"""Type definitions for PyHive."""

from __future__ import annotations

from pyhive.src.types.assignment import Assignment
from pyhive.src.types.assignment_notification import AssignmentNotification
from pyhive.src.types.assignment_response import AssignmentResponse
from pyhive.src.types.assignment_response_content import AssignmentResponseContent
from pyhive.src.types.autocheck_status import AutoCheckStatus
from pyhive.src.types.class_ import Class
from pyhive.src.types.client_info import ClientInfo
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
from pyhive.src.types.event_attendee import EventAttendee
from pyhive.src.types.event_attendees_type_0_item import EventAttendeesType0Item
from pyhive.src.types.event_category import EventCategory
from pyhive.src.types.event_color import EventColor
from pyhive.src.types.event_instructor import EventInstructor
from pyhive.src.types.event_tag import EventTag
from pyhive.src.types.event_tagging import EventTagging
from pyhive.src.types.exercise import Exercise
from pyhive.src.types.form_field import FormField
from pyhive.src.types.help_ import Help
from pyhive.src.types.help_notification import HelpNotification
from pyhive.src.types.help_response import HelpResponse
from pyhive.src.types.help_response_segel_nested import HelpResponseSegelNested
from pyhive.src.types.lesson import Lesson
from pyhive.src.types.lesson_rule import LessonRule
from pyhive.src.types.me import Me
from pyhive.src.types.module import Module
from pyhive.src.types.notification import Notification
from pyhive.src.types.notification_nested import NotificationNested
from pyhive.src.types.powersync_token import PowerSyncToken
from pyhive.src.types.program import Program
from pyhive.src.types.queue import Queue
from pyhive.src.types.queue_item import QueueItem
from pyhive.src.types.schedule_event import ScheduleEvent
from pyhive.src.types.seating import Seating
from pyhive.src.types.sso_application import SsoApplication
from pyhive.src.types.subject import Subject
from pyhive.src.types.tag import Tag
from pyhive.src.types.top_help_response_checker import TopHelpResponseChecker
from pyhive.src.types.user import User

__all__ = [
    "ActionEnum",
    "Assignment",
    "AssignmentNotification",
    "AssignmentResponse",
    "AssignmentResponseContent",
    "AssignmentResponseTypeEnum",
    "AssignmentStatusEnum",
    "AutoCheckStatus",
    "Class",
    "ClassTypeEnum",
    "ClearanceEnum",
    "ClientInfo",
    "Event",
    "EventAttendee",
    "EventAttendeesType0Item",
    "EventCategory",
    "EventColor",
    "EventInstructor",
    "EventTag",
    "EventTagging",
    "EventTypeEnum",
    "Exercise",
    "ExercisePreviewTypes",
    "FormField",
    "FormFieldTypeEnum",
    "GenderEnum",
    "Help",
    "HelpNotification",
    "HelpResponse",
    "HelpResponseSegelNested",
    "HelpResponseTypeEnum",
    "HelpStatusEnum",
    "HelpTypeEnum",
    "Lesson",
    "LessonRule",
    "Me",
    "Module",
    "Notification",
    "NotificationNested",
    "PatbasEnum",
    "PowerSyncToken",
    "Program",
    "Queue",
    "QueueItem",
    "QueueRuleEnum",
    "ScheduleEvent",
    "Seating",
    "SsoApplication",
    "StatusEnum",
    "Subject",
    "SyncStatusEnum",
    "Tag",
    "TopHelpResponseChecker",
    "User",
    "VisibilityEnum",
]
