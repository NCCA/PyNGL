import pytest

from ncca.ngl import BBox, Vec3


def assert_bbox_extents(bbox, min_x, max_x, min_y, max_y, min_z, max_z):
    """Helper function to assert bbox extents."""
    assert bbox.min_x == pytest.approx(min_x)
    assert bbox.max_x == pytest.approx(max_x)
    assert bbox.min_y == pytest.approx(min_y)
    assert bbox.max_y == pytest.approx(max_y)
    assert bbox.min_z == pytest.approx(min_z)
    assert bbox.max_z == pytest.approx(max_z)


def assert_bbox_dimensions(bbox, width, height, depth):
    """Helper function to assert bbox dimensions."""
    assert bbox.width == pytest.approx(width)
    assert bbox.height == pytest.approx(height)
    assert bbox.depth == pytest.approx(depth)


def assert_bbox_center(bbox, center):
    """Helper function to assert bbox center."""
    assert bbox.center == center


def assert_bbox_properties(bbox, min_x, max_x, min_y, max_y, min_z, max_z, width, height, depth, center):
    """Helper function to assert all bbox properties."""
    assert_bbox_extents(bbox, min_x, max_x, min_y, max_y, min_z, max_z)
    assert_bbox_dimensions(bbox, width, height, depth)
    assert_bbox_center(bbox, center)


def test_default_ctor():
    test = BBox()
    assert_bbox_properties(
        test,
        min_x=-1.0,
        max_x=1.0,
        min_y=-1.0,
        max_y=1.0,
        min_z=-1.0,
        max_z=1.0,
        width=2.0,
        height=2.0,
        depth=2.0,
        center=Vec3(0.0, 0.0, 0.0),
    )


def test_construct_with_center():
    test = BBox(center=Vec3(2.0, 2.0, 2.0), width=2.0, height=3.0, depth=4.0)
    assert_bbox_properties(
        test,
        min_x=1.0,
        max_x=3.0,
        min_y=0.5,
        max_y=3.5,
        min_z=0.0,
        max_z=4.0,
        width=2.0,
        height=3.0,
        depth=4.0,
        center=Vec3(2.0, 2.0, 2.0),
    )


@pytest.mark.parametrize("method_name", ["from_extents", "set_extents"])
def test_extents_methods(method_name):
    """Test both from_extents constructor and set_extents method."""
    if method_name == "from_extents":
        test = BBox.from_extents(-5, 5, -2, 2, -3.2, 2.4)
    else:  # set_extents
        test = BBox()
        test.set_extents(-5, 5, -2, 2, -3.2, 2.4)

    assert_bbox_properties(
        test,
        min_x=-5.0,
        max_x=5.0,
        min_y=-2.0,
        max_y=2.0,
        min_z=-3.2,
        max_z=2.4,
        width=10.0,
        height=4.0,
        depth=5.6,
        center=Vec3(0.0, 0.0, -0.4),
    )


def test_setters():
    test = BBox()
    test.width = 5
    test.height = 25
    test.depth = 15

    assert_bbox_properties(
        test,
        min_x=-2.5,
        max_x=2.5,
        min_y=-12.5,
        max_y=12.5,
        min_z=-7.5,
        max_z=7.5,
        width=5.0,
        height=25.0,
        depth=15.0,
        center=Vec3(0.0, 0.0, 0.0),
    )


def test_get_verts():
    test = BBox()
    verts = test.get_vertex_array()
    expected_verts = [
        Vec3(-1, 1, -1),
        Vec3(1, 1, -1),
        Vec3(1, 1, 1),
        Vec3(-1, 1, 1),
        Vec3(-1, -1, -1),
        Vec3(1, -1, -1),
        Vec3(1, -1, 1),
        Vec3(-1, -1, 1),
    ]

    assert len(verts) == 8
    for i, expected_vert in enumerate(expected_verts):
        assert verts[i] == expected_vert


def test_center():
    test = BBox()
    test.center = Vec3(0, 2, 3)
    assert_bbox_center(test, Vec3(0, 2, 3))


def test_get_normal_array():
    test = BBox()
    normals = test.get_normal_array()
    expected_normals = [
        Vec3(0.0, 1.0, 0.0),
        Vec3(0.0, -1.0, 0.0),
        Vec3(1.0, 0.0, 0.0),
        Vec3(-1.0, 0.0, 0.0),
        Vec3(0.0, 0.0, 1.0),
        Vec3(0.0, 0.0, -1.0),
    ]

    assert len(normals) == 6
    for i, expected_normal in enumerate(expected_normals):
        assert normals[i] == expected_normal
