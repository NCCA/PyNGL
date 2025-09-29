"""
Note opengl_context created once in conftest.py
"""

from ncca.ngl import Text


def test_text_constructor(opengl_context):
    Text.add_font("Arial", "tests/files/Arial.ttf", 20)
    assert Text._fonts.get("Arial") is not None

    Text.set_screen_size(10, 10)
    # assert text is not None
    # text.set_screen_size(800, 600)
    # assert text
