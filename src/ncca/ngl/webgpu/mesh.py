"""WebGPU renderer for backend-neutral mesh data."""

import wgpu

from ..mesh import MeshData

STANDARD_MESH_VERTEX_STRIDE = 32
STANDARD_MESH_TOPOLOGY = wgpu.PrimitiveTopology.triangle_list


def standard_mesh_vertex_layout() -> dict[str, object]:
    """Return the interleaved position, normal and UV vertex layout."""
    return {
        "array_stride": STANDARD_MESH_VERTEX_STRIDE,
        "step_mode": "vertex",
        "attributes": [
            {"format": "float32x3", "offset": 0, "shader_location": 0},
            {"format": "float32x3", "offset": 12, "shader_location": 1},
            {"format": "float32x2", "offset": 24, "shader_location": 2},
        ],
    }


class WebGPUMesh:
    """Upload and draw a MeshData instance with one WebGPU vertex buffer."""

    def __init__(
        self, device: wgpu.GPUDevice, mesh: MeshData, *, flip_v: bool = False
    ) -> None:
        """Store the device, mesh and UV packing policy."""
        self.device = device
        self.mesh = mesh
        self.flip_v = flip_v
        self._buffer: wgpu.GPUBuffer | None = None
        self._vertex_count = 0

    @property
    def buffer(self) -> wgpu.GPUBuffer | None:
        """Return the GPU buffer after upload."""
        return self._buffer

    @property
    def vertex_count(self) -> int:
        """Return the number of expanded triangle vertices."""
        return self._vertex_count

    def upload(self, *, force: bool = False) -> None:
        """Create the static vertex buffer."""
        if self._buffer is not None and not force:
            return
        if self._buffer is not None:
            self.cleanup()
        data = self.mesh.triangle_vertex_data(flip_v=self.flip_v)
        if not data.size:
            raise RuntimeError("cannot upload an empty mesh")
        self._buffer = self.device.create_buffer_with_data(
            data=data.tobytes(),
            usage=wgpu.BufferUsage.VERTEX,
            label="mesh_vertex_buffer",
        )
        self._vertex_count = data.size // 8
        self.mesh.calc_dimensions()

    def draw(
        self,
        render_pass: wgpu.GPURenderPassEncoder,
        *,
        slot: int = 0,
        instance_count: int = 1,
        first_instance: int = 0,
    ) -> None:
        """Bind the mesh buffer and issue one draw command."""
        if self._buffer is None:
            raise RuntimeError("mesh must be uploaded before drawing")
        render_pass.set_vertex_buffer(slot, self._buffer)
        render_pass.draw(self._vertex_count, instance_count, 0, first_instance)

    def cleanup(self) -> None:
        """Destroy the owned vertex buffer."""
        if self._buffer is not None:
            self._buffer.destroy()
            self._buffer = None
            self._vertex_count = 0
