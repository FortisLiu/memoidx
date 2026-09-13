# Acceptance record

Status: development build; not yet a fully accepted v0.1 release.

## Executed on this workstation

Environment: Windows, Python 3.14. Test roots are TemporaryDirectory instances.
Real user memory is not used. Time follows the explicit project decision to
use UTC+08:00. Hooks are excluded by user instruction.

Command: `python -m unittest discover -s tests -v`

The suite includes:

- Core E2E: initialize two roots; add three units; retry add; update with a
  revision; reject stale update; search without changing LUT; recall one unit;
  preserve siblings' LUT; apply abstraction; refresh README; display tree;
  advance fake time; dry-run and execute GC; restore; forget; recover an
  interrupted transaction; doctor; scan all managed files for forgotten text.
- CLI E2E: initialize, add/retry, search, recall, forget, search again.
- Format failures and lossless round trips for blank lines, indentation,
  code, triple quotes, Unicode, and subsecond timestamps.
- Atomic replacement failure, lock timeout, prepared-transaction recovery,
  conflict preservation, and interrupted cleanup without replay.
- Search explanation version history, trace removal on forget, update retry.

Latest result: 32 tests run, 31 passed, 1 skipped because this Windows account
cannot create symlinks. Core E2E and CLI E2E both passed. The suite includes a
real subprocess termination test confirming that the root lock is released.

Installation verification: `python scripts/verify_install.py` passed. It built
a wheel in an isolated copy, installed with `--no-index --no-deps` into a fresh
virtual environment, and executed the CLI and packaged protocol outside the
checkout. Build dependencies were downloaded before the offline install.

These tests pass on the workstation. They are not evidence that every
requirement in the full development manual is complete.

## Outstanding acceptance work

- Linux and macOS execution, genuine process-kill tests at every transaction
  boundary, and OS-specific crash durability testing.
- Four-platform native maintainer configuration and live cross-agent tests;
  current docs/agents files are instruction drafts, not installed agents.
- Canonical schema-1 migration: the current reader retains MemoIdx.md's legacy
  lowercase `file id` layout. Source is currently text, including encoded JSON.

No untested platform or model availability is claimed. No hooks were created.
