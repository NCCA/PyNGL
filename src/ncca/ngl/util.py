"""Utility math module, contains various useful functions for 3D.

Most of these functions are based on functions found in other libraries such as GLM, NGL or GLU
"""

import enum
import math

import numpy as np

from .mat4 import Mat4


def clamp(num, low, high):
    "clamp to range min and max will throw ValueError is low>=high"
    if low > high or low == high:
        raise ValueError
    return max(min(num, high), low)


def look_at(eye, look, up):
    """
    Calculate 4x4 matrix for camera lookAt
    """

    n = look - eye
    u = up
    v = n.cross(u)
    u = v.cross(n)
    n.normalize()
    v.normalize()
    u.normalize()

    result = Mat4.identity()
    result.m[0][0] = v.x
    result.m[1][0] = v.y
    result.m[2][0] = v.z
    result.m[0][1] = u.x
    result.m[1][1] = u.y
    result.m[2][1] = u.z
    result.m[0][2] = -n.x
    result.m[1][2] = -n.y
    result.m[2][2] = -n.z
    result.m[3][0] = -eye.dot(v)
    result.m[3][1] = -eye.dot(u)
    result.m[3][2] = eye.dot(n)
    return result


class PerspMode(enum.Enum):
    OpenGL = "OpenGL"
    WebGPU = "WebGPU"
    Vulkan = "Vulkan"


def perspective(
    fov: float,
    aspect: float,
    near: float,
    far: float,
    mode: PerspMode = PerspMode.OpenGL,
) -> Mat4:
    """
    Calculate a perspective matrix for various 3D graphics API's default mode is OpenGL but will covert for Vulkan and Web GPU if
    required.

    Args :
        fov : float - Field of view angle in degrees.
        aspect : float - Aspect ratio of the viewport.
        near : float - Near clipping plane distance.
        far : float - Far clipping plane distance.

    Returns:
        Mat4 - The perspective matrix.
    """
    m = Mat4.zero()  # as per glm
    _range = math.tan(math.radians(fov / 2.0)) * near
    left = -_range * aspect
    right = _range * aspect
    bottom = -_range
    top = _range
    m.m[0][0] = (2.0 * near) / (right - left)
    m.m[1][1] = (2.0 * near) / (top - bottom)
    match mode:
        case PerspMode.OpenGL:
            m.m[2][2] = -(far + near) / (far - near)
            m.m[2][3] = -1.0
            m.m[3][2] = -(2.0 * far * near) / (far - near)

        # This ensures the clip space Z range is [0, 1] as required by Vulkan and WebGPU.
        case PerspMode.WebGPU | PerspMode.Vulkan:
            m.m[2][2] = -far / (far - near)
            m.m[2][3] = -1.0
            m.m[3][2] = -(far * near) / (far - near)
    return m


def ortho(left, right, bottom, top, near, far, mode=PerspMode.OpenGL):
    m = Mat4.identity()
    m.m[0][0] = 2.0 / (right - left)
    m.m[1][1] = 2.0 / (top - bottom)
    match mode:
        case PerspMode.OpenGL:
            m.m[2][2] = -2.0 / (far - near)
            m.m[3][2] = -(far + near) / (far - near)
        case PerspMode.WebGPU | PerspMode.Vulkan:
            m.m[2][2] = -1.0 / (far - near)
            m.m[3][2] = -near / (far - near)
    m.m[3][0] = -(right + left) / (right - left)
    m.m[3][1] = -(top + bottom) / (top - bottom)
    return m


def frustum(left, right, bottom, top, near, far):
    """Create a frustum projection matrix."""
    m = Mat4.zero()
    m.m[0][0] = (2.0 * near) / (right - left)
    m.m[1][1] = (2.0 * near) / (top - bottom)
    m.m[2][0] = (right + left) / (right - left)
    m.m[2][1] = (top + bottom) / (top - bottom)
    m.m[2][2] = -(far + near) / (far - near)
    m.m[2][3] = -1.0
    m.m[3][2] = -(2.0 * far * near) / (far - near)
    return m


def lerp(a, b, t):
    return a + (b - a) * t


