# Sourcebook starter

The starting repo for the capstone in the [PixioLab AI Mentor](https://pixiolab.com)
45-day path. Over six weeks it grows into one system:

- **Sourcebook**: hybrid-search RAG with citations and permission-aware retrieval.
- **Groundtruth**: the eval harness that measures its retrieval.
- **Tripwire**: the CI gate that blocks a pull request when quality regresses.

This template gives you the plumbing (project config, lint, tests, CI, a
pre-check script) and none of the build. Every folder that matters is empty
until the day that fills it.

## Start here (Day 1)

1. **Create your repo.** On this page, click **Use this template → Create a new
   repository**. Make it **public**: the checks on pixiolab.com read public repos
   only. `sourcebook` is a good name.
2. **Clone and install.** You need Python 3.11+ and [uv](https://docs.astral.sh/uv/).

   ```bash
   git clone https://github.com/YOUR-NAME/sourcebook.git
   cd sourcebook
   uv sync
   ```

   `uv sync` creates `.venv/` and `uv.lock`. Commit `uv.lock`, so a fresh clone
   installs the same versions.
3. **Add your key.** Run `cp .env.example .env` and paste in an API key made
   just for this project. `.env` is git-ignored: check that `git status` never
   lists it. If a key ever reaches GitHub, revoke it in your provider's console,
   because deleting the file leaves it in the history.
4. **Check the scaffold.** `uv run pytest -q` and `uv run ruff check .` both
   pass on a fresh clone, with no key and no network.
5. **Follow [Day 1 on pixiolab.com](https://pixiolab.com/path/d01).** The template
   has done `uv init`, `uv add anthropic pydantic`, `.gitignore`, `.env.example`
   and the `LEARNING.md` headings for you. You still set a spend limit, then
   commit and push `uv.lock`.

## The rule

> Use AI coding tools, and own every line. Let an assistant write boilerplate,
> tests and refactors; you make the design decisions, write the eval cases and
> read every diff. If you can't explain a line, you can't ship it, and an
> interviewer will ask.

## Folder map

Paths marked * aren't in the template: you create them on the day shown. They
are what the checkpoint checks look for, so the template leaves them to you.

| Path | When | What goes there |
|---|---|---|
| `README.md` | Day 43 | This file, until you rewrite it results-first. |
| `LEARNING.md` | Every week | What you built, one decision + evidence, one thing that broke. |
| `CHANGELOG.md` | Every tag | What changed, and which number it moved. |
| `EXPERIMENTS.md` * | Week 1, Day 7 | Your logged runs, with numbers. |
| `llm/` | Weeks 1–2, Days 6 and 12 | Client, timeouts, retries, cost log. |
| `warmups/` * | Weeks 1–2, Days 6 and 10 | `hello_llm.py`, `extract.py`. |
| `prompts/` * | Week 2, Day 9 | Versioned prompt files. |
| `data/README.md` * | Week 2, Day 14 | Corpus source, license and document count. |
| `sourcebook/` | Week 3, Days 16–20 | Ingest, chunk, index, retrieve, answer. |
| `sourcebook/agent/` * | Week 4, Days 23–27 | Tool loop, budgets, traces. |
| `groundtruth/` | Week 5, Days 31–32 | Metrics, runner, judge. |
| `eval/` * | Days 21, 30 and 38 | `golden.jsonl`, then `attacks.jsonl`. |
| `results/` * | Week 5 on, from Day 31 | One JSON file per eval run, committed. |
| `ml-basics/` * | Week 6, Day 40 | A classic ML notebook, beside the core. |
| `.github/workflows/` | Now, then Day 41 | `tests.yml` runs lint and tests; you add `eval.yml`, the Tripwire gate. |
| `tests/` | Week 2 on | Starter tests; yours go beside them. |
| `scripts/precheck.py` | Before each tag | The website's path checks, run locally. |

`llm/`, `sourcebook/` and `groundtruth/` hold only an `__init__.py` whose
docstring links the day that fills them.

## Checkpoint tags

Tag a release at the end of each week, and pixiolab.com checks it. Every tag
must be pushed, the repo public, and no `.env` committed. The full criteria are
on each checkpoint page.

| Tag | Day | Must contain | Paths checked automatically |
|---|---|---|---|
| [`v0.1`](https://pixiolab.com/path/w1-check) | 7 | An `llm/` client that logs model, stop reason, tokens and latency to JSONL; 4+ runs in `EXPERIMENTS.md`; a fresh clone runs with `uv sync` and one environment variable. | `README.md`, `EXPERIMENTS.md`, `.env.example` |
| [`v0.2`](https://pixiolab.com/path/w2-check) | 14 | The extractor CLI with a schema and one tool; field-level accuracy on 20 labeled inputs; timeouts and safe retries; prompts in files; the corpus chosen. | `prompts/`, `data/README.md` |
| [`v0.3`](https://pixiolab.com/path/w3-check) | 21 | Sourcebook `ingest` and `ask` with checked citations; recall@5 for vector-only vs hybrid, n = 20, in the README. | `README.md`, `data/README.md` |
| [`v0.4`](https://pixiolab.com/path/w4-check) | 28 | Agent mode with budgets and a trace per run; plain vs agent on 10 multi-part questions in the README. | `README.md`, `sourcebook/agent/` |
| [`v0.5`](https://pixiolab.com/path/w5-check) | 35 | 50+ golden questions; Groundtruth metrics written to `results/`; 3+ configs compared; judge TPR and TNR; p50/p95 latency and cost per 100 queries. | `eval/golden.jsonl`, `results/` |
| [`v0.6`](https://pixiolab.com/path/w6-check) | 42 | 20+ attacks; a permission test; Tripwire failing a deliberately bad PR; the ML notebook. CI must be green. | `eval/attacks.jsonl`, `.github/workflows/`, `ml-basics/` |
| [`v1.0`](https://pixiolab.com/path/final-check) | 44 | A results-first README; three-command setup; a green CI badge and a linked PR the gate caught; a demo video; known limitations. CI must be green. | `README.md`, `.env.example`, `eval/golden.jsonl`, `eval/attacks.jsonl`, `results/` |

CI is only a warning before `v0.6`. The automatic checks look for paths, and
this template already holds a few of them; passing them is the floor, and the
criteria are about what's inside.

### Check before you tag

```bash
uv run python scripts/precheck.py v0.2 --worktree   # what you'd commit now
git tag v0.2
uv run python scripts/precheck.py v0.2              # what the tag holds
git push origin v0.2
```

`precheck.py` mirrors the website's path checks; when they disagree, the
website wins. Before each tag, add an entry to `CHANGELOG.md` and the week's
three lines to `LEARNING.md`.

## Everyday commands

```bash
uv sync                               # install what pyproject.toml and uv.lock list
uv add chromadb                       # add a dependency (you will on Day 17)
uv run pytest -q                      # tests: offline, no key needed
uv run ruff check .                   # lint; CI runs this and the tests
uv run ruff format .                  # format
uv run python -m warmups.hello_llm    # run modules from the repo root (Day 6)
```

## This README is temporary

It explains the template. On [Day 43](https://pixiolab.com/path/d43) you replace
all of it with your project's README, results first: a one-sentence summary and
a results table with every n, then demo, architecture, method, decisions and
known limitations.

## License

MIT, © 2026 PixioLab. Your code is yours: put your name on the copyright line
in `LICENSE`, or choose another license.
