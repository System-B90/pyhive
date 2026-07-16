import random
import uuid

import pytest

from pyhive import HiveClient
from pyhive.types import (
    ClearanceEnum,
    GenderEnum,
    Module,
    Program,
    Subject,
    User,
)
from tests.common import (
    get_client_params,
    random_letter,
    random_string,
    random_user_data,
)


@pytest.fixture(scope="session")
def client():
    with HiveClient(**get_client_params()) as c:
        yield c


@pytest.fixture
def mentor(client: HiveClient):
    name_suffix = uuid.uuid4().hex[:8]
    mentor = client.create_user(
        f"TestMentor-{name_suffix}",
        "Password1",
        clearance=ClearanceEnum.SEGEL,
        gender=GenderEnum.NONBINARY,
    )
    yield mentor
    try:
        mentor.delete()
    except Exception:
        pass


@pytest.fixture
def checker(client: HiveClient):
    name_suffix = uuid.uuid4().hex[:8]
    checker = client.create_user(
        f"TestChecker-{name_suffix}",
        "Password1",
        clearance=ClearanceEnum.CHECKER,
        gender=GenderEnum.NONBINARY,
    )
    yield checker
    try:
        checker.delete()
    except Exception:
        pass


@pytest.fixture
def program(client: HiveClient, checker: User):
    name_suffix = uuid.uuid4().hex[:8]
    program = client.create_program(name=f"TestProgram{name_suffix}", checker=checker)
    yield program
    try:
        program.delete()
    except Exception:
        pass


@pytest.fixture
def student(client: HiveClient, program: Program, mentor: User):
    name_suffix = uuid.uuid4().hex[:8]
    student = client.create_student(
        f"TestStudent-{name_suffix}",
        "Password1",
        gender=GenderEnum.NONBINARY,
        program=program,
        mentor=mentor,
        number=random.randint(500, 9999),
    )
    yield student
    try:
        student.delete()
    except Exception:
        pass


@pytest.fixture
def subject(client: HiveClient, program: Program):
    name_suffix = uuid.uuid4().hex[:8]
    symbol = random_letter()
    subject = client.create_subject(
        name=f"TestSubject{name_suffix}",
        symbol=symbol,
        color="#ffffff",
        program=program,
    )
    yield subject
    try:
        subject.delete()
    except Exception:
        pass


@pytest.fixture
def module(client: HiveClient, subject: Subject):
    name_suffix = uuid.uuid4().hex[:8]
    module = client.create_module(
        name=f"TestModule{name_suffix}",
        order=9,
        parent_subject=subject,
    )
    yield module
    try:
        module.delete()
    except Exception:
        pass


@pytest.fixture
def exercise(client: HiveClient, module: Module):
    name_suffix = uuid.uuid4().hex[:8]
    exercise = client.create_exercise(
        name=f"TestExercise{name_suffix}",
        order=123,
        parent_module=module,
    )
    yield exercise
    try:
        exercise.delete()
    except Exception:
        pass


@pytest.fixture(scope="session")
def large_program(client: HiveClient):
    """
    Create a large program with multiple users and subjects for integration testing.
    Reuses existing client.create_* and program.create_* methods
    instead of duplicating logic.
    """

    checker_name_suffix = uuid.uuid4().hex[:8]
    checker = client.create_user(
        f"LargeProgramChecker-{checker_name_suffix}",
        "Password1",
        clearance=ClearanceEnum.CHECKER,
        gender=GenderEnum.NONBINARY,
    )

    name_suffix = uuid.uuid4().hex[:8]
    program = client.create_program(
        name=f"TestLargeProgram{name_suffix}", checker=checker
    )

    created_users: list[User] = []
    created_subjects: list[Subject] = []
    mentors: list[User] = []

    try:
        # Create several mentors and checkers for the program
        for role, clearance in [
            ("Mentor", ClearanceEnum.SEGEL),
            ("Checker", ClearanceEnum.CHECKER),
        ]:
            for i in range(4):  # two of each type
                user = client.create_user(
                    username=f"Test{role}-{i}-{uuid.uuid4().hex[:6]}",
                    password="Password1",
                    clearance=clearance,
                    gender=GenderEnum.NONBINARY,
                    mentees=[],
                    first_name=random_string(),
                    last_name=random_string(),
                )
                created_users.append(user)
                if clearance == ClearanceEnum.SEGEL:
                    mentors.append(user)

        for student_info in [
            random_user_data(program=program, mentor=mentors[i % len(mentors)])
            for i in range(16)
        ]:
            student = client.create_student(**student_info)
            created_users.append(student)

        # Create multiple subjects under this program
        for _ in range(5):
            symbol = random_letter()
            subj = program.create_subject(
                name=f"LargeSubj{uuid.uuid4().hex[:6]}",
                symbol=symbol,
                color="#abcdef",
            )
            created_subjects.append(subj)

            # Each subject gets a few modules and exercises
            for module_order in range(8):
                module = subj.create_module(
                    name=f"LargeModule{module_order}{uuid.uuid4().hex[:4]}",
                    order=module_order + 1,
                )

                # Simple example: add two exercises per module
                for ex_order in range(2):
                    module.create_exercise(
                        name=f"LargeEx{ex_order}{uuid.uuid4().hex[:4]}",
                        order=ex_order + 1,
                    )

        yield program

    finally:
        # Cleanup phase (only if necessary)
        for subj in created_subjects:
            try:
                subj.delete()
            except Exception:
                pass
        for user in created_users:
            try:
                user.delete()
            except Exception:
                pass
        try:
            program.delete()
        except Exception:
            pass

    try:
        checker.delete()
    except Exception:
        pass
