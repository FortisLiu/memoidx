# Windows installer

The release artifact is `MemoIdx-Setup.exe`. End users do not need Python.
The build machine needs Python, PyInstaller, and Inno Setup.

From a Windows checkout, run PowerShell:

```powershell
./scripts/build_windows_installer.ps1
```

The script creates self-contained `dist/windows/memoidx.exe` and
`dist/windows/memoidx-init.exe`, then packages them into
`dist/installer/install.exe`. `--SkipInno` builds only the portable
executables for inspection.

The installer uses a per-user install under `%LOCALAPPDATA%\\MemoIdx`, so admin
rights are not required. It adds the CLI directory to the current user's PATH,
creates `%USERPROFILE%\\.memoidx`, and offers to initialize a selected workspace.
Initialization creates `MemoIdx.md`, `memoidx-cli.md`, `memoidx-scout.md`,
`AGENTS.md`, `CLAUDE.md`, `.codex/agents/memoidx_scout.toml`, and
`.claude/agents/memoidx-scout.md`. Existing workspace documents are preserved.

After installation, open a new terminal so PATH is refreshed:

```powershell
memoidx --version
memoidx-init --workspace C:\\work\\my-project
memoidx reference
```

The installer cannot prove that a host platform supports or actually invokes a
native subagent. Use `docs/subagent-verification.md` in a fresh host session.

Before distributing `MemoIdx-Setup.exe`, sign it with the publisher's Windows
code-signing certificate and test uninstall/reinstall on a clean Windows user.
