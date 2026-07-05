"""
Note opengl_context created once in conftest.py
"""

from ncca.ngl.opengl import Text


def test_text_constructor(opengl_context):
    Text.add_font("Arial", "tests/files/Arial.ttf", 20)
    assert Text._fonts.get("Arial") is not None

    Text.set_screen_size(10, 10)
