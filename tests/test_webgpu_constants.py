import pytest
import numpy as np
from ncca.ngl.webgpu.webgpu_constants import FLOAT_SIZE, NGLToWebGPU


class TestWebGPUConstants:
    """Test cases for WebGPU constants and conversion utilities."""

    def test_float_size_constant(self):
        """Test that FLOAT_SIZE is correctly calculated."""
        expected_size = np.dtype(np.float32).itemsize
        assert FLOAT_SIZE == expected_size
        assert FLOAT_SIZE == 4  # float32 should be 4 bytes

    def test_stride_calculations(self):
        """Test stride calculations for different data types."""
        # Test vector strides
        assert NGLToWebGPU.stride_from_type("vec2") == 2 * FLOAT_SIZE
        assert NGLToWebGPU.stride_from_type("vec3") == 3 * FLOAT_SIZE
        assert NGLToWebGPU.stride_from_type("vec4") == 4 * FLOAT_SIZE

        # Test matrix strides
        assert NGLToWebGPU.stride_from_type("mat2") == 4 * FLOAT_SIZE
        assert NGLToWebGPU.stride_from_type("mat3") == 12 * FLOAT_SIZE
        assert NGLToWebGPU.stride_from_type("mat4") == 16 * FLOAT_SIZE

    def test_stride_case_insensitive(self):
        """Test that stride_from_type handles case insensitive input."""
        assert NGLToWebGPU.stride_from_type("VEC2") == 2 * FLOAT_SIZE
        assert NGLToWebGPU.stride_from_type("Vec3") == 3 * FLOAT_SIZE
        assert NGLToWebGPU.stride_from_type("vEc4") == 4 * FLOAT_SIZE

    def test_vertex_format_conversions(self):
        """Test vertex format string conversions."""
        assert NGLToWebGPU.vertex_format("vec2") == "float32x2"
        assert NGLToWebGPU.vertex_format("vec3") == "float32x3"
        assert NGLToWebGPU.vertex_format("vec4") == "float32x4"

    def test_vertex_format_case_insensitive(self):
        """Test that vertex_format handles case insensitive input."""
        assert NGLToWebGPU.vertex_format("VEC2") == "float32x2"
        assert NGLToWebGPU.vertex_format("Vec3") == "float32x3"
        assert NGLToWebGPU.vertex_format("vEc4") == "float32x4"

    def test_stride_invalid_type(self):
        """Test that stride_from_type raises KeyError for invalid types."""
        with pytest.raises(KeyError):
            NGLToWebGPU.stride_from_type("invalid")

        with pytest.raises(KeyError):
            NGLToWebGPU.stride_from_type("vec5")  # Not supported

    def test_vertex_format_invalid_type(self):
        """Test that vertex_format raises KeyError for invalid types."""
        with pytest.raises(KeyError):
            NGLToWebGPU.vertex_format("invalid")

        with pytest.raises(KeyError):
            NGLToWebGPU.vertex_format(
                "mat2"
            )  # Only vectors supported for vertex format

    def test_stride_values_are_positive(self):
        """Test that all stride values are positive."""
        for type_name in ["vec2", "vec3", "vec4", "mat2", "mat3", "mat4"]:
            stride = NGLToWebGPU.stride_from_type(type_name)
            assert stride > 0
            assert isinstance(stride, int)

    def test_vertex_format_strings(self):
        """Test that vertex format strings have correct format."""
        formats = [
            NGLToWebGPU.vertex_format("vec2"),
            NGLToWebGPU.vertex_format("vec3"),
            NGLToWebGPU.vertex_format("vec4"),
        ]

        for format_str in formats:
            assert format_str.startswith("float32x")
            assert format_str in ["float32x2", "float32x3", "float32x4"]

    def test_matrix_stride_consistency(self):
        """Test that matrix strides are consistent with their layout."""
        # Mat2 should be 4 floats (2x2)
        mat2_stride = NGLToWebGPU.stride_from_type("mat2")
        assert mat2_stride == 4 * FLOAT_SIZE

        # Mat3 should be 12 floats (3x3, aligned as 3x4)
        mat3_stride = NGLToWebGPU.stride_from_type("mat3")
        assert mat3_stride == 12 * FLOAT_SIZE

        # Mat4 should be 16 floats (4x4)
        mat4_stride = NGLToWebGPU.stride_from_type("mat4")
        assert mat4_stride == 16 * FLOAT_SIZE
