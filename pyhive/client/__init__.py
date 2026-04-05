from .client import HiveClient  # re-export

# Rebuild Pydantic models to resolve forward references
from ..src.types.assignment import Assignment
from ..src.types.assignment_response import AssignmentResponse
from ..src.types.assignment_response_content import AssignmentResponseContent
from ..src.types.autocheck_status import AutoCheckStatus
from ..src.types.class_ import Class
from ..src.types.event import Event
from ..src.types.event_attendees_type_0_item import EventAttendeesType0Item
from ..src.types.event_color import EventColor
from ..src.types.exercise import Exercise
from ..src.types.form_field import FormField
from ..src.types.help_ import Help
from ..src.types.help_response import HelpResponse
from ..src.types.help_response_segel_nested import HelpResponseSegelNested
from ..src.types.module import Module
from ..src.types.notification_nested import NotificationNested
from ..src.types.program import Program
from ..src.types.queue import Queue
from ..src.types.queue_item import QueueItem
from ..src.types.subject import Subject
from ..src.types.tag import Tag
from ..src.types.user import User

Assignment.model_rebuild()
AssignmentResponse.model_rebuild()
AssignmentResponseContent.model_rebuild()
AutoCheckStatus.model_rebuild()
Class.model_rebuild()
Event.model_rebuild()
EventAttendeesType0Item.model_rebuild()
EventColor.model_rebuild()
Exercise.model_rebuild()
FormField.model_rebuild()
Help.model_rebuild()
HelpResponse.model_rebuild()
HelpResponseSegelNested.model_rebuild()
Module.model_rebuild()
NotificationNested.model_rebuild()
Program.model_rebuild()
Queue.model_rebuild()
QueueItem.model_rebuild()
Subject.model_rebuild()
Tag.model_rebuild()
User.model_rebuild()

__all__ = ["HiveClient"]
