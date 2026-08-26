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


class _FakeBuffer:
    """Stands in for a wgpu read-back buffer, recording when it was mapped."""

    def __init__(self, size: int) -> None:
        self._size = size
        self.map_count = 0
        self.mapped = False

    def map_sync(self, mode) -> None:
        assert not self.mapped, "buffer mapped while already mapped"
        self.mapped = True
        self.map_count += 1

    def read_mapped(self) -> bytes:
        return bytes(self._size)

    def unmap(self) -> None:
        self.mapped = False


class _FakeEncoder:
    def __init__(self, log: list) -> None:
        self._log = log

    def copy_texture_to_buffer(self, source, destination, size) -> None:
        self._log.append(destination["buffer"])

    def finish(self):
        return object()


class _FakeQueue:
    def submit(self, command_buffers) -> None:
        pass


class _FakeDevice:
    """Enough of a wgpu device for _update_colour_buffer to run through."""

    def __init__(self) -> None:
        self.copied_into: list = []
        self.queue = _FakeQueue()

    def create_command_encoder(self):
        return _FakeEncoder(self.copied_into)


def _widget_with_fake_ring(qtbot, pipelined: bool) -> _RinglessWidget:
    """A widget wired to fake GPU objects so the copy-back path completes."""
    widget = _RinglessWidget()
    qtbot.addWidget(widget)
    widget.pipelined_readback = pipelined
    widget.device = _FakeDevice()
    widget.colour_buffer_texture = object()
    widget.texture_size = (4, 4)
    size = widget._calculate_aligned_buffer_size()
    widget.readback_buffers = [_FakeBuffer(size), _FakeBuffer(size)]
    widget._readback_index = 0
    widget._readback_pending = [False, False]
    widget.frame_buffer = np.zeros((4, 4, 4), dtype=np.uint8)
    return widget


def test_pipelined_readback_defaults_off(qt_app, qtbot):
    """The default must present the frame just drawn: a widget that only
    repaints on an event would otherwise never show the event's own frame."""
    widget = _RinglessWidget()
    qtbot.addWidget(widget)

    assert widget.pipelined_readback is False


def test_synchronous_readback_maps_the_frame_it_just_copied(qt_app, qtbot):
    """With pipelining off, the buffer read back is the one this frame was
    copied into, so the frame reaches the widget on its own paint."""
    widget = _widget_with_fake_ring(qtbot, pipelined=False)

    widget._update_colour_buffer()

    copied_into = widget.device.copied_into[-1]
    assert copied_into.map_count == 1
    assert copied_into is widget.readback_buffers[0]
    # nothing left in flight, and the same buffer serves the next frame
    assert widget._readback_pending == [False, False]
    assert widget._readback_index == 0

    widget._update_colour_buffer()
    assert widget.readback_buffers[0].map_count == 2
    assert widget.readback_buffers[1].map_count == 0


def test_pipelined_readback_maps_the_previous_frame(qt_app, qtbot):
    """With pipelining on, the first frame is copied but not read - the ring
    alternates and each frame maps its predecessor's buffer."""
    widget = _widget_with_fake_ring(qtbot, pipelined=True)

    widget._update_colour_buffer()
    # frame one is still in flight: copied into buffer 0, nothing mapped yet
    assert widget.readback_buffers[0].map_count == 0
    assert widget.readback_buffers[1].map_count == 0
    assert widget._readback_pending == [True, False]
    assert widget._readback_index == 1

    widget._update_colour_buffer()
    # frame two goes into buffer 1 and frame one is read back out of buffer 0
    assert widget.device.copied_into[-1] is widget.readback_buffers[1]
    assert widget.readback_buffers[0].map_count == 1
    assert widget._readback_pending == [False, True]
    assert widget._readback_index == 0


def test_readback_buffer_never_mapped_while_it_is_the_copy_target(qt_app, qtbot):
    """The invariant the ring rests on, checked over many frames in both
    modes: _FakeBuffer asserts on a double map, and a buffer must always be
    unmapped by the time it is written to again."""
    for pipelined in (False, True):
        widget = _widget_with_fake_ring(qtbot, pipelined=pipelined)
        for _ in range(10):
            widget._update_colour_buffer()
            target = widget.device.copied_into[-1]
            assert not target.mapped
