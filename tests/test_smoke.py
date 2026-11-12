"""Smoke tests: the scaffold is wired up and no secret can slip in. Add your own beside these."""

import importlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_packages_import():
    for name in ("llm", "sourcebook", "groundtruth"):
        importlib.import_module(name)


def test_env_example_has_placeholders_only():
    lines = (ROOT / ".env.example").read_text().splitlines()
    values = dict(line.split("=", 1) for line in lines if line.strip() and not line.startswith("#"))
    assert values["ANTHROPIC_API_KEY"].strip() == "", "never put a real key in .env.example"
    assert values["LLM_MODEL"].strip(), "the model ID comes from configuration"


def test_env_is_gitignored():
    assert ".env" in (ROOT / ".gitignore").read_text().splitlines()
