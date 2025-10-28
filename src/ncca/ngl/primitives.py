"""
OpenGL primitive generation and drawing functions
In this class we can generate a pipeline for drawing our data for the most part it will be
x,y,z nx,ny,nz and u,v data in a flat numpy array.
We need to create the data first which is stored in a map as part of the class, we can then call draw
which will generate a pipeline for this object and draw into the current context.
"""

from typing import Dict, Union

import numpy as np
import OpenGL.GL as gl

from .log import logger
from .prim_data import PrimData, Prims
from .simple_vao import VertexData
from .vao_factory import VAOFactory, VAOType  # noqa
from .vec3 import Vec3


class _primitive:
    """A private class to hold VAO data for a primitive."""

    def __init__(self, prim_data: np.ndarray):
        """
        Initializes the primitive with the given data.

        Args:
            prim_data: A numpy array containing the vertex data (x,y,z,nx,ny,nz,u,v).
        """
        self.vao = VAOFactory.create_vao(VAOType.SIMPLE, gl.GL_TRIANGLES)
        with self.vao:
            data = VertexData(data=prim_data.data, size=prim_data.size)
            self.vao.set_data(data)
            vert_data_size = 8 * 4  # 4 is sizeof float and 8 is x,y,z,nx,ny,nz,uv
            self.vao.set_vertex_attribute_pointer(0, 3, gl.GL_FLOAT, vert_data_size, 0)
            self.vao.set_vertex_attribute_pointer(1, 3, gl.GL_FLOAT, vert_data_size, Vec3.sizeof())
            self.vao.set_vertex_attribute_pointer(2, 2, gl.GL_FLOAT, vert_data_size, 2 * Vec3.sizeof())
            self.vao.set_num_indices(prim_data.size // 8)


class Primitives:
    """A static class for creating and drawing primitives."""

    # this is effectively a static class so we can use it to store data
    # and generate pipelines for drawing
    _primitives: Dict[str, _primitive] = {}
    _loaded: bool = False

    @classmethod
    def create(cls, type: str, name: str, *args: object, **kwargs: object) -> None:
        """
        Creates and stores a primitive object of the specified type from :-
        Prims.LINE_GRID : (width: float, depth: float, steps: int).
        Prims.SPHERE : (radius: float, precision: int).
        Prims.TORUS : (radius: float, tube_radius: float, precision: int).
        Prims.CAPSULE : (radius: float, height: float, precision: int).
        Prims.CYLINDER : (radius: float, height: float, precision: int).

        Args:
            type (str): The primitive type, typically from the Prims enum (e.g., Prims.SPHERE).
            name (str): The name to associate with the created primitive.
            *args: Positional arguments to pass to the primitive creation function (e.g., radius, precision).
            **kwargs: Keyword arguments to pass to the primitive creation function.

        Raises:
            ValueError: If the primitive type is not recognized.

        Example:
            Primitives.create(Prims.SPHERE, "sphere", 0.3, 32)
            Primitives.create(Prims.SPHERE, "sphere", radius=0.3, precision=32)
        """
        prim_methods = {
            Prims.SPHERE: PrimData.sphere,
            Prims.TORUS: PrimData.torus,
            Prims.LINE_GRID: PrimData.line_grid,
            Prims.TRIANGLE_PLANE: PrimData.triangle_plane,
            Prims.CYLINDER: PrimData.cylinder,
            Prims.DISK: PrimData.disk,
            Prims.CAPSULE: PrimData.capsule,
            Prims.CONE: PrimData.cone,
        }
        try:
            method = prim_methods[type]
        except KeyError:
            raise ValueError(f"Unknown primitive: {name}")

        cls._primitives[name] = _primitive(method(*args, **kwargs))

    @classmethod
    def load_default_primitives(cls) -> None:
        """Loads the default primitives from the PrimData directory."""
        logger.info("Loading default primitives...")
        if not cls._loaded:
            for p in Prims:
                try:
                    prim_data = PrimData.primitive(p.value)
                    prim = _primitive(prim_data)
                    cls._primitives[p.value] = prim
                except Exception:
                    pass
            cls._loaded = True

    # @classmethod
    # def create_line_grid(cls, name: str, width: float, depth: float, steps: int) -> None:
    #     """
    #     Creates a line grid primitive.

    #     Args:
    #         name: The name of the primitive to create.
    #         width: The width of the grid.
    #         depth: The depth of the grid.
    #         steps: The number of steps in the grid.
    #     """
    #     # Convert the list to a NumPy array
    #     data_array = PrimData.line_grid(width, depth, steps)
    #     prim = _primitive(data_array)
    #     cls._primitives[name] = prim

    # @classmethod
    # def create_triangle_plane(cls, name: str, width: float, depth: float, w_p: int, d_p: int, v_n: Vec3) -> None:
    #     """
    #     Creates a triangle plane primitive.

    #     Args:
    #         name: The name of the primitive.
    #         width: The width of the plane.
    #         depth: The depth of the plane.
    #         w_p: The number of width partitions.
    #         d_p: The number of depth partitions.
    #         v_n: The normal vector for the plane.
    #     """

    #     data_array = PrimData.triangle_plane(width, depth, w_p, d_p, v_n)
    #     prim = _primitive(data_array)
    #     cls._primitives[name] = prim

    @classmethod
    def draw(cls, name: Union[str, Prims]) -> None:
        """
        Draws the specified primitive.

        Args:
            name: The name of the primitive to draw, either as a string or a Prims enum.
        """
        key = name.value if isinstance(name, Prims) else name
        try:
            prim = cls._primitives[key]
            with prim.vao:
                prim.vao.draw()
        except KeyError:
            logger.error(f"Failed to draw primitive {key}")
            return

    # @classmethod
    # def create_sphere(cls, name: str, radius: float, precision: int) -> None:
    #     """
    #     Creates a sphere primitive.

    #     Args:
    #         name: The name of the primitive.
    #         radius: The radius of the sphere.
    #         precision: The precision of the sphere (number of slices).
    #     """

    #     data_array = PrimData.sphere(radius, precision)
    #     prim = _primitive(data_array)
    #     cls._primitives[name] = prim

    # @classmethod
    # def create_cone(cls, name: str, base: float, height: float, slices: int, stacks: int) -> None:
    #     """
    #     Creates a cone primitive.

    #     Args:
    #         name: The name of the primitive.
    #         base: The radius of the cone's base.
    #         height: The height of the cone.
    #         slices: The number of divisions around the cone.
    #         stacks: The number of divisions along the cone's height.
    #     """
    #     data_array = PrimData.cone(base, height, slices, stacks)
    #     prim = _primitive(data_array)
    #     cls._primitives[name] = prim

    # @classmethod
    # def create_capsule(cls, name: str, radius: float, height: float, precision: int) -> None:
    #     """
    #     Creates a capsule primitive.
    #     The capsule is aligned along the y-axis.
    #     It is composed of a cylinder and two hemispherical caps.
    #     based on code from here https://code.google.com/p/rgine/source/browse/trunk/RGine/opengl/src/RGLShapes.cpp
    #     and adapted

    #     Args:
    #         name: The name of the primitive.
    #         radius: The radius of the capsule.
    #         height: The height of the capsule.
    #         precision: The precision of the capsule.
    #     """

    #     data_array = PrimData.capsule(radius, height, precision)
    #     prim = _primitive(data_array)
    #     cls._primitives[name] = prim

    # @classmethod
    # def create_cylinder(cls, name: str, radius: float, height: float, slices: int, stacks: int) -> None:
    #     """
    #     Creates a cylinder primitive.
    #     The cylinder is aligned along the y-axis.
    #     This method generates the cylinder walls, but not the top and bottom caps.

    #     Args:
    #         name: The name of the primitive.
    #         radius: The radius of the cylinder.
    #         height: The height of the cylinder.
    #         slices: The number of slices.
    #         stacks: The number of stacks.
    #     """

    #     data_array = PrimData.cylinder(radius, height, slices, stacks)
    #     prim = _primitive(data_array)
    #     cls._primitives[name] = prim

    # @classmethod
    # def create_disk(cls, name: str, radius: float, slices: int) -> None:
    #     """
    #     Creates a disk primitive.

    #     Args:
    #         name: The name of the primitive.
    #         radius: The radius of the disk.
    #         slices: The number of slices to divide the disk into.
    #     """

    #     data_array = PrimData.disk(radius, slices)
    #     prim = _primitive(data_array)
    #     cls._primitives[name] = prim

    # @classmethod
    # def create_torus(cls, name: str, minor_radius: float, major_radius: float, sides: int, rings: int) -> None:
    #     """
    #     Creates a torus primitive.

    #     Args:
    #         name: The name of the primitive.
    #         minor_radius: The minor radius of the torus.
    #         major_radius: The major radius of the torus.
    #         sides: The number of sides for each ring.
    #         rings: The number of rings for the torus.
    #     """

    #     data_array = PrimData.torus(minor_radius, major_radius, sides, rings)
    #     prim = _primitive(data_array)
    #     cls._primitives[name] = prim
