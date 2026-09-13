"""Build in an isolated copy and install a wheel into a fresh environment."""
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import venv


def run(args, cwd):
    result = subprocess.run([str(arg) for arg in args], cwd=cwd, capture_output=True,
                            text=True, encoding="utf-8",
                            env={**os.environ, "PYTHONIOENCODING": "utf-8"})
    if result.returncode:
        raise RuntimeError(result.stdout + result.stderr)
    return result.stdout


def main():
    source = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix="memoidx-install-") as directory:
        work = Path(directory)
        checkout = work / "source"
        checkout.mkdir()
        shutil.copytree(source / "memoidx", checkout / "memoidx", ignore=shutil.ignore_patterns("__pycache__"))
        shutil.copy2(source / "pyproject.toml", checkout / "pyproject.toml")
        build = work / "build-env"
        venv.create(build, with_pip=True)
        executable = "Scripts/python.exe" if os.name == "nt" else "bin/python"
        builder = build / executable
        run([builder, "-m", "pip", "install", "setuptools>=68", "wheel"], work)
        wheels = work / "wheels"
        run([builder, "-m", "pip", "wheel", "--no-build-isolation", "--no-deps", "--wheel-dir", wheels, checkout], work)
        target = work / "fresh-env"
        venv.create(target, with_pip=True)
        python = target / executable
        wheel = next(wheels.glob("memoidx_memory-*.whl"))
        run([python, "-m", "pip", "install", "--no-index", "--no-deps", wheel], work)
        cli = target / ("Scripts/memoidx.exe" if os.name == "nt" else "bin/memoidx")
        assert "0.1.0" in run([cli, "--version"], work)
        assert "MemoIdx protocol" in run([cli, "protocol"], work)
        assert "Frequent operations" in run([cli, "reference"], work)
        bootstrap = target / ("Scripts/memoidx-init.exe" if os.name == "nt" else "bin/memoidx-init")
        workspace = work / "installed-workspace"
        run([bootstrap, "--workspace", workspace, "--user-root", work / "isolated-user"], work)
        assert "@MemoIdx.md" in (workspace / "CLAUDE.md").read_text()
        assert (workspace / "memoidx-cli.md").is_file()
        assert (workspace / "memoidx-scout.md").is_file()
        assert (workspace / ".codex/agents/memoidx_scout.toml").is_file()
        assert (workspace / ".claude/agents/memoidx-scout.md").is_file()
        added = json.loads(run([cli, "remember", "--content", "installation fact", "--source", "test"], workspace))
        result = json.loads(run([cli, "--json", "context", "installation"], workspace))
        assert result["memories"][0]["id"] == added["id"]
        revision = result["memories"][0]["revision"]
        run([cli, "update", "--id", added["id"], "--expected-revision", revision,
             "--content", "updated installation fact"], workspace)
        config = work / "lab.json"
        config.write_text(json.dumps({"user_root": "user/.memoidx", "project_root": "project"}))
        run([cli, "--config", config, "init", "--scope", "project"], work)
        assert (work / "project" / ".memoidx" / "config.json").exists()
        print("PASS: wheel built; offline fresh-environment installation; CLI and protocol work outside checkout")


if __name__ == "__main__":
    main()
