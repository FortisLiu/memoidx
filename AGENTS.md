## Mandatory MemoIdx Protocol

Before starting any task, read and follow `MemoIdx.md`.
Treat `MemoIdx.md` as mandatory repository guidance.

# Repository Guidelines

## Project Structure

`memoidx/` contains the Python package and CLI. Core areas include Markdown
format parsing (`format.py`), models, paths and initialization, atomic storage
and locking, transactions and recovery, search/recall, retention, and
maintenance. `tests/` contains the `unittest` suite, including unit, failure,
CLI, and end-to-end tests. `docs/` contains usage, acceptance, and platform
maintainer guidance. `lab/` is disposable test data; do not use real memory
roots there. `MemoIdx.md` and `memoidx/protocol.md` define the shared protocol.

## Build, Test, and Development Commands

Run the complete test suite:

```text
python -m unittest discover -s tests -v
```

Run a focused test module, for example:

```text
python -m unittest tests.test_end_to_end -v
```

Build and verify a fresh installation with:

```text
python scripts/verify_install.py
```

Run the CLI locally with `python -m memoidx --help`; use `--config` with a
test configuration before commands that access memory. Do not add hooks.

## Coding Style and Naming

Use Python 3.11+ and four-space indentation. Follow standard PEP 8 naming:
`snake_case` for functions and variables, `PascalCase` for classes, and clear
exception names ending in `Error`. Keep file writes UTF-8 with LF newlines,
use program-generated IDs and timestamps, and preserve the Markdown format
strictly. Prefer small, typed functions and explicit validation over silent
repair. No formatter or linter is currently configured.

## Testing Guidelines

Use Python's built-in `unittest`. Name files `test_*.py` and test methods
`test_*`. Tests must use temporary roots and injectable clocks; never write to
`~/.memoidx`. Include meaningful failure-path coverage for malformed files,
path escapes, lock conflicts, transaction recovery, and unchanged LUTs.

## Commits and Pull Requests

Use imperative, descriptive commit subjects, such as `Add controllable clock
and stable IDs`. Explain behavior and validation in the body. Pull requests
should describe the user-visible change, list tests run, identify platform or
filesystem limitations, and call out protocol or data-format changes. Do not
include real user memory or generated cache files.

## Safety and Configuration

Use `MemoIdx.md` and `memoidx/protocol.md` as the behavioral references. Route
mutations through locking and transaction helpers. Keep configuration paths
anchored to the config file and verify resolved paths remain inside the
selected root.
