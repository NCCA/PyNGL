import logging
from abc import ABCMeta, abstractmethod
from typing import List, Optional, Tuple, Union

import numpy as np
import wgpu
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor, QFont, QImage, QPainter
from PySide6.QtWidgets import QWidget

logger = logging.getLogger(__name__)

# The WebGPU spec mandates this alignment for copy_texture_to_buffer
# (COPY_BYTES_PER_ROW_ALIGNMENT). It is not a per-GPU quirk.
COPY_BYTES_PER_ROW_ALIGNMENT = 256

# Number of readback buffers in the ring. Two gives the GPU a full frame
# to complete each copy before we map it; bump to 3 if ever GPU-bound.
NUM_READBACK_BUFFERS = 2


class QWidgetABCMeta(ABCMeta, type(QWidget)):
    """
    A metaclass that combines the functionality of ABCMeta and QWidget's metaclass.

    This allows the creation of abstract base classes that are also QWidgets.
    """

    pass


class WebGPUWidget(QWidget, metaclass=QWidgetABCMeta):
    """
    An abstract base class for widgets that render WebGPU content offscreen
    and present it via QPainter.

    The scene is rendered to an offscreen texture, read back to a numpy
    buffer, and blitted to the widget with QPainter. This keeps the whole
    data flow visible and allows QPainter text overlays via render_text().

    The readback is pipelined through a small ring of buffers: each frame
    the current image is copied into one buffer while the *previous*
    frame's buffer is mapped and read. Mapping a buffer whose copy was
    submitted a frame ago returns almost immediately, so the CPU never
    stalls waiting for the GPU to drain. The presented image therefore
    lags the simulation by one frame, which is imperceptible at
    interactive rates.

    Subclasses must implement paintWebGPU() and resizeWebGPU(), and must
    set self.device to a wgpu device before any rendering can occur. The
    base class owns the render target textures and the readback machinery;
    resizeWebGPU() should only update subclass state (projection matrix,
    per-pipeline sizes etc.) and must NOT recreate render buffers itself.
    """

    def __init__(self) -> None:
        """
        Initialize the widget.

        Note the wgpu device is not created here; subclasses are
        responsible for creating it (self.device) before the first paint.
        """
        super().__init__()
        self.device: Optional[wgpu.GPUDevice] = None
        self.msaa_sample_count = 4
        self.text_buffer: List[Tuple[int, int, str, int, str, QColor]] = []
        self.frame_buffer: Optional[np.ndarray] = None
        self._update_timer = QTimer(self)
        self._update_timer.timeout.connect(self.update)
        # Device pixel ratio for high-DPI displays. This is re-queried on
        # resize and paint, as it changes when the window moves between
        # screens with different scale factors.
        self.ratio = self.devicePixelRatioF()
        self._initialize_buffer()

    # ------------------------------------------------------------------
    # Timer control
    # ------------------------------------------------------------------
    def start_update_timer(self, interval_ms: int) -> None:
        """
        Start the update timer with the given interval.

        Args:
            interval_ms (int): The interval in milliseconds.
        """
        self._update_timer.start(interval_ms)

    def stop_update_timer(self) -> None:
        """Stop the update timer."""
        self._update_timer.stop()

    # ------------------------------------------------------------------
    # Abstract interface
    # ------------------------------------------------------------------
    @abstractmethod
    def resizeWebGPU(self, width: int, height: int) -> None:
        """
        Called when the widget is resized, after the render buffers have
        been recreated at the new size.

        Subclasses should update projection matrices and any per-pipeline
        sizes here. Width and height are in device pixels.

        Args:
            width (int): New width in device pixels.
            height (int): New height in device pixels.
        """
        pass

    @abstractmethod
    def paintWebGPU(self) -> None:
        """
        Render the WebGPU content.

        Called on every paint event; all the main rendering code goes
        here. Implementations should end by calling
        _update_colour_buffer() so the rendered frame is read back for
        presentation.
        """
        pass

    # ------------------------------------------------------------------
    # Qt event handlers
    # ------------------------------------------------------------------
    def resizeEvent(self, event) -> None:
        """
        Handle window resize.

        Recreates the render targets and the readback frame buffer at the
        new size (in device pixels), then notifies the subclass via
        resizeWebGPU().
        """
        self.ratio = self.devicePixelRatioF()
        width = int(event.size().width() * self.ratio)
        height = int(event.size().height() * self.ratio)

        # A minimised or degenerate window gives a zero dimension, which
        # is a wgpu validation error - skip until we have a real size.
        if width <= 0 or height <= 0:
            return super().resizeEvent(event)

        self.texture_size = (width, height)
        self.frame_buffer = np.zeros([height, width, 4], dtype=np.uint8)

        if self.device is not None:
            self._create_render_buffer()
            self.resizeWebGPU(width, height)

        return super().resizeEvent(event)

    def paintEvent(self, event) -> None:
        """
        Handle the paint event to render and present the WebGPU content.
        """
        # The device pixel ratio can change without a resize when the
        # window moves between screens - rebuild render targets if it has.
        current_ratio = self.devicePixelRatioF()
        if current_ratio != self.ratio:
            self.ratio = current_ratio
            width = int(self.width() * self.ratio)
            height = int(self.height() * self.ratio)
            if width > 0 and height > 0:
                self.texture_size = (width, height)
                self.frame_buffer = np.zeros([height, width, 4], dtype=np.uint8)
                if self.device is not None:
                    self._create_render_buffer()
                    self.resizeWebGPU(width, height)

        if self.device is not None:
            self.paintWebGPU()

        painter = QPainter(self)
        if self.frame_buffer is not None:
            self._present_image(painter, self.frame_buffer)

        # Draw any queued text. Font size is scaled relative to a base
        # window height so text keeps its proportions when resizing.
        base_height = 600.0
        scale_factor = self.height() / base_height
        for x, y, text, size, font, colour in self.text_buffer:
            scaled_size = int(size * scale_factor)
            painter.setPen(colour)
            painter.setFont(QFont(font, scaled_size))
            draw_y = y
            if y < 0:
                draw_y = self.height() + y
            painter.drawText(x, draw_y, text)
        self.text_buffer.clear()
        painter.end()

    # ------------------------------------------------------------------
    # Buffer / texture management
    # ------------------------------------------------------------------
    def _initialize_buffer(self) -> None:
        """
        Initialize the numpy buffer used for the final framebuffer render.
        """
        width = max(1, int(self.width() * self.ratio))
        height = max(1, int(self.height() * self.ratio))
        self.frame_buffer = np.zeros([height, width, 4], dtype=np.uint8)
        self.texture_size = (width, height)

    def _create_render_buffer(self) -> None:
        """
        Create the render target textures and the readback buffer ring.

        Requires self.device to be set. Called automatically on resize;
        subclasses should call it once after creating the device.
        Recreating the ring resets the pending flags, which conveniently
        discards any in-flight copy at the old size.
        """
        if self.device is None:
            raise RuntimeError("self.device must be set before creating render buffers")

        # The single-sample texture the MSAA render is resolved into, and
        # which is copied back to the CPU for presentation.
        self.colour_buffer_texture = self.device.create_texture(
            size=self.texture_size,
            sample_count=1,
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT | wgpu.TextureUsage.COPY_SRC,
        )
        self.colour_buffer_texture_view = self.colour_buffer_texture.create_view()

        # The multisampled texture that is actually rendered to.
        self.multisample_texture = self.device.create_texture(
            size=self.texture_size,
            sample_count=self.msaa_sample_count,
            format=wgpu.TextureFormat.rgba8unorm,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT,
        )
        self.multisample_texture_view = self.multisample_texture.create_view()

        # Depth buffer (multisampled to match). Keep an explicit reference
        # to the texture as well as the view so ownership is obvious.
        self.depth_buffer_texture = self.device.create_texture(
            size=self.texture_size,
            format=wgpu.TextureFormat.depth24plus,
            usage=wgpu.TextureUsage.RENDER_ATTACHMENT,
            sample_count=self.msaa_sample_count,
        )
        self.depth_buffer_view = self.depth_buffer_texture.create_view()

        # Ring of buffers for reading the resolved texture back to the
        # CPU. Rows are padded to the spec-mandated 256 byte alignment.
        buffer_size = self._calculate_aligned_buffer_size()
        self.readback_buffers = [
            self.device.create_buffer(
                size=buffer_size,
                usage=wgpu.BufferUsage.COPY_DST | wgpu.BufferUsage.MAP_READ,
                label=f"readback_buffer_{i}",
            )
            for i in range(NUM_READBACK_BUFFERS)
        ]
        # Index of the buffer the next copy will go into, and per-buffer
        # flags recording whether it holds a frame we haven't read yet.
        self._readback_index = 0
        self._readback_pending = [False] * NUM_READBACK_BUFFERS

    def render_text(
        self,
        x: int,
        y: int,
        text: str,
        size: int = 10,
        font: str = "Arial",
        colour: Union[QColor, Qt.GlobalColor] = Qt.black,
    ) -> None:
        """
        Queue text to be drawn over the rendered frame.

        The text buffer is cleared each frame, so text must be re-added
        every frame (typically from paintWebGPU or a timer callback).
        Note the rendered image lags the simulation by one frame due to
        the pipelined readback, so text meant to track a moving 3D
        object's screen position will swim slightly during fast motion;
        HUD-style labels are unaffected.

        Args:
            x (int): The x-coordinate of the text.
            y (int): The y-coordinate of the text. A negative value
                positions the text relative to the bottom of the window.
            text (str): The text to render.
            size (int, optional): Base font size, scaled with window
                height. Defaults to 10.
            font (str, optional): Font family. Defaults to "Arial".
            colour: Text colour. Defaults to Qt.black.
        """
        self.text_buffer.append((x, y, text, size, font, QColor(colour)))

    def _calculate_aligned_row_size(self) -> int:
        """
        Calculate the row stride for texture copy operations, padded to
        the WebGPU spec's COPY_BYTES_PER_ROW_ALIGNMENT (256 bytes).
        """
        bytes_per_pixel = 4  # rgba8unorm
        raw_row_size = self.texture_size[0] * bytes_per_pixel
        alignment = COPY_BYTES_PER_ROW_ALIGNMENT
        return ((raw_row_size + alignment - 1) // alignment) * alignment

    def _calculate_aligned_buffer_size(self) -> int:
        """
        Calculate the total readback buffer size (aligned row stride times
        the number of rows).
        """
        return self._calculate_aligned_row_size() * self.texture_size[1]

    def _update_colour_buffer(self) -> None:
        """
        Copy the resolved colour texture to a readback buffer, and read
        the *previous* frame's buffer into the numpy frame buffer.

        A buffer is only ever mapped when it is not the copy target, and
        is unmapped before it becomes the copy target again - the
        alternation guarantees this. The first frame after startup or a
        resize has nothing pending, so the previous frame buffer contents
        are shown once and everything flows from the next frame on.
        """
        # A subclass that overrides _create_render_buffer must still create the
        # read-back ring - easiest by calling super()._create_render_buffer().
        # Without it the copy-back below would raise AttributeError on the ring
        # attributes, which the try/except would swallow every single frame,
        # leaving a grey window and no obvious cause. Fail loudly instead.
        if not getattr(self, "readback_buffers", None):
            raise RuntimeError(
                "WebGPUWidget read-back ring is not initialised. A subclass that "
                "overrides _create_render_buffer() must call "
                "super()._create_render_buffer() (or otherwise create the "
                "readback_buffers ring) before rendering."
            )

        bytes_per_row = self._calculate_aligned_row_size()
        width, height = self.texture_size
        try:
            write_idx = self._readback_index
            read_idx = (write_idx + 1) % len(self.readback_buffers)

            # Kick off the copy of this frame. We do not wait for it.
            command_encoder = self.device.create_command_encoder()
            command_encoder.copy_texture_to_buffer(
                {"texture": self.colour_buffer_texture},
                {
                    "buffer": self.readback_buffers[write_idx],
                    "bytes_per_row": bytes_per_row,
                    "rows_per_image": height,
                },
                (width, height, 1),
            )
            self.device.queue.submit([command_encoder.finish()])
            self._readback_pending[write_idx] = True

            # Read back last frame's buffer, if it holds one. The map
            # returns almost immediately because the GPU has had a full
            # frame to complete that copy.
            if self._readback_pending[read_idx]:
                buf = self.readback_buffers[read_idx]
                buf.map_sync(mode=wgpu.MapMode.READ)
                raw_data = buf.read_mapped()

                # The raw data includes per-row padding to meet the
                # alignment requirement, so build a strided view and copy
                # it to a contiguous array before unmapping.
                strided_view = np.lib.stride_tricks.as_strided(
                    np.frombuffer(raw_data, dtype=np.uint8),
                    shape=(height, width, 4),
                    strides=(bytes_per_row, 4, 1),
                )
                self.frame_buffer = np.copy(strided_view)
                buf.unmap()
                self._readback_pending[read_idx] = False

            # Alternate: next frame writes into the buffer just drained.
            self._readback_index = read_idx
        except Exception:
            # A genuine (usually transient) GPU/mapping error - log it with a
            # traceback so it is visible, and fall back to a grey frame rather
            # than tearing down the event loop.
            logger.exception("Failed to update colour buffer")
            if self.frame_buffer is not None:
                self.frame_buffer.fill(128)

    def _present_image(self, painter: QPainter, image_data: np.ndarray) -> None:
        """
        Present the frame buffer on the widget.

        The image is tagged with the device pixel ratio so Qt blits it
        1:1 to the physical pixels rather than rescaling a
        device-pixel-sized image into a logical-pixel rect.

        Args:
            painter (QPainter): The active painter.
            image_data (np.ndarray): The image data to render.
        """
        height, width, _ = image_data.shape
        image = QImage(
            image_data.data,
            width,
            height,
            image_data.strides[0],
            QImage.Format.Format_RGBA8888,
        )
        image.setDevicePixelRatio(self.ratio)
        painter.drawImage(0, 0, image)
