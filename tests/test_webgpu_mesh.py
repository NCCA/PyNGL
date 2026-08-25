from ncca.ngl import Face, MeshData, Vec3
from ncca.ngl.webgpu import WebGPUMesh, standard_mesh_vertex_layout


class FakeBuffer:
    def __init__(self) -> None:
        self.destroyed = False

    def destroy(self) -> None:
        self.destroyed = True


class FakeDevice:
    def __init__(self) -> None:
        self.calls = []

    def create_buffer_with_data(self, **kwargs):
        self.calls.append(kwargs)
        return FakeBuffer()


class FakePass:
    def __init__(self) -> None:
        self.calls = []

    def set_vertex_buffer(self, *args) -> None:
        self.calls.append(("buffer", args))

    def draw(self, *args) -> None:
        self.calls.append(("draw", args))


def test_webgpu_mesh_uploads_and_draws_standard_data():
    mesh = MeshData()
    mesh.vertex = [Vec3(), Vec3(1, 0, 0), Vec3(0, 1, 0)]
    mesh.faces = [Face(vertex=[0, 1, 2])]
    device = FakeDevice()
    renderer = WebGPUMesh(device, mesh)

    renderer.upload()
    render_pass = FakePass()
    renderer.draw(render_pass, slot=2, instance_count=3, first_instance=4)

    assert renderer.vertex_count == 3
    assert len(device.calls[0]["data"]) == 96
    assert render_pass.calls[0][1][0] == 2
    assert render_pass.calls[1] == ("draw", (3, 3, 0, 4))


def test_standard_mesh_layout_is_fresh_and_has_expected_offsets():
    layout = standard_mesh_vertex_layout()

    assert layout["array_stride"] == 32
    assert [attribute["offset"] for attribute in layout["attributes"]] == [0, 12, 24]
    assert layout is not standard_mesh_vertex_layout()
