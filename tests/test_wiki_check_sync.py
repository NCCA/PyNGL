"""Tests for the wiki staleness checker (wiki/tools/check_sync.py)."""

import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_MODULE_PATH = Path(__file__).resolve().parent.parent / "wiki" / "tools" / "check_sync.py"
_spec = importlib.util.spec_from_file_location("check_sync", _MODULE_PATH)
check_sync = importlib.util.module_from_spec(_spec)
sys.modules["check_sync"] = check_sync
_spec.loader.exec_module(check_sync)


class TestParseFrontmatter:
    def test_parses_sources_and_synced(self):
        text = (
            "---\n"
            "sources:\n"
            "  - src/ncca/ngl/vec*.py\n"
            "  - tests/test_api_consistency.py\n"
            "synced: 112100b112100b112100b112100b11221\n"
            "---\n"
            "# Page body\n"
        )
        fm = check_sync.parse_frontmatter(text)
        assert fm.sources == ["src/ncca/ngl/vec*.py", "tests/test_api_consistency.py"]
        assert fm.synced == "112100b112100b112100b112100b11221"

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
