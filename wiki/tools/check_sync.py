#!/usr/bin/env -S uv run --script
"""Staleness checker for the PyNGL knowledge wiki.

Every page under wiki/ carries YAML frontmatter listing the source globs it
describes (``sources``) and the commit its content was last verified against
(``synced``). This script reports pages whose sources changed since that
commit (STALE), pages with broken metadata (ERROR), and src/ files covered by
no page (UNTRACKED). Stdlib only.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path


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
