# PyHive — Hive LMS API Client

Python SDK and CLI for the Hive Learning Management System API (package name: `PyHiveLMS`, import name: `pyhive`).

Org-wide conventions (repo list, Hive-org boundary, package scopes, git workflow, commit
format, CI secrets) live in
[System-B90/.github CLAUDE.md](https://github.com/System-B90/.github/blob/main/CLAUDE.md).
This file covers what's specific to pyhive.

## Git

Commit format: `Vibe-<PastTenseVerb> <description>` (e.g. `Vibe-Fixed`, `Vibe-Added`). No `feat:`/`fix:`/`chore:` prefixes. Never commit directly to `main`/`master` — feature branch + PR.

## Project layout

```
pyhive/
├── __init__.py                          # Public export: HiveClient
├── types.py                             # Public export: all Pydantic models + enums
├── client/
│   ├── client.py                        # HiveClient — mixin aggregator + auth factory methods
│   ├── client_shared.py                 # Base class inherited by every mixin
│   ├── <resource>.py                    # One mixin per resource domain (programs, subjects, …)
│   └── sso_utils.py                     # Browser-based OIDC/SSO helpers (Flask local server)
├── src/
│   ├── authenticated_hive_client.py     # AuthenticatedHiveClient — httpx wrapper, retry/refresh
│   ├── api_versions.py                  # MIN/LATEST/SUPPORTED_API_VERSIONS constants
│   ├── _generated_versions.py           # Auto-generated at build time — do not edit
│   └── types/                           # Pydantic V2 models (internal); enums in types/enums/
└── cli/
    ├── cli.py                           # Typer app + root commands (token, register, version, versions)
    ├── base.py                          # PyHiveTyper — injects --json + --cache-token everywhere
    ├── state.py                         # CLIState singleton (use_json, username, password, …)
    ├── client_factory.py                # get_hive_client() — credential priority chain
    ├── formatter.py                     # print_result / print_error_and_exit / print_formatted_list
    └── users.py                         # `pyhive users` subcommand group
tests/
    conftest.py                          # Integration test fixtures (create/teardown real resources)
    common.py                            # get_client_params(), random helpers, EXERCISE_DATA_LIST
```

## Architecture and key patterns

### HTTP layer

`AuthenticatedHiveClient` wraps `httpx.Client`. All requests go through `_get`, `_post`, `_patch`, `_put`, `_delete`, each decorated with `@_with_retries_and_token_refresh` which composes:
- `@_retry_on_bad_gateway` — exponential backoff on HTTP 502 (up to 5 attempts)
- `@_refresh_token_on_unauthorized` — single token refresh + retry on HTTP 401

Public methods (`get`, `post`, `put`, `delete`) parse JSON and return typed dicts/lists.

### Authentication strategies

`AuthenticatedHiveClient._auth_strategy` is one of:
- `"password"` — username/password login via `/api/core/token/`; supports refresh
- `"sso"` — SSO token with refresh token; supports refresh
- `"cache"` — cached token with refresh token; supports refresh
- `"token_only"` — bare API token with no refresh; raises `RuntimeError` on 401

### Credential priority in the CLI (`client_factory.py`)

`get_hive_client()` resolves in this order:
1. `--username` + `--password` (CLI flags) → `HiveClient(username, password, …)`
2. `--token` (CLI flag) → `HiveClient.from_api_token(…)`
3. `HIVE_ACCESS_TOKEN` env var → `HiveClient.from_api_token(…)`
4. OS keyring (`service=pyhive_cli`, `account=pyhive_access_token`) → `HiveClient.from_api_token(…)`
5. Fallback → `HiveClient.from_sso(…)` (opens browser for OIDC flow)

### Mixin inheritance

`HiveClient` inherits from a linear chain of `*ClientMixin` classes, each owning one resource domain. Every mixin inherits `ClientShared` (which provides the session). To add a new resource:
1. Create `pyhive/client/<resource>.py` with class `<Resource>ClientMixin(ClientShared)`.
2. Add it to `HiveClient`'s MRO in `pyhive/client/client.py`.
3. Export new Pydantic models from `pyhive/types.py`.

### Auto-generation from Hive's OpenAPI spec

PyHive's typed core is **auto-generated** from Hive's spec (`api/core.yaml`) by `tools/hive_codegen` (see `tools/hive_codegen/README.md`). The model layer is split:

- `pyhive/src/types/_generated/` — `enums.py`, `models.py`, `manifest.json`. **Regenerated every Hive release; never hand-edit.** Built with datamodel-code-generator, driven by `tools/hive_codegen/codegen.toml`.
- `pyhive/src/types/<resource>.py` — curated subclasses (`class Exercise(_ExerciseBase): ...`) that add `hive_client`, lazy relations, convenience methods and the occasional field override. New spec fields/enum values flow into the base and are inherited automatically.
- `pyhive/src/types/enums/<enum>.py` — thin re-exports of the generated enums (keeping historical import paths). `event_type_enum.py` is hand-written (dropped from the spec).

`.github/workflows/sync-hive.yml` regenerates on a `repository_dispatch` from Hive's release, opens a PR, and auto-merges when drift is purely additive (breaking changes are labelled `needs-manual-review`). Regenerate locally with `python -m hive_codegen sync --spec ../Hive/api/core.yaml --repo-root .`. When editing curated models, only add ergonomics/overrides — never re-declare a field already provided by the generated base unless intentionally overriding it.

### Generator-based list endpoints

All list methods return generators. Callers must `list(...)` or iterate explicitly. Never buffer entire results internally in the SDK.

### CLI global options (`PyHiveTyper`)

`PyHiveTyper` subclasses `typer.Typer` and injects `--json` and `--cache-token` into every command at decoration time via `_inject_global_options`. The injected options update `state` before the real command body executes. **Commands must not declare `use_json` or `cache_token` in their own signatures.**

### Version management

`[tool.api_versions].supported` in `pyproject.toml` is the source of truth. The hatchling build hook at `scripts/generate_versions.py` writes `pyhive/src/_generated_versions.py`. Never edit that file directly. `HiveClient._api_version_check()` validates the live server's version at construction time.

## Commands

### Build

```pwsh
pip install -e ".[dev]"   # editable install with dev extras
hatch build               # build wheel (triggers version generation hook)
```

### Test

```pwsh
pytest -q
```

Tests are **integration tests** against a live Hive server (`https://hive.org`). Credentials are hardcoded in `tests/common.py::get_client_params()`. There is no mock layer — tests create and tear down real resources via fixtures in `tests/conftest.py`.

### Lint / type-check

```pwsh
pre-commit run --all-files   # ruff check + pylint on pyhive/
mypy pyhive/                 # strict mode (see [tool.mypy] in pyproject.toml)
```

Ruff ignored rules (project-wide): `BLE001` (broad-except), `RET504` (unnecessary-assign), `ARG001` (unused-arg). Pylint excludes `_generated_*.py` and the `tests/` directory.

### Publish

Releasing is a version bump + tag; CI (`.github/workflows/publish.yml`) does the rest — builds wheels for 3.11–3.14, cuts the GitHub Release, and pushes the wheel + regenerated index into `System-B90/.github`'s `pypi/pyhive/`.

```pwsh
python ..\.github\scripts\publish.py . patch   # or: minor / major
```

(assumes the standard sibling checkout layout, `pyhive` and `.github` both under the same parent dir). The script:
1. Bumps `version` in `pyproject.toml`.
2. Commits directly to `master` as `Vibe-Bumped version to X.Y.Z` and pushes — **the one sanctioned exception to "never commit directly to master"**, since a version bump has nothing to review and always immediately precedes the tag.
3. Tags `vX.Y.Z` and pushes the tag, which triggers the release workflow.

Requires `master` to be clean and checked out locally, and a git identity that can push directly (bypasses the PR flow, not branch protection).

Verify the release landed: `gh run list --branch vX.Y.Z` in the pyhive repo, and check `https://raw.githubusercontent.com/System-B90/.github/main/pypi/pyhive/index.html` (needs a PAT) lists the new wheel.

## Code conventions

- **Python ≥ 3.11**: use `X | Y` union syntax, built-in generics (`list[X]`, `dict[K, V]`), not `Union`/`List`/`Dict`.
- **Full annotations required** everywhere — mypy strict mode enforces this.
- **No comments** unless the *why* is non-obvious (hidden constraint, workaround, subtle invariant). Never describe *what* the code does.
- **No multi-line docstrings** for internal helpers; one-line max for public methods.
- **Pydantic V2 models** live under `pyhive/src/types/`; enums under `pyhive/src/types/enums/`.
- **Broad except** (`except Exception`) is permitted where unavoidable (keyring, cleanup paths) — add `# pylint: disable=broad-exception-caught`.

## Adding a new CLI command

1. Decorate a function with `@app.command()` (or `@<sub_app>.command()`) in the relevant `cli/*.py` file.
2. Call `get_hive_client(hive_url, verify)` to obtain an authenticated client.
3. Wrap output with `print_result(data_dict, text_fallback)` for JSON/text duality.
4. Use `print_error_and_exit(message, error_data)` for all error paths.
5. Do **not** declare `use_json` or `cache_token` — injected automatically by `PyHiveTyper`.

## Known gotchas

- `HiveClient.__repr__` contains `input()` — this is intentional (prevents accidental credential leakage in logs) and should not be "fixed".
- `AuthenticatedHiveClient._api_version_check()` makes a live network call at construction; pass `skip_version_check=True` in tests to avoid this overhead.
- The `dist/` directory contains a vendored venv used for distribution; it is not the development environment and should not be modified.
- The `verify-tag-version` pre-push hook prints a `✅` on success; on Windows consoles with a non-UTF-8 codepage this crashes with `UnicodeEncodeError` even though the check itself passed. Run the push with `PYTHONIOENCODING=utf-8` (e.g. `PYTHONIOENCODING=utf-8 git push origin vX.Y.Z`) rather than `--no-verify`.
