"""Tests for scripts/precheck.py, each in a throwaway git repo."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

from scripts import precheck

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "precheck.py"
# Ignore your global and system git config (signing, hooks) in these test repos.
GIT_ENV = {**os.environ, "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1"}


def git(repo: Path, *args: str) -> None:
    identity = ["-c", "user.name=Test", "-c", "user.email=test@example.com"]
    subprocess.run(
        ["git", *identity, *args], cwd=repo, env=GIT_ENV, check=True, capture_output=True
    )


def write(repo: Path, *paths: str) -> None:
    for p in paths:
        (repo / p).parent.mkdir(parents=True, exist_ok=True)
        (repo / p).write_text("x\n")


def commit_and_tag(repo: Path, tag: str, *extra: str) -> None:
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "--allow-empty", "-m", tag)
    git(repo, "tag", *extra, tag)


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    git(tmp_path, "init", "-q")
    monkeypatch.chdir(tmp_path)
    return tmp_path


def test_checks_cover_every_checkpoint_tag():
    assert list(precheck.CHECKS) == ["v0.1", "v0.2", "v0.3", "v0.4", "v0.5", "v0.6", "v1.0"]
    assert all(spec["forbiddenPaths"] == [".env"] for spec in precheck.CHECKS.values())
    green = [tag for tag, spec in precheck.CHECKS.items() if spec.get("requireGreenCI")]
    assert green == ["v0.6", "v1.0"]


def test_has_path_matches_files_and_directories_but_not_prefixes():
    files = {"prompts/extract.yaml", "promptsX.txt", ".env.example"}
    assert precheck.has_path(files, "prompts")
    assert precheck.has_path(files, "prompts/")
    assert not precheck.has_path({"promptsX.txt"}, "prompts")
    assert not precheck.has_path(files, ".env")


def test_tag_with_missing_path_fails_then_passes_once_fixed(repo, capsys):
    write(repo, "README.md", ".env.example")
    commit_and_tag(repo, "v0.1")
    assert precheck.main(["v0.1"]) == 1
    assert "MISSING  EXPERIMENTS.md" in capsys.readouterr().out

    write(repo, "EXPERIMENTS.md")
    commit_and_tag(repo, "v0.1", "-f")
    assert precheck.main(["v0.1"]) == 0


def test_tag_mode_reads_the_tag_not_the_working_tree(repo):
    write(repo, "README.md")
    commit_and_tag(repo, "v0.2", "-a", "-m", "annotated tags work too")
    write(repo, "prompts/extract.yaml", "data/README.md")  # added after the tag
    assert precheck.check("v0.2", precheck.files_at_tag(repo, "v0.2")) == [
        ("required", "prompts", False),
        ("required", "data/README.md", False),
        ("forbidden", ".env", True),
    ]
    assert precheck.main(["v0.2", "--worktree"]) == 0


def test_committed_env_fails(repo, capsys):
    write(repo, "README.md", "sourcebook/agent/loop.py", ".env")
    commit_and_tag(repo, "v0.4")
    assert precheck.main(["v0.4"]) == 1
    assert "FOUND    no .env committed" in capsys.readouterr().out


def test_worktree_skips_an_ignored_env_but_flags_an_unignored_one(repo):
    write(repo, "README.md", "sourcebook/agent/loop.py", ".env")
    (repo / ".gitignore").write_text(".env\n")
    assert precheck.main(["v0.4", "--worktree"]) == 0
    (repo / ".gitignore").unlink()
    assert precheck.main(["v0.4", "--worktree"]) == 1


def test_missing_tag_and_non_repo_cannot_run(repo, tmp_path_factory, monkeypatch, capsys):
    assert precheck.main(["v0.3"]) == 2
    assert "no tag v0.3" in capsys.readouterr().err
    monkeypatch.chdir(tmp_path_factory.mktemp("not-a-repo"))
    assert precheck.main(["v0.3"]) == 2


def test_cli_runs_as_a_script(repo):
    write(repo, "README.md")
    out = subprocess.run(
        [sys.executable, str(SCRIPT), "v0.1", "--worktree"],
        cwd=repo,
        capture_output=True,
        text=True,
    )
    assert out.returncode == 1
    assert "MISSING  EXPERIMENTS.md" in out.stdout
    assert "MISSING  .env.example" in out.stdout
