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
