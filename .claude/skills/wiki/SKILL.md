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
