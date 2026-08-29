"""Hive API Client module."""

# Rebuild Pydantic models to resolve forward references
from ..src.types.assignment import Assignment
from ..src.types.assignment_notification import AssignmentNotification
from ..src.types.assignment_response import AssignmentResponse
from ..src.types.assignment_response_content import AssignmentResponseContent
from ..src.types.autocheck_status import AutoCheckStatus
from ..src.types.class_ import Class
from ..src.types.client_info import ClientInfo
from ..src.types.event import Event
from ..src.types.event_attendee import EventAttendee
from ..src.types.event_attendees_type_0_item import EventAttendeesType0Item
from ..src.types.event_category import EventCategory
from ..src.types.event_color import EventColor
from ..src.types.event_instructor import EventInstructor
from ..src.types.event_tag import EventTag
from ..src.types.event_tagging import EventTagging
from ..src.types.exercise import Exercise
from ..src.types.form_field import FormField
from ..src.types.help_ import Help
from ..src.types.help_notification import HelpNotification
from ..src.types.help_response import HelpResponse
from ..src.types.help_response_segel_nested import HelpResponseSegelNested
from ..src.types.lesson import Lesson
from ..src.types.lesson_rule import LessonRule
from ..src.types.me import Me
from ..src.types.module import Module
from ..src.types.notification import Notification
from ..src.types.notification_nested import NotificationNested
from ..src.types.powersync_token import PowerSyncToken
from ..src.types.program import Program
from ..src.types.queue import Queue
from ..src.types.queue_item import QueueItem
from ..src.types.schedule_event import ScheduleEvent
from ..src.types.seating import Seating
from ..src.types.sso_application import SsoApplication
from ..src.types.subject import Subject
from ..src.types.tag import Tag
from ..src.types.top_help_response_checker import TopHelpResponseChecker
from ..src.types.user import User
from .client import HiveClient  # re-export

Assignment.model_rebuild()
AssignmentNotification.model_rebuild()
AssignmentResponse.model_rebuild()
AssignmentResponseContent.model_rebuild()
AutoCheckStatus.model_rebuild()
Class.model_rebuild()
ClientInfo.model_rebuild()
Event.model_rebuild()
EventAttendee.model_rebuild()
EventAttendeesType0Item.model_rebuild()
EventCategory.model_rebuild()
EventColor.model_rebuild()
EventInstructor.model_rebuild()
EventTag.model_rebuild()
EventTagging.model_rebuild()
Exercise.model_rebuild()
FormField.model_rebuild()
Help.model_rebuild()
HelpNotification.model_rebuild()
HelpResponse.model_rebuild()
HelpResponseSegelNested.model_rebuild()
Lesson.model_rebuild()
LessonRule.model_rebuild()
Me.model_rebuild()
Module.model_rebuild()
Notification.model_rebuild()
NotificationNested.model_rebuild()
PowerSyncToken.model_rebuild()
Program.model_rebuild()
Queue.model_rebuild()
QueueItem.model_rebuild()
ScheduleEvent.model_rebuild()
Seating.model_rebuild()
SsoApplication.model_rebuild()
Subject.model_rebuild()
Tag.model_rebuild()
TopHelpResponseChecker.model_rebuild()
User.model_rebuild()

__all__ = ["HiveClient"]
