# MemoIdx

MemoIdx is a local, Markdown-based memory cabinet for coding agents. A
`MemoryUnit` is a stable memory card; a memory file is a notebook containing
related cards; a folder `README.md` is the drawer index. The same files can be
used by Claude Code, Codex, OpenCode, and AGY. Read [MemoIdx.md](MemoIdx.md)
before changing or operating on memory.

MemoIdx stores data locally and does not need a database, vector store, or
external service. If a cloud agent reads recalled text, that text still enters
the provider's context. The current implementation uses UTC+08:00 timestamps,
UUID-based `f_` file IDs and `u_` unit IDs, strict Markdown parsing, atomic
writes, locks, and recoverable transactions.

## For users

Install the package in a development environment:

```text
python -m pip install -e .
memoidx --version
```

Create a test configuration whose paths are relative to the configuration file:

```json
{"user_root":"user/.memoidx","project_root":"project"}
```

Initialize and use a project memory cabinet:

```text
memoidx --config config.json init --scope project
memoidx --config config.json edit add --input add.json
memoidx --config config.json search "繁體中文 回答"
memoidx --config config.json recall --id <unit-id>
memoidx --config config.json edit show --id <unit-id>
memoidx --config config.json forget --id <unit-id>
```

Use `gc --dry-run` to preview expiry, `restore --id` to restore a trashed
unit, `doctor` to inspect errors, `tree` to view the cabinet, and `protocol`
to print the agent protocol. Add, update, and maintenance inputs are JSON;
see [docs/usage.md](docs/usage.md) for fields and examples.

## For developers

Source code is in `memoidx/`; tests are in `tests/`; design and acceptance
notes are in `docs/`; `lab/` contains disposable fixtures. Important modules
include `format.py` for Markdown, `transactions.py` for recovery,
`repository.py` for reads, and `search.py`, `recall.py`, `gc.py`, and
`forget.py` for lifecycle operations.

Run all tests:

```text
python -m unittest discover -s tests -v
```

Verify wheel installation in a fresh environment:

```text
python scripts/verify_install.py
```

Tests must use temporary roots and injectable clocks. Route mutations through
the locking and transaction helpers. Do not commit real memory, generated
`__pycache__` files, or hook integrations. Use imperative commit subjects and
include validation results in the commit body. See [AGENTS.md](AGENTS.md) for
contributor rules and [docs/acceptance.md](docs/acceptance.md) for current
verification status and known limitations.
