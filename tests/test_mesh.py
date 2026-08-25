import numpy as np
import pytest

from ncca.ngl import Face, MeshData, MeshValidationError, Vec2, Vec3


def test_triangle_vertex_data_is_flat_float32_and_ordered():
    mesh = MeshData()
    mesh.vertex = [Vec3(1, 2, 3), Vec3(4, 5, 6), Vec3(7, 8, 9)]
    mesh.normals = [Vec3(0, 0, 1)] * 3
    mesh.uv = [Vec2(0, 0), Vec2(0.5, 0.25), Vec2(1, 1)]
    mesh.faces = [Face(vertex=[0, 1, 2], normal=[0, 1, 2], uv=[0, 1, 2])]

    data = mesh.triangle_vertex_data()

    assert data.dtype == np.float32
    assert data.ndim == 1
    assert data.flags.c_contiguous
    assert data.tolist() == pytest.approx(
        [1, 2, 3, 0, 0, 1, 0, 0, 4, 5, 6, 0, 0, 1, 0.5, 0.25, 7, 8, 9, 0, 0, 1, 1, 1]
    )


def test_mesh_data_supports_missing_attributes_and_flips_v():
    mesh = MeshData()
    mesh.vertex = [Vec3(), Vec3(1, 0, 0), Vec3(0, 1, 0)]
    mesh.uv = [Vec2(0, 0.25), Vec2(), Vec2()]
    mesh.faces = [Face(vertex=[0, 1, 2], uv=[0, 1, 2])]

    assert mesh.triangle_vertex_data(flip_v=True)[6:8].tolist() == pytest.approx(
        [0, 0.75]
    )
    assert mesh.triangle_vertex_data()[3:6].tolist() == pytest.approx([0, 0, 0])


def test_mesh_data_validates_partial_attributes_and_indices():
    mesh = MeshData()
    mesh.vertex = [Vec3(), Vec3(), Vec3()]
    mesh.faces = [Face(vertex=[0, 1, 3])]

    with pytest.raises(MeshValidationError):
        mesh.validate()


def test_mesh_data_empty_bounds_and_empty_packing():
    mesh = MeshData()
    mesh.calc_dimensions()

    assert mesh.bbox is None
    assert mesh.triangle_vertex_data().dtype == np.float32
    assert mesh.triangle_vertex_data().size == 0
