import numpy as np
import pytest

from ncca.ngl.webgpu import WebGPUWidget


class _RinglessWidget(WebGPUWidget):
    """Concrete widget that never creates the read-back ring, standing in for
    a subclass that overrides _create_render_buffer() and forgets to build it
    (or to call super())."""

    def paintWebGPU(self) -> None:  # pragma: no cover - not exercised here
        pass

    def resizeWebGPU(self, width: int, height: int) -> None:  # pragma: no cover
        pass


def test_update_colour_buffer_without_ring_raises(qt_app, qtbot):
    """_update_colour_buffer must fail loudly when the read-back ring was
    never created, instead of swallowing an AttributeError every frame."""
    widget = _RinglessWidget()
    qtbot.addWidget(widget)

    assert getattr(widget, "readback_buffers", None) is None
    with pytest.raises(RuntimeError, match="read-back ring is not initialised"):
        widget._update_colour_buffer()


def test_update_colour_buffer_error_is_logged_not_printed(qt_app, qtbot, caplog):
    """Once the ring exists, a failure in the copy-back is logged with a
    traceback rather than silently swallowed."""
    widget = _RinglessWidget()
    qtbot.addWidget(widget)

    # Minimal ring so the guard passes; the copy-back then fails because there
    # is no real device/texture behind it.
    widget.readback_buffers = [object()]
    widget._readback_index = 0
    widget._readback_pending = [False]
    widget.frame_buffer = np.zeros((4, 4, 4), dtype=np.uint8)

    with caplog.at_level("ERROR"):
        widget._update_colour_buffer()

    assert "Failed to update colour buffer" in caplog.text
    # the fallback grey fill was applied
    assert np.all(widget.frame_buffer == 128)
