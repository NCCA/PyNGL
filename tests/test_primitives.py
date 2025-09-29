import pytest

from ncca.ngl import Primitives, Vec3


# Helper to clear primitives between tests
def clear_primitives():
    Primitives._primitives.clear()
    Primitives._loaded = False


@pytest.fixture(autouse=True)
def run_around_tests():
    clear_primitives()
    yield
    clear_primitives()


def test_create_line_grid_basic():
    Primitives.create_line_grid("test_grid", width=2.0, depth=2.0, steps=2)
    prim = Primitives._primitives["test_grid"]
    assert hasattr(prim, "vao")
    assert prim.vao is not None
    assert prim.vao.num_indices() > 0


def test_create_triangle_plane_basic():
    Primitives.create_triangle_plane("test_plane", width=2.0, depth=2.0, w_p=2, d_p=2, v_n=Vec3(0, 1, 0))
    prim = Primitives._primitives["test_plane"]
    assert hasattr(prim, "vao")
    assert prim.vao is not None
    assert prim.vao.num_indices() > 0


def test_create_sphere_basic():
    Primitives.create_sphere("test_sphere", radius=1.0, precision=8)
    prim = Primitives._primitives["test_sphere"]
    assert hasattr(prim, "vao")
    assert prim.vao is not None
    assert prim.vao.num_indices() > 0


def test_create_sphere_negative_radius():
    Primitives.create_sphere("neg_sphere", radius=-1.0, precision=8)
    prim = Primitives._primitives["neg_sphere"]
    assert prim.vao is not None


def test_create_sphere_low_precision():
    Primitives.create_sphere("low_prec_sphere", radius=1.0, precision=2)
    prim = Primitives._primitives["low_prec_sphere"]
    assert prim.vao is not None


def test_create_cone_basic():
    Primitives.create_cone("test_cone", base=1.0, height=2.0, stacks=2, slices=8)
    prim = Primitives._primitives["test_cone"]
    assert prim.vao is not None


def test_create_capsule_basic():
    Primitives.create_capsule("test_capsule", radius=1.0, height=2.0, precision=8)
    prim = Primitives._primitives["test_capsule"]
    assert prim.vao is not None


def test_create_capsule_invalid_radius():
    with pytest.raises(ValueError):
        Primitives.create_capsule("bad_capsule", radius=0.0, height=2.0, precision=8)


def test_create_capsule_invalid_height():
    with pytest.raises(ValueError):
        Primitives.create_capsule("bad_capsule", radius=1.0, height=-2.0, precision=8)


def test_create_cylinder_basic():
    Primitives.create_cylinder("test_cylinder", radius=1.0, height=2.0, slices=8, stacks=2)
    prim = Primitives._primitives["test_cylinder"]
    assert prim.vao is not None


def test_create_cylinder_invalid_radius():
    with pytest.raises(ValueError):
        Primitives.create_cylinder("bad_cylinder", radius=0.0, height=2.0, slices=8, stacks=2)


def test_create_cylinder_invalid_height():
    with pytest.raises(ValueError):
        Primitives.create_cylinder("bad_cylinder", radius=1.0, height=-2.0, slices=8, stacks=2)


def test_create_disk_basic():
    Primitives.create_disk("test_disk", radius=1.0, slices=8)
    prim = Primitives._primitives["test_disk"]
    assert prim.vao is not None


def test_create_disk_invalid_radius():
    with pytest.raises(ValueError):
        Primitives.create_disk("bad_disk", radius=0.0, slices=8)


def test_create_torus_basic():
    Primitives.create_torus("test_torus", major_radius=2.0, minor_radius=1.0, sides=8, rings=8)
    prim = Primitives._primitives["test_torus"]
    assert prim.vao is not None


def test_create_torus_invalid_radii():
    with pytest.raises(ValueError):
        Primitives.create_torus("bad_torus", major_radius=0.0, minor_radius=1.0, sides=8, rings=8)
    with pytest.raises(ValueError):
        Primitives.create_torus("bad_torus", major_radius=2.0, minor_radius=0.0, sides=8, rings=8)


def test_create_torus_invalid_sides_rings():
    with pytest.raises(ValueError):
        Primitives.create_torus("bad_torus", major_radius=2.0, minor_radius=1.0, sides=2, rings=8)
    with pytest.raises(ValueError):
        Primitives.create_torus("bad_torus", major_radius=2.0, minor_radius=1.0, sides=8, rings=2)
