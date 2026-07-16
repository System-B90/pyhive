import random
import string
import uuid
from typing import Any, Optional

from pyhive.src.types.enums.exercise_patbas_enum import PatbasEnum
from pyhive.src.types.enums.exercise_preview_types import ExercisePreviewTypes
from pyhive.src.types.program import ProgramLike
from pyhive.src.types.queue import QueueLike
from pyhive.src.types.user import UserLike
from pyhive.types import GenderEnum, StatusEnum


def get_client_params() -> dict[str, Any]:
    return {
        "username": "admin",
        "password": "Password1",
        "hive_url": "https://hive.org",
        "verify": False,
        "timeout": 20,  # Very long timeout so tests do not fail just because the Hive endpoint is slow
        "skip_version_check": True,
    }


def random_letter() -> str:
    return chr(random.randint(ord("A"), ord("Z")))


EXERCISE_DATA_LIST: list[dict[str, Any]] = [
    {
        "name": "Introduction to Loops",
        "order": 1,
        "download": False,
        "preview": ExercisePreviewTypes.DISABLED,
        "patbas_preview": ExercisePreviewTypes.DISABLED,
        "style": "",
        "patbas_download": False,
        "patbas": PatbasEnum.NEVER,
        "on_creation_data": "intro_loops_v1",
        "autocheck_tag": "check_loops",
        "autodone": False,
        "expected_duration": "10:00",
        "segel_brief": "A gentle intro to loops in Python.",
        "is_lecture": True,
        "tags": ["A"],
    },
    {
        "name": "Conditional Statements",
        "order": 2,
        "download": True,
        "preview": ExercisePreviewTypes.PDF,
        "patbas_preview": ExercisePreviewTypes.DISABLED,
        "style": "modern",
        "patbas_download": False,
        "patbas": PatbasEnum.ON_DONE,
        "on_creation_data": "cond_v2",
        "autocheck_tag": "check_ifelse",
        "autodone": True,
        "expected_duration": "15:00",
        "segel_brief": "Exploring if-else statements.",
        "is_lecture": False,
    },
    {
        "name": "Working with Lists",
        "order": 3,
        "download": True,
        "preview": ExercisePreviewTypes.DISABLED,
        "patbas_preview": ExercisePreviewTypes.MARKDOWN,
        "style": "practice",
        "patbas_download": True,
        "patbas": PatbasEnum.ALWAYS,
        "on_creation_data": "lists_v1",
        "autocheck_tag": "check_lists",
        "autodone": False,
        "expected_duration": "20:00",
        "segel_brief": "Hands-on list manipulation exercises.",
        "is_lecture": False,
        "tags": ["B"],
    },
    {
        "name": "Functions and Scope",
        "order": 4,
        "download": False,
        "preview": ExercisePreviewTypes.MARKDOWN,
        "patbas_preview": ExercisePreviewTypes.MARKDOWN,
        "style": "clean",
        "patbas_download": False,
        "patbas": PatbasEnum.STAFF_ONLY,
        "on_creation_data": "func_scope",
        "autocheck_tag": "check_func",
        "autodone": True,
        "expected_duration": "25:15",
        "segel_brief": "Understanding local and global variables.",
        "is_lecture": True,
        "tags": ["C"],
    },
    {
        "name": "Final Project Setup",
        "order": 5,
        "download": True,
        "preview": ExercisePreviewTypes.DISABLED,
        "patbas_preview": ExercisePreviewTypes.DISABLED,
        "style": "project",
        "patbas_download": False,
        "patbas": PatbasEnum.ON_DONE,
        "on_creation_data": "final_proj_init",
        "autocheck_tag": "check_project",
        "autodone": False,
        "expected_duration": "45:45",
        "segel_brief": "Prepare the environment for your final project.",
        "is_lecture": False,
        "tags": ["A", "B", "C"],
    },
]


def random_string(prefix: str = "", length: int = 6) -> str:
    """
    Generate a random plausible string, optionally prefixed.
    Example: "User-ab12cd"
    """
    letters = string.ascii_lowercase + string.digits
    suffix = "".join(random.choices(letters, k=length))
    return f"{prefix}{suffix}"


def random_user_data(
    *,
    program: Optional["ProgramLike"] = None,
    mentor: Optional["UserLike"] = None,
    queue: Optional["QueueLike"] = None,
    user_queue: Optional["QueueLike"] = None,
    override_queue: Optional["QueueLike"] = None,
) -> dict[str, Any]:
    """
    Generate random user data roughly matching the create_user() signature.
    """
    genders = list(GenderEnum)
    statuses = list(StatusEnum)

    first_name = random.choice(
        [
            "Alex",
            "Jordan",
            "Taylor",
            "Sam",
            "Casey",
            "Riley",
            "Avery",
            "Kai",
            "Jamie",
            "Skyler",
            "Morgan",
            "Drew",
            "Charlie",
            "Rowan",
            "Sasha",
            "Emery",
            "Blake",
            "Quinn",
            "Harper",
            "Eden",
            "Aria",
            "Leo",
            "Maya",
            "Noah",
            "Zoe",
            "Luca",
            "Milo",
            "Nova",
            "Finn",
            "Isla",
            "Ezra",
            "Luna",
            "Theo",
            "Ivy",
            "Jasper",
            "Nora",
            "Kieran",
            "Ada",
            "Owen",
            "Freya",
        ]
    )

    last_name = random.choice(
        [
            "Smith",
            "Lee",
            "Patel",
            "Brown",
            "Garcia",
            "Khan",
            "Nguyen",
            "Rodriguez",
            "Kim",
            "Anderson",
            "Singh",
            "Lopez",
            "Chen",
            "Martinez",
            "Davis",
            "Hernandez",
            "Wong",
            "Miller",
            "Silva",
            "Baker",
            "Cohen",
            "Dubois",
            "Kowalski",
            "Ivanov",
            "Nakamura",
            "Hassan",
            "Johansson",
            "Santos",
            "Nowak",
            "Petrov",
            "Costa",
            "Murphy",
            "Rossi",
            "Larsen",
            "Schmidt",
            "O'Neill",
            "Yilmaz",
            "Novak",
            "Takahashi",
            "Fernandez",
        ]
    )
    username = f"{first_name.lower()}-{uuid.uuid4().hex[:6]}"
    password = "Password1"
    hostname = f"{random_string('host-', 5)}.local"

    return {
        "username": username,
        "password": password,
        "gender": random.choice(genders),
        "number": random.randint(1, 9999),
        "first_name": first_name,
        "last_name": last_name,
        "program": program,
        "hostname": hostname,
        "status": random.choice(statuses),
        "mentor": mentor,
        "classes": None,
        "avatar_filename": None,
        "checkers_brief": "",
        "queue": queue,
        "user_queue": user_queue,
        "disable_queue": random.choice([True, False, None]),
        "disable_user_queue": random.choice([True, False, None]),
        "override_queue": override_queue,
    }