def calc_normal(p1, p2, p3):
    """
    Calculates the normal of a triangle defined by three points.

    This is a Python implementation of the NGL C++ Util::calcNormal function.
    It uses the vector cross product method for clarity and leverages the py-ngl library.
    The order of the cross product is chosen to match the output of the C++ version.

    Args:
        p1: The first vertex of the triangle.
        p2: The second vertex of the triangle.
        p3: The third vertex of the triangle.

    Returns:
        The normalized normal vector of the triangle.
    """
    # Two vectors on the plane of the triangle
    v1 = p3 - p1
    v2 = p2 - p1

    # The cross product gives the normal vector.
    # The order (v1 x v2) is used to match the C++ implementation's result.
    normal = v1.cross(v2)

    # Normalize the result to get a unit length normal
    normal.normalize()

    return normal


def hash_combine(seed, h):
    # emulate the NGL C++ combine: seed ^= h + 0x9e3779b9 + (seed<<6) + (seed>>2)
    seed = (seed + 0x9E3779B9 + ((seed << 6) & 0xFFFFFFFFFFFFFFFF) + (seed >> 2)) & 0xFFFFFFFFFFFFFFFF
    seed ^= h
    return seed


def renderman_look_at(eye, look, up):
    """
    Calculate 4x4 matrix for RenderMan camera lookAt
    Accounts for RenderMan's right-handed Y-down, Z-forward coordinate system

    Args:
        eye: Vec3 - camera position
        look: Vec3 - point to look at
        up: Vec3 - up vector (typically (0, 1, 0) in world space)

    Returns:
        Mat4 - 4x4 transformation matrix
    """
    # Calculate view direction (from eye to look point)
    n = look - eye
    n.normalize()

    # Calculate right vector
    up.y = -up.y
    v = n.cross(up)
    v.normalize()

    # Recalculate orthogonal up vector
    u = v.cross(n)
    u.normalize()

    # Build the matrix for RenderMan's coordinate system
    # RenderMan uses Y-down, Z-forward
    result = Mat4.identity()

    # Right vector (X-axis)
    result.m[0][0] = v.x
    result.m[1][0] = v.y
    result.m[2][0] = v.z

    # Up vector (Y-axis) - negated for Y-down convention
    result.m[0][1] = -u.x
    result.m[1][1] = -u.y
    result.m[2][1] = -u.z

    # Forward vector (Z-axis) - camera looks down +Z
    result.m[0][2] = n.x
    result.m[1][2] = n.y
    result.m[2][2] = n.z

    # Translation (camera position)
    result.m[3][0] = -eye.dot(v)
    result.m[3][1] = -eye.dot(u)  # Negated Y component
    result.m[3][2] = -eye.dot(n)

    return result


def prim_data_to_ri_points_polygons(triangles: np.ndarray):
    """
    Convert a packed numpy array of triangles to RenderMan PointsPolygons format.
    This is designed to work with the PrimData class outputs.
    Parameters
    ----------
    triangles : np.ndarray
        Array of shape (n_vertices, 8) where each row is: x, y, z, nx, ny, nz, u, v
        n_vertices must be divisible by 3 (since we have triangles)

    Returns
    -------
    tuple
        (nvertices, vertices, parameterlist)
        - nvertices: list of vertex counts per polygon (all 3 for triangles)
        - vertices: flat list of vertex indices
        - parameterlist: dict with 'P', 'N', 'st' arrays for RenderMan
    """
    # Ensure it's a 2D array
    if triangles.ndim == 1:
        # If completely flat, reshape to (n_verts, 8)
        if len(triangles) % 8 != 0:
            raise ValueError("1D array length must be divisible by 8")
        triangles = triangles.reshape(-1, 8)

    n_verts = triangles.shape[0]
    if n_verts % 3 != 0:
        raise ValueError("Number of vertices must be divisible by 3")

    n_triangles = n_verts // 3

    # Extract components from each row
    positions = triangles[:, 0:3]  # (n_verts, 3) - x, y, z
    normals = triangles[:, 3:6]  # (n_verts, 3) - nx, ny, nz
    uvs = triangles[:, 6:8]  # (n_verts, 2) - u, v

    # RenderMan PointsPolygons format
    nvertices = [3] * n_triangles  # Each polygon has 3 vertices
    vertices = list(range(n_verts))  # Sequential vertex indices

    # Parameter list - flatten to 1D arrays as RenderMan expects
    parameterlist = {
        "P": positions.flatten().tolist(),  # Position
        "N": normals.flatten().tolist(),  # Normals
        "st": uvs.flatten().tolist(),  # Texture coordinates
    }

    return nvertices, vertices, parameterlist
