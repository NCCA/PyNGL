# Agentic Knowledge Wiki Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `wiki/` of agent-maintained markdown pages about how PyNGL works, a stdlib-only staleness checker (`wiki/tools/check_sync.py`), and a `/wiki` project skill to build/update it.

**Architecture:** Every wiki page carries YAML frontmatter (`sources:` globs + `synced:` commit hash). `check_sync.py` diffs each page's sources since its synced commit to find stale pages and flags `src/` files no page covers. A project skill (`.claude/skills/wiki/SKILL.md`) drives `status`/`update`/`build` workflows using that script.

**Tech Stack:** Python ≥3.11 stdlib only (argparse, subprocess, re, json, pathlib, dataclasses), git, pytest, markdown.

**Spec:** `docs/superpowers/specs/2026-07-06-agentic-knowledge-wiki-design.md`

## Global Constraints

- Work on branch `agent/knowledge-wiki` in a git worktree (`git worktree add .worktrees/knowledge-wiki -b agent/knowledge-wiki`) — never commit to `main`.
- All commands via `uv run` (`uv run pytest`, `uv run ruff check`).
- `check_sync.py` uses **stdlib only** — no PyYAML, no third-party deps.
- Executable script shebang: `#!/usr/bin/env -S uv run --script`.
- Type hints on all signatures; Google-style docstrings with Args/Returns/Raises.
- "Colour" spelling in prose and identifiers.
- Conventional commit messages.
- Run the **whole** default test suite (`uv run pytest`) after changes, not just the new tests.
- Wiki pages: frontmatter (`sources`, `synced` = full 40-char hash), then sections **Summary / How it works / Key invariants / Connections**; reference code by path, don't paste blocks.

---

### Task 1: `check_sync.py` — frontmatter parsing and glob matching

**Files:**
- Create: `wiki/tools/check_sync.py`
- Test: `tests/test_wiki_check_sync.py`

**Interfaces:**
- Produces: `Frontmatter` dataclass (`sources: list[str]`, `synced: str`); `FrontmatterError(Exception)`; `parse_frontmatter(text: str) -> Frontmatter`; `glob_to_regex(pattern: str) -> re.Pattern[str]`. Tasks 2–3 import these from the same module.

- [ ] **Step 1: Write the failing tests**

Create `tests/test_wiki_check_sync.py`:

