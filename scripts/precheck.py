"""Run pixiolab.com's automatic path checks for a checkpoint tag, locally.

    uv run python scripts/precheck.py v0.2             # the files at tag v0.2
    uv run python scripts/precheck.py v0.2 --worktree  # the files you'd commit now

Tag mode reads `git ls-tree -r --name-only` at the tag. Worktree mode lists
tracked files plus untracked files that .gitignore doesn't exclude, which is
what `git add -A` would commit. A required directory counts when it holds at
least one file, as on GitHub. Standard library only.

It checks paths and nothing else. The website also checks that the repo is
public, that the tag is pushed, and CI at the tag. Exit code: 0 when every
check passes, 1 when one fails, 2 when the check can't run.
"""

import argparse
import subprocess
import sys
from pathlib import Path

# Mirrors the automatic checks pixiolab.com runs at each checkpoint tag, 2026
# edition, with the website's field names. The website is the source of truth:
# if this list and the site disagree, the site wins. From v0.6 on, CI must also
# be green at the tag; before that a red or missing CI is only a warning.
CHECKS: dict[str, dict] = {
    "v0.1": {
        "requiredPaths": ["README.md", "EXPERIMENTS.md", ".env.example"],
        "forbiddenPaths": [".env"],
    },
    "v0.2": {
        "requiredPaths": ["prompts", "data/README.md"],
        "forbiddenPaths": [".env"],
    },
    "v0.3": {
        "requiredPaths": ["README.md", "data/README.md"],
        "forbiddenPaths": [".env"],
    },
    "v0.4": {
        "requiredPaths": ["README.md", "sourcebook/agent"],
        "forbiddenPaths": [".env"],
    },
    "v0.5": {
        "requiredPaths": ["eval/golden.jsonl", "results"],
        "forbiddenPaths": [".env"],
    },
    "v0.6": {
        "requiredPaths": ["eval/attacks.jsonl", ".github/workflows", "ml-basics"],
        "forbiddenPaths": [".env"],
        "requireGreenCI": True,
    },
    "v1.0": {
        "requiredPaths": [
            "README.md",
            ".env.example",
            "eval/golden.jsonl",
            "eval/attacks.jsonl",
            "results",
        ],
        "forbiddenPaths": [".env"],
        "requireGreenCI": True,
    },
}


class PrecheckError(Exception):
    """The check couldn't run: not a git repo, no such tag, no git."""


def _git(repo: Path, *args: str) -> str:
    try:
        out = subprocess.run(
            ["git", "-C", str(repo), *args], capture_output=True, text=True, check=False
        )
    except FileNotFoundError:
        raise PrecheckError("git isn't installed or isn't on PATH.") from None
    if out.returncode != 0:
        raise PrecheckError(out.stderr.strip() or f"git {args[0]} failed")
    return out.stdout


def repo_root(start: Path) -> Path:
    try:
        return Path(_git(start, "rev-parse", "--show-toplevel").strip())
    except PrecheckError:
        raise PrecheckError(f"{start} isn't inside a git repository.") from None


def files_at_tag(repo: Path, tag: str) -> set[str]:
    """Every file path in the tree at refs/tags/<tag>, relative to the repo root."""
    ref = f"refs/tags/{tag}"
    try:
        _git(repo, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}")
    except PrecheckError:
        raise PrecheckError(
            f"There's no tag {tag} here. Create it with: git tag {tag}\n"
            f"Or check what you'd commit now: precheck.py {tag} --worktree"
        ) from None
    return {p for p in _git(repo, "ls-tree", "-r", "--name-only", "-z", ref).split("\0") if p}


def files_in_worktree(repo: Path) -> set[str]:
    """Tracked files plus untracked files .gitignore doesn't exclude, minus deleted ones."""
    listed = _git(repo, "ls-files", "-z", "--cached", "--others", "--exclude-standard")
    return {p for p in listed.split("\0") if p and (repo / p).exists()}


def has_path(files: set[str], path: str) -> bool:
    """True if `path` is a file in `files`, or a directory holding at least one of them."""
    path = path.rstrip("/")
    return path in files or any(f.startswith(path + "/") for f in files)


def check(tag: str, files: set[str]) -> list[tuple[str, str, bool]]:
    """(kind, path, passed) for each required and forbidden path of a checkpoint tag."""
    spec = CHECKS[tag]
    results = [("required", p, has_path(files, p)) for p in spec["requiredPaths"]]
    results += [("forbidden", p, not has_path(files, p)) for p in spec["forbiddenPaths"]]
    return results


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check a checkpoint tag's required and forbidden paths, as pixiolab.com does.",
    )
    parser.add_argument("tag", choices=list(CHECKS), help="the checkpoint tag to check")
    parser.add_argument(
        "--worktree",
        action="store_true",
        help="check the files you'd commit now instead of the files at the tag",
    )
    args = parser.parse_args(argv)

    try:
        repo = repo_root(Path.cwd())
        if args.worktree:
            files = files_in_worktree(repo)
            source = "the working tree (what `git add -A` would commit)"
        else:
            files = files_at_tag(repo, args.tag)
            source = f"tag {args.tag}"
    except PrecheckError as err:
        print(f"precheck: {err}", file=sys.stderr)
        return 2

    results = check(args.tag, files)
    print(f"Checkpoint {args.tag}: checking {source}\n")
    for kind, path, passed in results:
        if kind == "required":
            print(f"  {'ok' if passed else 'MISSING':8} {path}")
        else:
            print(f"  {'ok' if passed else 'FOUND':8} no {path} committed")

    failed = [(kind, path) for kind, path, passed in results if not passed]
    if CHECKS[args.tag].get("requireGreenCI"):
        ci = "CI must be green at the tag (from v0.6 on)"
    else:
        ci = "CI is a warning only until v0.6"
    print(
        f"\nNot checked here: the repo is public, the tag is pushed "
        f"(git push origin {args.tag}), and CI. {ci}."
    )
    if not failed:
        print("All path checks pass.")
        return 0

    print(f"\n{len(failed)} check(s) failed.")
    for kind, path in failed:
        if kind == "forbidden" and args.worktree:
            print(
                f"  {path} would be committed. Add it to .gitignore, and run "
                f"git rm --cached {path} if git already tracks it."
            )
        elif kind == "forbidden":
            print(
                f"  {path} is in the repository. Delete it, rotate every key it held, "
                f"and add it to .gitignore."
            )
    if any(kind == "required" for kind, _ in failed):
        print("  Commit the missing paths.")
    if not args.worktree:
        print(
            f"  Then move the tag to the fixed commit: "
            f"git tag -f {args.tag} && git push -f origin {args.tag}"
        )
    return 1


if __name__ == "__main__":
    sys.exit(main())
