## PyHive — Hive API client for Python

PyHive (package: `PyHiveLMS`) is a lightweight synchronous Python client for the Hive LMS API, featuring Pydantic V2-based models for type safety and validation.

It provides:

- A simple `HiveClient` that manages authentication and the session lifecycle.
- Built-in support for Hive SSO and username/password authentication.
- Generator-based list endpoints for efficient paging and iteration.
- Model convenience helpers for working with programs, subjects, modules, exercises, assignments, queues, and users.
- Filter-friendly APIs that accept both IDs and model instances.

### Supported Hive Versions
<!-- SUPPORTED_API_VERSIONS_START -->
- `5.1.2`
- `6.2.0`
- `6.4.0`
- `7.1.0`
<!-- SUPPORTED_API_VERSIONS_END -->

## Install

Install a tagged release from the org's private pip index (needs a GitHub PAT with `repo` scope):

```pwsh
pip install PyHiveLMS --index-url https://<user>:<PAT>@raw.githubusercontent.com/System-B90/.github/main/pypi/
```

Or install an unreleased ref directly from GitHub:

```pwsh
pip install git+https://github.com/System-B90/pyhive.git
```

## Quickstart

The main entry point is `HiveClient`. Use it as a context manager to keep authentication and HTTP resources scoped cleanly.

### SSO login (recommended)

Use `HiveClient.from_sso(...)` to authenticate via Hive SSO. This workflow opens a browser-based login page and completes authentication automatically.

```python
from pyhive import HiveClient

with HiveClient.from_sso(hive_url="https://hive.org", verify=False) as client:
    programs = list(client.get_programs())
    print(programs)
```

### Username/password login

Authenticate directly with Hive credentials when SSO is not desirable.

```python
from pyhive import HiveClient

with HiveClient("username", "password", "https://hive.org") as client:
    subjects = list(client.get_subjects())
    print(subjects)
```

## Core features

### Iterable model helpers

Models expose convenience methods and iterators so you can fetch related objects naturally.

- `Subject` supports `subject.get_modules()` and can be iterated to yield its modules.
- `Assignment` supports `assignment.get_responses()` and can be iterated to yield its responses.

### Filter-friendly list APIs

List endpoints accept filter keyword arguments that are forwarded to Hive.

```python
subjects = client.get_subjects(parent_program__id__in=[123])
assignments = client.get_assignments(user__id__in=[456])
```

Many methods also accept either an ID or a model instance.

```python
exercise_fields = client.get_exercise_fields(exercise)
```

### Type hints

Public model classes are available from `pyhive.types` for type-safe code and editor completion. All models are Pydantic V2 BaseModel subclasses with automatic validation and serialization.

```python
from pyhive import HiveClient
from pyhive.types import Program, Subject, User

with HiveClient("username", "password", "https://hive.org") as client:
    program = client.get_program(123)
    subjects = client.get_subjects(parent_program=program)
    for subject in subjects:
        print(subject.id, subject.name)
```

### Convenience helpers

Call methods directly on models for common domain operations.

```python
with HiveClient("username", "password", "https://hive.org") as client:
    # Create a new module in a subject
    subject = client.get_subjects(parent_program__id__in=[123])[0]
    new_module = subject.create_module(
        name="Limits and Continuity",
        order=10,
        segel_brief="Introduction to limits.",
    )
    print(new_module.id, new_module.name)
    
    # Create a new exercise in a module
    new_exercise = new_module.create_exercise(
        name="Derivative Rules",
        order=1,
        description="Practice basic derivative rules.",
    )
    print(new_exercise.id, new_exercise.name)
    
    # Create a new user
    new_user = client.create_user(
        username="student123",
        email="student@example.com",
        first_name="John",
        last_name="Doe",
    )
    print(new_user.id, new_user.username)
```

## Common methods

- `HiveClient(username, password, hive_url, **kwargs)`
- `HiveClient.from_sso(hive_url, **kwargs)`
- `get_programs(...)`
- `get_program(program_id)`
- `get_subjects(...)`
- `get_modules(...)`
- `get_exercises(...)`
- `get_exercise(exercise_id)`
- `get_exercise_fields(exercise)`
- `get_assignments(...)`
- `get_assignment(assignment_id)`
- `get_assignment_responses(assignment)`
- `get_users(...)`
- `get_classes(...)`

Return values are typed model objects or generators of model objects.

## CLI

PyHive includes a CLI exposed as the `pyhive` console script with the following commands:

- `pyhive versions`: Display supported Hive API versions.
- `pyhive token`: Authenticate via SSO and output a valid access token.
- `pyhive register <service_name> <redirect_uri>`: Register a new service with the Hive server and generate client keys.

## Testing

Run the package tests with pytest:

```pwsh
pip install -e .
pytest -q
```

## Notes

- Network and HTTP errors are surfaced through the underlying HTTP client.
- Pass `verify=False` only when necessary for self-signed or development servers.
- The package is intended for synchronous Hive API usage with a minimal convenience layer.