```python
"""Tests for the wiki staleness checker (wiki/tools/check_sync.py)."""

import importlib.util
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parent.parent / "wiki" / "tools" / "check_sync.py"
_spec = importlib.util.spec_from_file_location("check_sync", _MODULE_PATH)
check_sync = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(check_sync)


class TestParseFrontmatter:
    def test_parses_sources_and_synced(self):
        text = (
            "---\n"
            "sources:\n"
            "  - src/ncca/ngl/vec*.py\n"
            "  - tests/test_api_consistency.py\n"
            "synced: 112100b112100b112100b112100b112100b11221\n"
            "---\n"
            "# Page body\n"
        )
        fm = check_sync.parse_frontmatter(text)
        assert fm.sources == ["src/ncca/ngl/vec*.py", "tests/test_api_consistency.py"]
        assert fm.synced == "112100b112100b112100b112100b112100b11221"

    def test_missing_opening_delimiter_raises(self):
        with pytest.raises(check_sync.FrontmatterError):
            check_sync.parse_frontmatter("# no frontmatter here\n")

    def test_missing_closing_delimiter_raises(self):
        with pytest.raises(check_sync.FrontmatterError):
            check_sync.parse_frontmatter("---\nsources:\n  - a.py\nsynced: abc\n")

    def test_missing_synced_raises(self):
        with pytest.raises(check_sync.FrontmatterError):
            check_sync.parse_frontmatter("---\nsources:\n  - a.py\n---\n")

    def test_missing_or_empty_sources_raises(self):
        with pytest.raises(check_sync.FrontmatterError):
            check_sync.parse_frontmatter("---\nsynced: abc\n---\n")
        with pytest.raises(check_sync.FrontmatterError):
            check_sync.parse_frontmatter("---\nsources:\nsynced: abc\n---\n")


class TestGlobToRegex:
    @pytest.mark.parametrize(
        ("pattern", "path", "matches"),
        [
            ("src/ncca/ngl/vec*.py", "src/ncca/ngl/vec3.py", True),
            ("src/ncca/ngl/vec*.py", "src/ncca/ngl/vec3_array.py", True),
            ("src/ncca/ngl/vec*.py", "src/ncca/ngl/opengl/vec3.py", False),  # * stays in one dir
            ("src/ncca/ngl/webgpu/**", "src/ncca/ngl/webgpu/line_pipeline.py", True),
            ("**/conftest.py", "tests/conftest.py", True),
            ("**/conftest.py", "conftest.py", True),  # **/ also matches zero dirs
            ("src/ncca/ngl/mat?.py", "src/ncca/ngl/mat4.py", True),
            ("src/ncca/ngl/mat?.py", "src/ncca/ngl/mat44.py", False),
            ("src/ncca/ngl/obj.py", "src/ncca/ngl/obj.py", True),
            ("src/ncca/ngl/obj.py", "src/ncca/ngl/objx.py", False),
        ],
    )
    def test_matching(self, pattern, path, matches):
        assert bool(check_sync.glob_to_regex(pattern).match(path)) is matches
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_wiki_check_sync.py -v`
Expected: FAIL at import time — `FileNotFoundError` (module file doesn't exist yet).

- [ ] **Step 3: Write minimal implementation**

Create `wiki/tools/check_sync.py`:

```python
#!/usr/bin/env -S uv run --script
"""Staleness checker for the PyNGL knowledge wiki.

Every page under wiki/ carries YAML frontmatter listing the source globs it
describes (``sources``) and the commit its content was last verified against
(``synced``). This script reports pages whose sources changed since that
commit (STALE), pages with broken metadata (ERROR), and src/ files covered by
no page (UNTRACKED). Stdlib only.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


class FrontmatterError(Exception):
    """Raised when a wiki page's frontmatter is missing or malformed."""


@dataclass
class Frontmatter:
    """Parsed wiki-page frontmatter.

    Attributes:
        sources: Glob patterns (repo-relative) for the files the page describes.
        synced: Commit hash the page content was last verified against.
    """

    sources: list[str]
    synced: str


def parse_frontmatter(text: str) -> Frontmatter:
    """Parse the YAML frontmatter block of a wiki page.

    Only the minimal subset used by the wiki is supported: a ``sources`` key
    holding a list of strings and a scalar ``synced`` key, between ``---``
    delimiters at the top of the file.

    Args:
        text: Full text of the wiki page.

    Returns:
        The parsed frontmatter.

    Raises:
        FrontmatterError: If the block or either required key is missing.
    """
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        raise FrontmatterError("page does not start with a '---' frontmatter block")
    try:
        end = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == "---")
    except StopIteration:
        raise FrontmatterError("frontmatter block is never closed with '---'") from None

    sources: list[str] = []
    synced = ""
    in_sources = False
    for line in lines[1:end]:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped == "sources:":
            in_sources = True
        elif in_sources and stripped.startswith("- "):
            sources.append(stripped[2:].strip().strip("'\""))
        elif stripped.startswith("synced:"):
            in_sources = False
            synced = stripped.removeprefix("synced:").strip().strip("'\"")
        else:
            in_sources = False

    if not sources:
        raise FrontmatterError("frontmatter has no 'sources' list")
    if not synced:
        raise FrontmatterError("frontmatter has no 'synced' commit")
    return Frontmatter(sources=sources, synced=synced)


def glob_to_regex(pattern: str) -> re.Pattern[str]:
    """Compile a repo-relative glob pattern to a regex over posix paths.

    ``*`` and ``?`` do not cross ``/``; ``**`` matches across directories and
    ``**/`` also matches zero directories.

    Args:
        pattern: Glob pattern, e.g. ``src/ncca/ngl/vec*.py``.

    Returns:
        Compiled regex matching whole repo-relative posix paths.
    """
    out: list[str] = []
    i = 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:.*/)?")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_wiki_check_sync.py -v`
Expected: all PASS.

- [ ] **Step 5: Full suite + lint, then commit**

Run: `uv run pytest` (expect 503+ passed) and `uv run ruff check wiki/ tests/test_wiki_check_sync.py` (expect clean; fix anything it flags).

```bash
git add wiki/tools/check_sync.py tests/test_wiki_check_sync.py
git commit -m "feat(wiki): frontmatter parsing and glob matching for staleness checker"
```

---

### Task 2: `check_sync.py` — git staleness and coverage checks

**Files:**
- Modify: `wiki/tools/check_sync.py` (append functions)
- Test: `tests/test_wiki_check_sync.py` (append tests)

**Interfaces:**
- Consumes: `parse_frontmatter`, `glob_to_regex`, `Frontmatter`, `FrontmatterError` from Task 1.
- Produces: `PageStatus` dataclass (`path: Path`, `state: str` in `{"fresh", "stale", "error"}`, `changed: list[str]`, `message: str`, `frontmatter: Frontmatter | None`); `check_page(repo_root: Path, page: Path) -> PageStatus`; `find_untracked(repo_root: Path, patterns: list[str]) -> list[str]`. Task 3 builds the CLI on these.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_wiki_check_sync.py` (add `import subprocess` at the top):

```python
def _git(repo: Path, *args: str) -> str:
    return subprocess.run(
        ["git", "-C", str(repo), *args], capture_output=True, text=True, check=True
    ).stdout


@pytest.fixture
def wiki_repo(tmp_path):
    """A temp git repo with one src file and one fresh wiki page."""
    _git(tmp_path, "init", "-b", "main")
    _git(tmp_path, "config", "user.email", "test@example.com")
    _git(tmp_path, "config", "user.name", "Test")
    src = tmp_path / "src" / "ncca" / "ngl"
    src.mkdir(parents=True)
    (src / "vec3.py").write_text("x = 1\n")
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "initial")
    head = _git(tmp_path, "rev-parse", "HEAD").strip()
    wiki = tmp_path / "wiki" / "modules"
    wiki.mkdir(parents=True)
    (wiki / "math.md").write_text(
        f"---\nsources:\n  - src/ncca/ngl/vec*.py\nsynced: {head}\n---\n# Math\n"
    )
    _git(tmp_path, "add", ".")
    _git(tmp_path, "commit", "-m", "add wiki page")
    return tmp_path


