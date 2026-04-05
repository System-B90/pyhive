## PyHive — Hive API client for Python

PyHive (package: `PyHiveLMS`) is a lightweight synchronous Python client for the Hive LMS API.

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
<!-- SUPPORTED_API_VERSIONS_END -->

## Install

Install from PyPI in a virtual environment:

```pwsh
pip install PyHiveLMS
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

Public model classes are available from `pyhive.types` for type-safe code and editor completion.

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
    subject = client.get_subjects(parent_program__id__in=[123])[0]
    new_module = subject.create_module(
        name="Limits and Continuity",
        order=10,
        segel_brief="Introduction to limits.",
    )
    print(new_module.id, new_module.name)
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

PyHive includes a small CLI exposed as the `pyhive` console script.

- `pyhive versions` / `pyhive versions2`: display supported Hive API versions.

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
