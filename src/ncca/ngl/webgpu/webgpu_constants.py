"""Constants and type mappings between NGL data types and WebGPU formats."""

import numpy as np


FLOAT_SIZE = np.dtype(np.float32).itemsize


class NGLToWebGPU:
    """Maps NGL type names to WebGPU strides and vertex formats."""

    _strides = {
        "vec2": 2 * FLOAT_SIZE,
        "vec3": 3 * FLOAT_SIZE,
        "vec4": 4 * FLOAT_SIZE,
        "mat2": 4 * FLOAT_SIZE,
        "mat3": 12 * FLOAT_SIZE,
        "mat4": 16 * FLOAT_SIZE,
    }
    _vertex_format = {
        "vec2": "float32x2",
        "vec3": "float32x3",
        "vec4": "float32x4",
    }

    @staticmethod
    def stride_from_type(type: str) -> int:
        """Return the byte stride for the given NGL type name."""
        return NGLToWebGPU._strides[type.lower()]

    @staticmethod
    def vertex_format(type: str) -> str:
        """Return the WebGPU vertex format for the given NGL type name."""
        return NGLToWebGPU._vertex_format[type.lower()]
