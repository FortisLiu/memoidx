# MemoIdx

MemoIdx is a local Markdown memory system for coding agents. It stores durable
facts in user-level and project-level memory roots and provides a CLI for
searching, recalling, creating, editing, forgetting, and maintaining them.

## For users

### Quick start

1. Run the provided install.exe installer.

2. In the workspace where you want to use MemoIdx, open a new terminal and run:

   ~~~text
   memoidx-init --workspace .
   ~~~

   This creates or initializes the project root at <workspace>/.memoidx, the
   user root at ~/.memoidx, root configuration, retention state, and agent
   instruction files including MemoIdx.md, memoidx-cli.md, memoidx-scout.md,
   AGENTS.md, and CLAUDE.md. Existing instruction files are preserved and
   augmented only when needed.

3. Restart the agent session. You can then ask the agent to start memorizing.

Initialization is safe to repeat for the same workspace. To initialize a
different workspace, run memoidx-init --workspace <PATH> from any terminal.

### Uninstall

Use one of these Windows options:

- Open Windows Settings > Apps > Installed apps, find MemoIdx, and select
  Uninstall.
- Run the uninstaller from the MemoIdx installation directory if one was
  provided by the installer.

Uninstalling the application does not automatically remove memory roots or
workspace instruction files. Remove those separately only if their data is no
longer needed. Forgetting a memory removes managed MemoIdx data, not backups,
Git history, or conversation history.

## For developers

### Install from source

Python 3.11 or newer is required only for source installation or development:

~~~powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install .
~~~

The package exposes memoidx and memoidx-init. Run python -m memoidx directly
from a checkout when a package installation is not needed.

### Build the Windows installer

Installer builds require:

- Windows PowerShell
- Python 3.11 or newer
- PyInstaller (the build script installs or upgrades it with pip)
- Inno Setup 6, including ISCC.exe, to create the installer

From the repository root, run:

~~~powershell
.\scripts\build_windows_installer.ps1
~~~

The script first builds the self-contained portable executables:

~~~text
dist/windows/memoidx.exe
dist/windows/memoidx-init.exe
~~~

It then uses Inno Setup to create:

~~~text
dist/installer/install.exe
~~~

To build only the portable executables without Inno Setup:

~~~powershell
.\scripts\build_windows_installer.ps1 -SkipInno
~~~

For a signed release, pass a publisher PFX certificate. The script signs both
portable executables and `dist/installer/install.exe` (the PFX password is
requested securely if omitted):

~~~powershell
.\scripts\build_windows_installer.ps1 `
  -CertificatePath C:\secure\memoidx-release.pfx `
  -TimestampUrl https://timestamp.digicert.com
~~~

The generated installer is per-user and installs under
%LOCALAPPDATA%\\MemoIdx, so administrator privileges are not required. End
users of the generated installer do not need Python.

### How the system works

MemoIdx has three levels of data:

1. A memory unit is a durable fact with a program-generated ID, content,
   source, retention class, revision, and latest-used timestamp (LUT).
2. A memory file is Markdown containing one or more units and a three-line
   abstraction used for retrieval.
3. A memory folder contains memory files and a README.md abstraction/index.

The two scopes are user (cross-workspace preferences and facts) and project
(facts and decisions for one workspace). The project root is usually
<workspace>/.memoidx; the user root is usually ~/.memoidx. roots.json selects
roots and each root's config.json stores retention settings.

The CLI flow is:

~~~text
CLI
  -> configuration and scope selection
  -> root validation and recovery check
  -> root lock
  -> read/validate Markdown and metadata
  -> transaction commit with atomic writes
  -> JSON or text result
~~~

Mutating operations use root locks and transaction helpers. Pending
transactions are recovered before normal work continues. IDs, revisions, and
timestamps are program-controlled; do not edit managed Markdown or _state
files directly.

### Core operations

- context performs bounded retrieval and touches only returned units.
- search uses literal keyword matching and returns unit IDs, paths, snippets,
  scores, revisions, and a search ID; it does not update LUTs.
- recall returns one complete unit and updates its LUT.
- remember creates a unit and performs exact active-content deduplication.
- update requires the revision that was read, preventing blind overwrites.
- forget removes a managed unit and related search traces.
- gc moves expired normal units to trash and excludes pinned units.
- restore recovers a trashed unit during the trash-retention period.

### Maintenance

After a unit write, edit, forget, or GC change, run:

~~~text
memoidx maintenance read --file <FILE> --scope <SCOPE>
        -> compose summary.json
memoidx maintenance apply --input summary.json --scope <SCOPE>
memoidx maintenance read-folder --folder <FOLDER> --scope <SCOPE>
        -> compose folder.json
memoidx maintenance apply-folder --input folder.json --scope <SCOPE>
~~~

summary.json contains file, expected_source_hash, and exactly three nonempty
single-line summary strings. folder.json contains folder,
expected_source_hash, and the same three-string summary array. Copy each hash
unchanged from the preceding read command. On a hash conflict, reread and
regenerate the input instead of overwriting concurrent work.

### Repository layout

~~~text
memoidx/       Python package and CLI implementation
tests/         unittest coverage, including failure and end-to-end paths
docs/          usage, acceptance, installer, and maintainer documentation
lab/           disposable memory fixtures
installer/     Windows installer sources
scripts/       build and installation verification scripts
~~~

Important modules include cli.py (dispatch), paths.py (root safety),
locking.py and transactions.py (concurrency and recovery), format.py
(Markdown format), search.py/recall.py (retrieval), gc.py and restore.py
(retention), and maintenance.py/folders.py (summaries).

### Development

Run the test suite:

~~~text
python -m unittest discover -s tests -v
~~~

Verify a fresh installation:

~~~text
python scripts/verify_install.py
~~~

Tests use temporary roots and controllable clocks; never use a real
~/.memoidx in tests. For behavioral details, read MemoIdx.md,
memoidx/protocol.md, and memoidx/memoidx-cli.md.
