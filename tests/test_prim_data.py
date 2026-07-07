"""Tests for ncca.ngl.prim_data procedural vertex generation.

These generators are pure NumPy functions (no GPU context required), so the
tests assert on observable output: array shape, dtype, vertex counts and value
invariants (points on the expected radius, constant normals, symmetry) rather
than on internal implementation details.
"""

import numpy as np
import pytest

from ncca.ngl import PrimData, Prims, Vec3
from ncca.ngl.prim_data import NON_NEG, RAD_POS, _circle_table


def _flat_to_vertices(data: np.ndarray) -> np.ndarray:
    """Reshape a flat interleaved (x,y,z,nx,ny,nz,u,v) buffer to (N, 8)."""
    assert data.ndim == 1
    assert data.size % 8 == 0
    return data.reshape(-1, 8)


# --------------------------------------------------------------------------- #
# _circle_table
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("n", [4, 8, 16])
def test_circle_table_shape_is_n_plus_one_by_two(n):
    cs = _circle_table(n)

    assert cs.shape == (n + 1, 2)
    assert cs.dtype == np.float32


def test_circle_table_first_entry_is_unit_x():
    cs = _circle_table(8)

    assert cs[0, 0] == pytest.approx(1.0)
    assert cs[0, 1] == pytest.approx(0.0)


def test_circle_table_last_row_duplicates_first():
    cs = _circle_table(12)

    assert cs[-1, 0] == pytest.approx(cs[0, 0])
    assert cs[-1, 1] == pytest.approx(cs[0, 1])


# --------------------------------------------------------------------------- #
# line_grid
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("steps", [1, 2, 5])
def test_line_grid_vertex_count_scales_with_steps(steps):
    data = PrimData.line_grid(2.0, 2.0, steps)

    # 4 line endpoints per step row, (steps + 1) rows, xyz each.
    assert data.shape == ((steps + 1) * 4, 3)
    assert data.dtype == np.float32


def test_line_grid_is_symmetric_about_origin():
    data = PrimData.line_grid(4.0, 6.0, 3)

    # Grid spans width/2 and depth/2 in both directions, centred on origin.
    assert data[:, 0].min() == pytest.approx(-data[:, 0].max())
    assert data[:, 2].min() == pytest.approx(-data[:, 2].max())
    assert data[:, 1].max() == pytest.approx(0.0)  # grid is flat on the y-plane


# --------------------------------------------------------------------------- #
# triangle_plane
# --------------------------------------------------------------------------- #


def test_triangle_plane_has_six_vertices_per_cell():
    w_p, d_p = 3, 2
    data = PrimData.triangle_plane(2.0, 2.0, w_p, d_p, Vec3(0.0, 1.0, 0.0))

    verts = _flat_to_vertices(data)
    assert verts.shape == (w_p * d_p * 6, 8)
    assert data.dtype == np.float32


def test_triangle_plane_normals_all_equal_supplied_normal():
    normal = Vec3(0.0, 1.0, 0.0)
    data = PrimData.triangle_plane(2.0, 2.0, 2, 2, normal)

    verts = _flat_to_vertices(data)
    assert np.allclose(verts[:, 3], normal.x)
    assert np.allclose(verts[:, 4], normal.y)
    assert np.allclose(verts[:, 5], normal.z)


# --------------------------------------------------------------------------- #
# sphere
# --------------------------------------------------------------------------- #