class TestCheckPage:
    def test_fresh_when_sources_unchanged(self, wiki_repo):
        status = check_sync.check_page(wiki_repo, wiki_repo / "wiki" / "modules" / "math.md")
        assert status.state == "fresh"
        assert status.changed == []

    def test_stale_when_source_changes_after_sync(self, wiki_repo):
        (wiki_repo / "src" / "ncca" / "ngl" / "vec3.py").write_text("x = 2\n")
        _git(wiki_repo, "commit", "-am", "change vec3")
        status = check_sync.check_page(wiki_repo, wiki_repo / "wiki" / "modules" / "math.md")
        assert status.state == "stale"
        assert status.changed == ["src/ncca/ngl/vec3.py"]

    def test_fresh_when_unrelated_file_changes(self, wiki_repo):
        (wiki_repo / "README.md").write_text("hello\n")
        _git(wiki_repo, "add", ".")
        _git(wiki_repo, "commit", "-m", "add readme")
        status = check_sync.check_page(wiki_repo, wiki_repo / "wiki" / "modules" / "math.md")
        assert status.state == "fresh"

    def test_error_on_unknown_synced_commit(self, wiki_repo):
        page = wiki_repo / "wiki" / "modules" / "math.md"
        page.write_text("---\nsources:\n  - src/ncca/ngl/vec*.py\nsynced: " + "0" * 40 + "\n---\n")
        status = check_sync.check_page(wiki_repo, page)
        assert status.state == "error"
        assert "commit" in status.message

    def test_error_on_malformed_frontmatter(self, wiki_repo):
        page = wiki_repo / "wiki" / "modules" / "math.md"
        page.write_text("# no frontmatter\n")
        status = check_sync.check_page(wiki_repo, page)
        assert status.state == "error"


