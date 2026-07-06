"""Pillow-backed image loading, saving, and pixel manipulation."""

from __future__ import annotations

import logging
from enum import Enum

import numpy as np
from PIL import Image as PILImage

logger = logging.getLogger(__name__)


class ImageModes(Enum):
    """Supported image colour modes, matching PIL mode strings."""

    RGB = "RGB"
    RGBA = "RGBA"
    GRAY = "L"


class Image:
    """An image class for loading, saving, and manipulating pixel data.

    Uses Pillow for file I/O and stores pixel data as a numpy uint8 array.
    """

    def __init__(
        self,
        filename: str | None = None,
        width: int = 0,
        height: int = 0,
        mode: ImageModes | None = None,
    ) -> None:
        """Create an image, either from a file or as a blank canvas.

        Args:
            filename: Path of an image to load; takes precedence if given.
            width: Width of the blank image when no filename is given.
            height: Height of the blank image when no filename is given.
            mode: Colour mode for the blank image; data is None if omitted.
        """
        if filename:
            self.load(filename)
            logger.debug(f"Creating Image from file {filename} ")
        else:
            self._width = width
            self._height = height
            self._mode = mode
            if mode:
                if mode == ImageModes.GRAY:
                    self._data = np.zeros((height, width), dtype=np.uint8)
                else:
                    self._data = np.zeros(
                        (height, width, len(mode.value)), dtype=np.uint8
                    )
            else:
                self._data = None

    def set_pixel(self, x: int, y: int, r: int, g: int, b: int, a: int = 255) -> None:
        """Set the pixel at (x, y) to the given colour.

        Args:
            x: Pixel x coordinate.
            y: Pixel y coordinate.
            r: Red component (0-255).
            g: Green component (0-255).
            b: Blue component (0-255).
            a: Alpha component (0-255), used only in RGBA mode.

        Raises:
            ValueError: If the coordinates are out of bounds.
        """
        if x < 0 or x >= self._width or y < 0 or y >= self._height:
            raise ValueError("Pixel coordinates out of bounds")
        if self._mode == ImageModes.RGBA:
            self._data[y, x] = [r, g, b, a]
        else:
            self._data[y, x] = [r, g, b]

    def load(self, filename: str) -> bool:
        """Load an image from file, converting unsupported modes.

        Returns:
            bool: True on success, False if loading failed.
        """
        try:
            with PILImage.open(filename) as img:
                self._width = img.width
                self._height = img.height
                try:
                    self._mode = ImageModes(img.mode)
                except ValueError:
                    logger.warning(f"Image mode {img.mode} not supported, converting")
                    if img.mode == "I;16":
                        img = img.convert("L")
                    else:
                        img = img.convert("RGB")
                    self._mode = ImageModes(img.mode)

                self._data = np.array(img)
            return True
        except Exception as e:
            logger.error(f"Error loading image {filename}: {e}")
            return False

    def save(self, filename: str) -> bool:
        """Save the image to file, format inferred from the extension.

        Returns:
            bool: True on success, False if saving failed.
        """
        try:
            img = PILImage.fromarray(self._data).convert(self._mode.value)
            img.save(filename)
            return True
        except Exception as e:
            logger.error(f"Error saving image {filename}: {e}")
            return False

    @property
    def width(self) -> int:
        """The image width in pixels."""
        return self._width

    @property
    def height(self) -> int:
        """The image height in pixels."""
        return self._height

    @property
    def mode(self) -> ImageModes:
        """The image colour mode."""
        return self._mode

    def get_pixels(self) -> np.ndarray:
        """Return the raw pixel data array."""
        return self._data
