"""Tests for the wiki staleness checker (wiki/tools/check_sync.py)."""

import importlib.util
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