class TestFindUntracked:
    def test_reports_src_file_matched_by_no_pattern(self, wiki_repo):
        (wiki_repo / "src" / "ncca" / "ngl" / "quaternion.py").write_text("q = 1\n")
        _git(wiki_repo, "add", ".")
        _git(wiki_repo, "commit", "-m", "add quaternion")
        untracked = check_sync.find_untracked(wiki_repo, ["src/ncca/ngl/vec*.py"])
        assert untracked == ["src/ncca/ngl/quaternion.py"]

    def test_empty_when_everything_covered(self, wiki_repo):
        untracked = check_sync.find_untracked(wiki_repo, ["src/**"])
        assert untracked == []
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_wiki_check_sync.py -v -k "CheckPage or FindUntracked"`
Expected: FAIL with `AttributeError: module 'check_sync' has no attribute 'check_page'`.

- [ ] **Step 3: Write minimal implementation**

Append to `wiki/tools/check_sync.py` (extend the imports at the top with `import subprocess`, `from dataclasses import dataclass, field`, `from pathlib import Path`):

```python
@dataclass
class PageStatus:
    """Sync status of one wiki page.

    Attributes:
        path: Path to the page file.
        state: One of ``"fresh"``, ``"stale"``, ``"error"``.
        changed: Repo-relative source files changed since the synced commit.
        message: Human-readable detail for error states.
        frontmatter: Parsed frontmatter, or None when parsing failed.
    """

    path: Path
    state: str
    changed: list[str] = field(default_factory=list)
    message: str = ""
    frontmatter: Frontmatter | None = None


def _git(repo_root: Path, *args: str) -> str:
    """Run a git command in the repo and return its stdout.

    Args:
        repo_root: Repository root directory.
        *args: Git subcommand and arguments.

    Returns:
        Captured stdout.

    Raises:
        subprocess.CalledProcessError: If git exits non-zero.
    """
    result = subprocess.run(
        ["git", "-C", str(repo_root), *args],
        capture_output=True,
        text=True,
        check=True,
    )
    return result.stdout


def _commit_exists(repo_root: Path, ref: str) -> bool:
    """Return True if ``ref`` resolves to a commit in the repository.

    Args:
        repo_root: Repository root directory.
        ref: Commit hash or ref name.

    Returns:
        Whether the commit exists.
    """
    result = subprocess.run(
        ["git", "-C", str(repo_root), "cat-file", "-e", f"{ref}^{{commit}}"],
        capture_output=True,
    )
    return result.returncode == 0


def check_page(repo_root: Path, page: Path) -> PageStatus:
    """Determine whether a wiki page is fresh, stale, or broken.

    Args:
        repo_root: Repository root directory.
        page: Path to the wiki page.

    Returns:
        The page's sync status; STALE lists the source files that changed
        between the page's ``synced`` commit and HEAD.
    """
    try:
        fm = parse_frontmatter(page.read_text(encoding="utf-8"))
    except FrontmatterError as err:
        return PageStatus(path=page, state="error", message=str(err))
    if not _commit_exists(repo_root, fm.synced):
        return PageStatus(
            path=page,
            state="error",
            message=f"synced commit {fm.synced} not found in repository",
            frontmatter=fm,
        )
    out = _git(repo_root, "diff", "--name-only", f"{fm.synced}..HEAD", "--", *fm.sources)
    changed = [line for line in out.splitlines() if line]
    state = "stale" if changed else "fresh"
    return PageStatus(path=page, state=state, changed=changed, frontmatter=fm)


