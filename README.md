## PyHive — a minimal Hive API client for Python

PyHive (package: `PyHiveLMS`) is a small, synchronous Python client for the Hive API. It provides:

- A simple `HiveClient` you use as a context manager to handle authentication and the HTTP session.
- Generator-based list endpoints for memory-efficient iteration of large result sets.

### Supported Hive Versions
<!-- SUPPORTED_API_VERSIONS_START -->
- `5.1.2`
- `6.2.0`
- `6.4.0`
<!-- SUPPORTED_API_VERSIONS_END -->

## Install

Install from PyPI. It's recommended to use a virtual environment.

Using pip (PyPI):

```pwsh
pip install PyHiveLMS
```


## Quickstart — working with convenience helpers

The primary entry point is `HiveClient`. You can authenticate either via Hive SSO (recommended, no password in your code) or directly with a username and password.

### Log in via Hive SSO (no password in code)

`HiveClient.from_sso(...)` performs a browser-based login flow against the Hive SSO server. It will:

- Print a URL to your terminal (and try to open it in your default browser) that takes you to the Hive SSO login page.
- Start a small local HTTP server on `http://127.0.0.1:8765/sso/callback` to receive the OAuth redirect.
- Exchange the authorization code for tokens and extract the Hive `api_token`.
- Construct an authenticated `HiveClient` that uses this token under the hood.

Before using SSO, configure your Hive SSO client with:

- **Redirect URI**: `http://127.0.0.1:8765/sso/callback`
- **Environment variables**:
  - `HIVE_CLIENT_ID`
  - `HIVE_CLIENT_SECRET` (if your SSO client is configured as a confidential client)

Then create the client like this:

```python
from pyhive import HiveClient

HIVE_URL = "https://hive.org"

with HiveClient.from_sso(hive_url=HIVE_URL, verify=False) as client:
    programs = list(client.get_programs())
    print(programs)
```

### Log in with username/password

You can also authenticate directly with your Hive username and password if you prefer:

### Create modules from a `Subject`

`Subject` instances know how to create their own modules via `subject.create_module(...)`:

```python
from pyhive import HiveClient

USERNAME = "Mentor123"
PASSWORD = "Password1"
HIVE_URL = "https://hive.org"
PROGRAM_ID = 123  # replace with your program id
USER_ID = 456  # replace with your user id

with HiveClient(USERNAME, PASSWORD, HIVE_URL) as client:
	# Fetch a subject (for example by program ID)
	subject = client.get_subjects(parent_program__id__in=[PROGRAM_ID])[0]
	print("Subject:", subject.name)

	# Create a module directly from the subject
	new_module = subject.create_module(
		name="Limits and Continuity",
		order=10,
		segel_brief="Introduction to limits.",
	)
	print("Created module:", new_module.id, new_module.name)
```

### Iterate over related objects

Many models are iterable so you can work with related data without calling the client manually:

- `Subject`: iterates over its `Module` objects (internally using `subject.get_modules()`).
- `Assignment`: iterates over its responses (internally using `assignment.get_responses()`).

```python
from pyhive import HiveClient

with HiveClient(USERNAME, PASSWORD, HIVE_URL) as client:
	# Iterate modules via the Subject iterator
	subject = client.get_subjects(parent_program__id__in=[PROGRAM_ID])[0]
	for module in subject:
		print("Module:", module.id, module.name)

	# Iterate responses via the Assignment iterator
	assignments = client.get_assignments(user__id__in=[USER_ID])
	for assignment in assignments:
		print("Assignment:", assignment.id)
		for response in assignment:
			print("  Response:", response.id, response.submitted_by)
```

You can always call the underlying convenience methods directly if you prefer:

```python
with HiveClient(USERNAME, PASSWORD, HIVE_URL) as client:
	subject = client.get_subjects(parent_program__id__in=[PROGRAM_ID])[0]
	modules = list(subject.get_modules())

	assignment = client.get_assignments(user__id__in=[USER_ID])[0]
	responses = list(assignment.get_responses())
```