@pytest.mark.parametrize("radius", [1.0, 2.5])
@pytest.mark.parametrize("precision", [8, 16])
def test_sphere_positions_lie_on_radius(radius, precision):
    data = PrimData.sphere(radius, precision)

    assert data.shape == ((precision // 2) * precision * 6, 8)
    assert data.dtype == np.float32
    distances = np.linalg.norm(data[:, 0:3], axis=1)
    assert np.allclose(distances, radius, atol=1e-4)


def test_sphere_normals_are_unit_length():
    data = PrimData.sphere(3.0, 12)

    lengths = np.linalg.norm(data[:, 3:6], axis=1)
    assert np.allclose(lengths, 1.0, atol=1e-4)


def test_sphere_negative_radius_is_treated_as_positive():
    positive = PrimData.sphere(2.0, 8)
    negative = PrimData.sphere(-2.0, 8)

    distances = np.linalg.norm(negative[:, 0:3], axis=1)
    assert np.allclose(distances, 2.0, atol=1e-4)
    assert positive.shape == negative.shape


def test_sphere_precision_below_minimum_is_clamped_to_four():
    data = PrimData.sphere(1.0, 2)

    # precision clamped to 4 -> (4 // 2) * 4 * 6 vertices
    assert data.shape == (48, 8)


# --------------------------------------------------------------------------- #
# cone
# --------------------------------------------------------------------------- #


def test_cone_produces_interleaved_vertices():
    slices, stacks = 8, 4
    data = PrimData.cone(1.0, 2.0, slices, stacks)

    assert data.shape == (slices * stacks * 6, 8)
    assert data.dtype == np.float32


def test_cone_base_ring_sits_at_z_zero():
    data = PrimData.cone(1.0, 2.0, 8, 2)

    # At least some vertices are on the base plane z == 0.
    assert np.any(np.isclose(data[:, 2], 0.0))


# --------------------------------------------------------------------------- #
# capsule (exercises _add_cylinder_sides + _add_hemispherical_caps)
# --------------------------------------------------------------------------- #


def test_capsule_returns_non_empty_float32_buffer():
    data = PrimData.capsule(1.0, 2.0, 8)

    verts = _flat_to_vertices(data)
    assert verts.shape[0] > 0
    assert data.dtype == np.float32


def test_capsule_low_precision_is_clamped():
    data = PrimData.capsule(1.0, 2.0, 1)

    # precision clamped to 4 internally; still produces geometry.
    assert _flat_to_vertices(data).shape[0] > 0


@pytest.mark.parametrize("radius", [0.0, -1.0])
def test_capsule_rejects_non_positive_radius(radius):
    with pytest.raises(ValueError, match=RAD_POS):
        PrimData.capsule(radius, 2.0, 8)


def test_capsule_rejects_negative_height():
    with pytest.raises(ValueError, match=NON_NEG):
        PrimData.capsule(1.0, -1.0, 8)


# --------------------------------------------------------------------------- #
# cylinder
# --------------------------------------------------------------------------- #


def test_cylinder_positions_lie_on_radius():
    radius = 2.0
    data = PrimData.cylinder(radius, 4.0, 12, 2)

    verts = _flat_to_vertices(data)
    xz = verts[:, [0, 2]]
    assert np.allclose(np.linalg.norm(xz, axis=1), radius, atol=1e-4)


def test_cylinder_low_slices_and_stacks_are_clamped():
    data = PrimData.cylinder(1.0, 2.0, 1, 0)

    # slices clamped to 3, stacks to 1 -> 3 * 1 * 6 vertices.
    assert _flat_to_vertices(data).shape == (18, 8)


@pytest.mark.parametrize("radius", [0.0, -2.0])
def test_cylinder_rejects_non_positive_radius(radius):
    with pytest.raises(ValueError, match=RAD_POS):
        PrimData.cylinder(radius, 2.0, 8, 2)


def test_cylinder_rejects_negative_height():
    with pytest.raises(ValueError, match=NON_NEG):
        PrimData.cylinder(1.0, -1.0, 8, 2)


# --------------------------------------------------------------------------- #
# disk
# --------------------------------------------------------------------------- #


def test_disk_has_three_vertices_per_slice():
    slices = 10
    data = PrimData.disk(1.5, slices)

    assert _flat_to_vertices(data).shape == (slices * 3, 8)
    assert data.dtype == np.float32


def test_disk_low_slices_is_clamped_to_three():
    data = PrimData.disk(1.0, 1)

    assert _flat_to_vertices(data).shape == (9, 8)


@pytest.mark.parametrize("radius", [0.0, -1.0])
def test_disk_rejects_non_positive_radius(radius):
    with pytest.raises(ValueError, match=RAD_POS):
        PrimData.disk(radius, 8)


# --------------------------------------------------------------------------- #
# torus
# --------------------------------------------------------------------------- #


def test_torus_has_six_vertices_per_ring_side():
    sides, rings = 6, 8
    data = PrimData.torus(0.5, 2.0, sides, rings)

    assert _flat_to_vertices(data).shape == (sides * rings * 6, 8)
    assert data.dtype == np.float32


def test_torus_positions_lie_within_radius_band():
    minor, major = 0.5, 2.0
    data = PrimData.torus(minor, major, 12, 12)

    verts = _flat_to_vertices(data)
    dist_from_axis = np.linalg.norm(verts[:, [0, 2]], axis=1)
    assert dist_from_axis.min() >= major - minor - 1e-4
    assert dist_from_axis.max() <= major + minor + 1e-4


@pytest.mark.parametrize(
    ("minor", "major"),
    [(0.0, 2.0), (-1.0, 2.0), (0.5, 0.0), (0.5, -2.0)],
)
def test_torus_rejects_non_positive_radii(minor, major):
    with pytest.raises(ValueError, match=RAD_POS):
        PrimData.torus(minor, major, 8, 8)


@pytest.mark.parametrize(("sides", "rings"), [(2, 8), (8, 2)])
def test_torus_rejects_too_few_sides_or_rings(sides, rings):
    with pytest.raises(ValueError, match="at least 3"):
        PrimData.torus(0.5, 2.0, sides, rings)


# --------------------------------------------------------------------------- #
# primitive
# --------------------------------------------------------------------------- #


def test_primitive_loads_by_enum():
    data = PrimData.primitive(Prims.CUBE)

    assert isinstance(data, np.ndarray)
    assert data.size > 0


def test_primitive_loads_by_string_name():
    data = PrimData.primitive("cube")

    assert isinstance(data, np.ndarray)
    assert data.size > 0


def test_primitive_enum_and_string_agree():
    assert np.array_equal(
        PrimData.primitive(Prims.TEAPOT), PrimData.primitive("teapot")
    )


def test_primitive_unknown_name_raises_value_error():
    with pytest.raises(ValueError, match="not found"):
        PrimData.primitive("does_not_exist")