def find_untracked(repo_root: Path, patterns: list[str]) -> list[str]:
    """Find tracked ``src/`` files matched by no page's source patterns.

    Args:
        repo_root: Repository root directory.
        patterns: All ``sources`` globs collected from every wiki page.

    Returns:
        Sorted repo-relative paths of uncovered ``src/`` files.
    """
    regexes = [glob_to_regex(p) for p in patterns]
    files = [line for line in _git(repo_root, "ls-files", "src/").splitlines() if line]
    return sorted(f for f in files if not any(r.match(f) for r in regexes))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_wiki_check_sync.py -v`
Expected: all PASS (Task 1 tests included).

- [ ] **Step 5: Full suite + lint, then commit**

Run: `uv run pytest` and `uv run ruff check wiki/ tests/test_wiki_check_sync.py`.

```bash
git add wiki/tools/check_sync.py tests/test_wiki_check_sync.py
git commit -m "feat(wiki): git staleness and src coverage checks"
```

---

### Task 3: `check_sync.py` — CLI, report output, exit codes

**Files:**
- Modify: `wiki/tools/check_sync.py` (append CLI)
- Test: `tests/test_wiki_check_sync.py` (append tests)

**Interfaces:**
- Consumes: `check_page`, `find_untracked`, `PageStatus` from Task 2.
- Produces: `collect_pages(wiki_dir: Path) -> list[Path]`; `main(argv: list[str] | None = None) -> int` accepting `--wiki-dir PATH`, `--repo-root PATH`, `--json`. Exit 0 all fresh, 1 any stale/error. The `/wiki` skill (Task 4) calls `uv run wiki/tools/check_sync.py [--json]`.

- [ ] **Step 1: Write the failing tests**

Append to `tests/test_wiki_check_sync.py` (add `import json` at the top):

```python
class TestCli:
    def _run(self, repo, *extra):
        argv = ["--repo-root", str(repo), "--wiki-dir", str(repo / "wiki"), *extra]
        return check_sync.main(argv)

    def test_exit_zero_and_fresh_report_when_clean(self, wiki_repo, capsys):
        assert self._run(wiki_repo) == 0
        out = capsys.readouterr().out
        assert "FRESH" in out and "wiki/modules/math.md" in out

    def test_exit_one_and_stale_report_when_source_changed(self, wiki_repo, capsys):
        (wiki_repo / "src" / "ncca" / "ngl" / "vec3.py").write_text("x = 3\n")
        _git(wiki_repo, "commit", "-am", "change vec3")
        assert self._run(wiki_repo) == 1
        out = capsys.readouterr().out
        assert "STALE" in out and "src/ncca/ngl/vec3.py" in out

    def test_untracked_files_reported_but_do_not_fail(self, wiki_repo, capsys):
        (wiki_repo / "src" / "ncca" / "ngl" / "quaternion.py").write_text("q = 1\n")
        _git(wiki_repo, "add", ".")
        _git(wiki_repo, "commit", "-m", "add quaternion")
        assert self._run(wiki_repo) == 0
        assert "UNTRACKED src/ncca/ngl/quaternion.py" in capsys.readouterr().out

    def test_json_output(self, wiki_repo, capsys):
        (wiki_repo / "src" / "ncca" / "ngl" / "vec3.py").write_text("x = 3\n")
        _git(wiki_repo, "commit", "-am", "change vec3")
        assert self._run(wiki_repo, "--json") == 1
        data = json.loads(capsys.readouterr().out)
        assert data["pages"][0]["state"] == "stale"
        assert data["pages"][0]["path"] == "wiki/modules/math.md"
        assert data["pages"][0]["changed"] == ["src/ncca/ngl/vec3.py"]
        assert data["untracked"] == []

    def test_tools_dir_and_index_are_scanned_but_tools_excluded(self, wiki_repo):
        tools = wiki_repo / "wiki" / "tools"
        tools.mkdir()
        (tools / "README.md").write_text("# not a wiki page\n")
        pages = check_sync.collect_pages(wiki_repo / "wiki")
        assert pages == [wiki_repo / "wiki" / "modules" / "math.md"]
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_wiki_check_sync.py -v -k Cli`
Expected: FAIL with `AttributeError: module 'check_sync' has no attribute 'main'`.

- [ ] **Step 3: Write minimal implementation**

Append to `wiki/tools/check_sync.py` (extend imports with `import argparse`, `import json`, `import sys`):

```python
def collect_pages(wiki_dir: Path) -> list[Path]:
    """Collect all wiki pages, excluding the tools directory.

    Args:
        wiki_dir: Root of the wiki tree.

    Returns:
        Sorted paths of every ``*.md`` page under ``wiki_dir``.
    """
    tools_dir = wiki_dir / "tools"
    return sorted(p for p in wiki_dir.rglob("*.md") if tools_dir not in p.parents)