## Filtering and convenience

- List endpoints (`get_programs`, `get_subjects`, `get_modules`, `get_exercises`, `get_assignments`, `get_users`, etc.) accept filter keyword arguments that are forwarded to the API. Use `id__in`, `parent_program__id__in`, `queue__id`, and the other documented kwargs to restrict results.
- Many methods accept either an integer id or a model instance. For example `client.get_exercise_fields(exercise_id_or_model)` accepts either.
- Model types such as `Subject` and `Assignment` expose convenience helpers and iterators (e.g. `subject.create_module(...)`, `subject.get_modules()`, `for module in subject`, `assignment.get_responses()`, `for response in assignment`) so you can stay close to the domain objects and reduce boilerplate.

### Using type hints with `pyhive.types`

You can import the public model types from `pyhive.types` to add precise type hints to your code:

```python
from collections.abc import Iterable

from pyhive import HiveClient
from pyhive.types import Program, Subject, User


def list_program_subjects(client: HiveClient, program: Program) -> Iterable[Subject]:
	subjects = client.get_subjects(parent_program=program)
	for subject in subjects:
		print(subject.id, subject.name)
	return subjects


def find_student(client: HiveClient, username: str) -> User | None:
	return client.get_user_by_name(username)
```

### Using native objects as filters

You can often pass full model instances into list helpers instead of bare ids. This makes filtering more expressive and avoids unpacking attributes by hand.

Example — get students in a program:

```python
from pyhive import HiveClient

with HiveClient(USERNAME, PASSWORD, HIVE_URL) as client:
	program = client.get_program(PROGRAM_ID)

	# Using the program object directly as a filter
	students = client.get_users(parent_program=program)
	for student in students:
		print(student.id, student.first_name, student.last_name)
```

Example — get subjects for a program and assignments for a user:

```python
with HiveClient(USERNAME, PASSWORD, HIVE_URL) as client:
	program = client.get_program(PROGRAM_ID)
	user = client.get_user_by_name(USERNAME)

	# Filter subjects using the program object
	for subject in client.get_subjects(parent_program=program):
		print("Subject:", subject.id, subject.name)

	# Filter assignments using the user object
	for assignment in client.get_assignments(user=user):
		print("Assignment:", assignment.id, assignment.assignment_status)
```

## Error handling

Network and HTTP errors are surfaced from the underlying `httpx` client. Typical patterns:

```python
from httpx import HTTPError

try:
	with HiveClient(USERNAME, PASSWORD, HIVE_URL) as client:
		programs = list(client.get_programs())
except HTTPError as exc:
	print("Network/HTTP error:", exc)
```

Model parsing errors will raise normal Python exceptions — wrap calls where you need robust failure handling.

## Common methods (short reference)

- HiveClient(username, password, hive_url, **kwargs) — construct and authenticate client
- get_programs(...)
- get_program(program_id)
- get_subjects(...)
- get_modules(...)
- get_exercises(...)
- get_exercise(exercise_id)
- get_exercise_fields(exercise)
- get_assignments(...)
- get_assignment(assignment_id)
- get_assignment_responses(assignment)
- get_users(...)
- get_classes(...)

Return values are typed model objects from `src/types` or generators of those objects.

## CLI

PyHive ships with a small Typer-based CLI, exposed as the `pyhive` console script.

- `pyhive versions` / `pyhive versions2`: print the Hive API versions supported by this build (same list as shown in the "Supported Hive Versions" section above).

## Try it locally / Run tests

Install dev dependencies and run tests with pytest:

```pwsh
pip install -e .
pytest -q
```

## Troubleshooting

- Authentication errors: verify username/password and the `hive_url` base. The client authenticates at construction.
- SSL verification: pass `verify=False` to the client constructor for self-signed servers (not recommended for production).

## Contributing & development

- Tests live under `tests/` and show common usage patterns. Use them as examples.
- The typed models are in `src/types` and the `HiveClient` convenience layer is in `pyhive/client.py`.

If you plan to make changes, please add tests for new behavior and keep changes small and focused.
