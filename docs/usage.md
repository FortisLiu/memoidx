# Development CLI

Native memory operations are now delegated through the shared memoidx-scout.md
operator contract. Initialization installs Codex and Claude Code native
definitions and appends delegation routing even when MemoIdx.md already exists. See
[subagent-verification.md](subagent-verification.md) for a disposable fixture,
host-specific execution evidence and LUT checks. Other platforms use an explicit
native-child adapter or report main-agent-fallback; do not infer delegation
from a search trace alone.

## Install and initialize a workspace

From a checkout, install using `python -m pip install .` (prefer a virtual
environment). Alternatively install a supplied wheel with pip. No public
package registry publication is assumed.

Run `memoidx-init --workspace path/to/project` once per workspace. It creates
the user root (default ~/.memoidx), project root and instruction adapters.
Use --user-root PATH for an alternate user root. Existing MemoIdx.md and
memoidx-cli.md are preserved. Existing agent files are augmented only when no
read instruction/import is detected. No hooks or platform skills are installed.
CLAUDE.md uses @MemoIdx.md; AGENTS.md uses an explicit read instruction.
Restart the agent session after initialization so it can load instructions.

Generated MemoIdx.md contains the compact workflow. Read memoidx-cli.md on
demand, or use `memoidx reference` for the installed CLI documentation.
Older workspaces keep their existing protocol: review `memoidx protocol`
and update the document manually if desired.

```
memoidx context "short keywords"
memoidx remember --content "durable fact" --source "user decision"
memoidx update --id ID --expected-revision REV --content "replacement"
```

Context automatically searches both initialized scopes; --max-chars bounds
content characters, not tokens. Only returned units are touched. Remember
deduplicates exact active content/source/retention under a lock. Semantic
deduplication and summary creation remain the agent's responsibility.
Root discovery is in .memoidx/roots.json; retention stays in config.json.

Run from the checkout with `python -m memoidx`, or install the package and use
`memoidx`. Global flags such as `--config` and `--json` precede the subcommand.

Create a configuration in a test directory:

```json
{"user_root":"user/.memoidx","project_root":"project"}
```

Relative paths are anchored to the configuration file. Project paths point to
the project directory; `.memoidx` is appended when it is not already present.

```text
python -m memoidx --config path/to/config.json init --scope project
python -m memoidx --config path/to/config.json edit add --input path/to/add.json
python -m memoidx --config path/to/config.json search "keywords"
python -m memoidx --config path/to/config.json recall --id <returned-unit-id>
python -m memoidx --config path/to/config.json maintenance plan
python -m memoidx --config path/to/config.json maintenance read --file preferences.md
python -m memoidx --config path/to/config.json maintenance apply --input summary.json
python -m memoidx --config path/to/config.json maintenance folders
python -m memoidx --config path/to/config.json maintenance read-folder --folder .
python -m memoidx --config path/to/config.json maintenance apply-folder --input folder.json
python -m memoidx --config path/to/config.json gc --dry-run
python -m memoidx --config path/to/config.json gc --if-due
python -m memoidx --config path/to/config.json trash list
python -m memoidx --config path/to/config.json restore --id <returned-unit-id>
python -m memoidx --config path/to/config.json forget --id <returned-unit-id>
python -m memoidx --config path/to/config.json recover
python -m memoidx --config path/to/config.json doctor
python -m memoidx protocol
```

Add input contains request_id, file, content, retention (normal or pinned), and
source. Update input contains request_id, id, expected_revision, and content.
Use edit show --id to obtain the revision. IDs and timestamps come from the
program. Summary apply input contains file, expected_source_hash, and exactly
three summary strings; folder apply uses folder instead of file.

Search returns a search_id for `explain --search-id ... --id ...`. Search traces
retain matching terms, IDs, revisions and scores, but not full memory bodies.
GC expires old traces and forget removes traces related to the forgotten unit.

See acceptance.md for tested behavior and outstanding release requirements.