def main(argv: list[str] | None = None) -> int:
    """Check every wiki page for staleness and report the results.

    Args:
        argv: Command-line arguments; defaults to ``sys.argv[1:]``.

    Returns:
        0 when every page is fresh, 1 when any page is stale or in error.
    """
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wiki-dir", type=Path, default=Path(__file__).resolve().parent.parent)
    parser.add_argument("--repo-root", type=Path, default=None)
    parser.add_argument("--json", action="store_true", dest="as_json")
    args = parser.parse_args(argv)

    repo_root = args.repo_root or Path(
        _git(args.wiki_dir, "rev-parse", "--show-toplevel").strip()
    )
    statuses = [check_page(repo_root, page) for page in collect_pages(args.wiki_dir)]
    patterns = [p for s in statuses if s.frontmatter for p in s.frontmatter.sources]
    untracked = find_untracked(repo_root, patterns)

    if args.as_json:
        print(
            json.dumps(
                {
                    "pages": [
                        {
                            "path": s.path.relative_to(repo_root).as_posix(),
                            "state": s.state,
                            "changed": s.changed,
                            "message": s.message,
                            "synced": s.frontmatter.synced if s.frontmatter else None,
                        }
                        for s in statuses
                    ],
                    "untracked": untracked,
                },
                indent=2,
            )
        )
    else:
        for s in statuses:
            rel = s.path.relative_to(repo_root).as_posix()
            if s.state == "fresh":
                print(f"FRESH {rel}")
            elif s.state == "stale":
                print(f"STALE {rel} — {len(s.changed)} changed since {s.frontmatter.synced[:7]}:")
                for f in s.changed:
                    print(f"    {f}")
            else:
                print(f"ERROR {rel} — {s.message}")
        for f in untracked:
            print(f"UNTRACKED {f} — matched by no page's sources")

    return 1 if any(s.state in ("stale", "error") for s in statuses) else 0


if __name__ == "__main__":
    sys.exit(main())
```

Also run `chmod +x wiki/tools/check_sync.py`.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_wiki_check_sync.py -v`
Expected: all PASS.

- [ ] **Step 5: Full suite + lint, then commit**

Run: `uv run pytest` and `uv run ruff check wiki/ tests/test_wiki_check_sync.py`.

```bash
git add wiki/tools/check_sync.py tests/test_wiki_check_sync.py
git commit -m "feat(wiki): check_sync CLI with report, json output, and exit codes"
```

---

### Task 4: The `/wiki` project skill

**Files:**
- Create: `.claude/skills/wiki/SKILL.md`

**Interfaces:**
- Consumes: `uv run wiki/tools/check_sync.py [--json]` from Task 3.
- Produces: the `/wiki` command with `status` / `update` / `build [page]` modes; the page-format rules Task 5's generation subagents must follow.

- [ ] **Step 1: Write the skill file**

Create `.claude/skills/wiki/SKILL.md`:

```markdown
---
name: wiki
description: Maintain the PyNGL knowledge wiki (wiki/). Use for /wiki status (report stale pages), /wiki update (refresh stale pages), /wiki build [page] (regenerate pages from source). Also use after any change to the public API or module layout to keep the wiki in sync.
---

# PyNGL Knowledge Wiki Maintenance

The `wiki/` directory is an agent-maintained knowledge base about how PyNGL
works, written for both humans and coding agents. Every page's frontmatter
records which source files it describes (`sources`) and the commit it was
last verified against (`synced`). The staleness checker is the single
source of truth for what needs updating:

    uv run wiki/tools/check_sync.py          # human report
    uv run wiki/tools/check_sync.py --json   # machine-readable

Exit code 0 = all fresh; 1 = something stale or in error.

## Modes

Parse the argument after `/wiki`:

### `/wiki status`

Run the checker and relay the report: which pages are STALE (and which
source files changed), which are in ERROR, which src/ files are UNTRACKED
(covered by no page). Make no edits.

### `/wiki update`

1. Run the checker with `--json`.
2. For each STALE page:
   - Read the page.
   - Run `git diff <synced>..HEAD -- <sources...>` (the page's own values)
     to see exactly what changed.
   - Read the current source files that changed.
   - Rewrite only the parts of the page the changes invalidate. Do not
     rewrite prose that is still accurate.
   - Set `synced` to the current full HEAD hash (`git rev-parse HEAD`).
3. For each ERROR page: fix the frontmatter (usually a bad `synced` hash —
   re-verify the page against current sources, then set `synced` to HEAD).
4. For UNTRACKED files: either add them to the most relevant existing
   page's `sources` (and document them) or note that a new page is needed.
5. If more than ~4 pages are stale, fan out one subagent per page instead
   of updating inline; give each subagent the page path, its changed
   files, and the Page Format rules below.
6. Re-run the checker; it must exit 0 before you finish.

### `/wiki build [page]`

Full regeneration of one page (by path) or every page listed in
`wiki/index.md`. Dispatch one subagent per page. Each subagent must:
read the page's source files in full, follow the Page Format below, and
set `synced` to the current full HEAD hash. After all pages are built,
run the checker (must exit 0) and update `wiki/index.md`'s page map if
pages were added or removed.

## Page Format (all modes must preserve this)

Frontmatter, then four sections:

    ---
    sources:
      - src/ncca/ngl/vec*.py          # repo-relative globs; * stays within
      - tests/test_api_consistency.py # a directory, ** crosses directories
    synced: <full 40-char commit hash>
    ---

    # <Page Title>

    ## Summary
    One paragraph: what this part of the system is for.

    ## How it works
    The narrative: data flow, class relationships, lifecycle.

    ## Key invariants
    Bulleted facts an agent must not violate when editing this code
    (e.g. "`_data` is always `np.float32`").

    ## Connections
    Relative links to related wiki pages.

## Style rules

- Point at code with `path` / `path:symbol` references; never paste code
  blocks longer than 3 lines — pasted code rots.
- State invariants and contracts, not line-by-line narration.
- Keep each page short enough to load whole as context (~150 lines max).
- British "colour" spelling, per project convention.
- When a module is added/renamed/removed, update the affected page's
  `sources` list and `wiki/index.md`'s page map in the same change.
```

- [ ] **Step 2: Verify the skill file**

Run: `uv run wiki/tools/check_sync.py; echo "exit: $?"`
Expected: no pages yet, so no output and `exit: 0`. Confirm the SKILL.md frontmatter has `name` and `description` keys and the file is valid markdown (read it back).

- [ ] **Step 3: Commit**

```bash
git add .claude/skills/wiki/SKILL.md
git commit -m "feat(wiki): add /wiki project skill for status, update, and build"
```

---

### Task 5: Initial wiki build

**Files:**
- Create: `wiki/index.md`
- Create: `wiki/architecture/overview.md`, `wiki/architecture/api-conventions.md`, `wiki/architecture/test-architecture.md`
- Create: `wiki/modules/math.md`, `wiki/modules/geometry.md`, `wiki/modules/vao-stack.md`, `wiki/modules/shaders.md`, `wiki/modules/webgpu.md`, `wiki/modules/widgets.md`
- Create: `wiki/decisions.md`, `wiki/gotchas.md`
- Create: `wiki/howto/add-a-vao-type.md`, `wiki/howto/add-a-webgpu-pipeline.md`, `wiki/howto/add-a-primitive.md`

**Interfaces:**
- Consumes: the Page Format and style rules from `.claude/skills/wiki/SKILL.md` (Task 4); `uv run wiki/tools/check_sync.py` (Task 3).
- Produces: the complete initial wiki, checker-clean.

This task is agent-generation work, not fixed code, so steps prescribe the process and acceptance checks rather than page text.

- [ ] **Step 1: Write `wiki/index.md`**

Content: what the wiki is (agent-maintained knowledge base, complements the MkDocs API reference), the full page map as a nested list of relative links (all 14 pages above), and maintenance instructions ("run `/wiki status`; see `.claude/skills/wiki/SKILL.md`"). Frontmatter for the index: `sources: ["CLAUDE.md"]` (it summarises project structure; it must not list `wiki/**`, which would be self-referential) and current full HEAD hash for `synced`.

- [ ] **Step 2: Generate the 14 content pages via subagents**

