# Windows installer

The release artifact is `dist/installer/install.exe`. End users do not need Python.
The build machine needs Python, PyInstaller, and Inno Setup.

From a Windows checkout, run PowerShell:

```powershell
./scripts/build_windows_installer.ps1
```

The script creates self-contained `dist/windows/memoidx.exe` and
`dist/windows/memoidx-init.exe`, then packages them into an installer folder
containing `dist/installer/install.exe` and its adjacent `.bin` payload files.
`--SkipInno` builds only the portable
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

The installer uses `UseSetupLdr=no`, so it does not extract a setup engine into
`%TEMP%` before running it. This avoids the common Windows Application Control
Error 4551 path. The installer cannot prove that a host platform supports or actually invokes a
native subagent. Use `docs/subagent-verification.md` in a fresh host session.

For a signed release, provide a Windows SDK `signtool.exe` and a publisher's
PFX certificate. The script signs both portable executables before packaging,
then signs the installer too:

```powershell
.\scripts\build_windows_installer.ps1 `
  -CertificatePath C:\secure\memoidx-release.pfx `
  -TimestampUrl https://timestamp.digicert.com
```

The PFX password is requested securely when `-CertificatePassword` is omitted.
For CI, pass the password through the build secret mechanism. Test
uninstall/reinstall on a clean Windows user before distributing the signed
installer.