Dispatch one subagent per page (batch 3–4 at a time). Each subagent prompt must contain: the target page path; the page's `sources` globs (below); the full Page Format and Style rules copied from SKILL.md; the instruction to read every matched source file before writing; and the current full HEAD hash for `synced`.

Sources per page:

| Page | sources |
|---|---|
| architecture/overview.md | `src/ncca/ngl/__init__.py`, `src/ncca/ngl/opengl/__init__.py`, `src/ncca/ngl/webgpu/__init__.py`, `src/ncca/ngl/widgets/__init__.py`, `pyproject.toml` |
| architecture/api-conventions.md | `tests/test_api_consistency.py`, `CLAUDE.md` |
| architecture/test-architecture.md | `tests/conftest.py`, `run_coverage_nogpu.py`, `pyproject.toml` |
| modules/math.md | `src/ncca/ngl/vec*.py`, `src/ncca/ngl/mat*.py`, `src/ncca/ngl/quaternion.py`, `src/ncca/ngl/transform.py`, `src/ncca/ngl/util.py` |
| modules/geometry.md | `src/ncca/ngl/prim_data.py`, `src/ncca/ngl/obj.py`, `src/ncca/ngl/bezier_curve.py`, `src/ncca/ngl/plane.py`, `src/ncca/ngl/bbox.py` |
| modules/vao-stack.md | `src/ncca/ngl/opengl/*vao*.py`, `src/ncca/ngl/opengl/primitives.py`, `src/ncca/ngl/opengl/base_mesh.py` |
| modules/shaders.md | `src/ncca/ngl/opengl/shader*.py`, `src/ncca/ngl/opengl/text.py`, `src/ncca/ngl/opengl/texture.py`, `src/ncca/ngl/opengl/shaders/**` |
| modules/webgpu.md | `src/ncca/ngl/webgpu/**` |
| modules/widgets.md | `src/ncca/ngl/widgets/**`, `src/ncca/ngl/opengl/pyside_event_handling_mixin.py`, `src/ncca/ngl/first_person_camera.py` |
| decisions.md | `CLAUDE.md`, `tests/test_api_consistency.py` |
| gotchas.md | `tests/conftest.py`, `CLAUDE.md`, `.github/workflows/**` |
| howto/add-a-vao-type.md | `src/ncca/ngl/opengl/vao_factory.py`, `src/ncca/ngl/opengl/abstract_vao.py`, `src/ncca/ngl/opengl/simple_vao.py` |
| howto/add-a-webgpu-pipeline.md | `src/ncca/ngl/webgpu/pipeline_factory.py`, `src/ncca/ngl/webgpu/base_webgpu_pipeline.py`, `src/ncca/ngl/webgpu/line_pipeline.py` |
| howto/add-a-primitive.md | `src/ncca/ngl/prim_data.py`, `src/ncca/ngl/opengl/primitives.py` |

The remaining top-level modules — `src/ncca/ngl/image.py`, `src/ncca/ngl/random.py`, `src/ncca/ngl/log.py` — are covered by adding a short **Other utilities** section to `architecture/overview.md` and including those three files in its `sources` (`first_person_camera.py` is already in the widgets page). Every `src/` file must be matched by some page or the checker reports UNTRACKED.

- [ ] **Step 3: Verify with the checker**

Run: `uv run wiki/tools/check_sync.py; echo "exit: $?"`
Expected: every page FRESH, `exit: 0`, and **zero UNTRACKED lines**. If UNTRACKED files appear, extend the appropriate page's `sources` (and its content) until none remain.

- [ ] **Step 4: Accuracy review pass**

For each generated page, spot-check every stated invariant and file reference against the code (open the referenced file; confirm the claim). Fix inaccuracies. This is the step that catches subagent hallucination — do not skip it.

- [ ] **Step 5: Full suite, lint, commit**

Run: `uv run pytest` and `uv run ruff check wiki/`.

```bash
git add wiki/
git commit -m "docs(wiki): initial knowledge wiki build"
```

---

## After the plan

Merge/PR per `superpowers:finishing-a-development-branch`; the wiki and skill land together. Follow-up ideas deliberately out of scope (spec non-goals): MkDocs integration, CI freshness gate.
