"""OpenGL primitive generation and drawing functions.

In this class we can generate a pipeline for drawing our data for the most part it will be
x,y,z nx,ny,nz and u,v data in a flat numpy array.
We need to create the data first which is stored in a map as part of the class, we can then call draw
which will generate a pipeline for this object and draw into the current context.
"""

from typing import Dict

import numpy as np
import OpenGL.GL as gl

from ..log import logger
from ..prim_data import PrimData, Prims
from .simple_vao import VertexData
from .vao_factory import VAOFactory, VAOType  # noqa
from ..vec3 import Vec3


class _primitive:
    """A private class to hold VAO data for a primitive."""

    def __init__(
        self,
        prim_data: np.ndarray,
        draw_mode: int = gl.GL_TRIANGLES,
        floats_per_vertex: int = 8,
    ) -> None:
        """Initializes the primitive with the given data.

        Args:
            prim_data: A numpy array containing the vertex data. Surface
                primitives use 8 floats per vertex (x,y,z,nx,ny,nz,u,v);
                line primitives use 3 (x,y,z).
            draw_mode: The OpenGL primitive mode to draw with.
            floats_per_vertex: Number of floats per vertex in prim_data (8 or 3).
        """
        self.vao = VAOFactory.create_vao(VAOType.SIMPLE, draw_mode)
        with self.vao:
            data = VertexData(data=prim_data.data, size=prim_data.size)
            self.vao.set_data(data)
            vert_data_size = floats_per_vertex * 4  # 4 is sizeof float
            self.vao.set_vertex_attribute_pointer(0, 3, gl.GL_FLOAT, vert_data_size, 0)
            if floats_per_vertex == 8:
                self.vao.set_vertex_attribute_pointer(
                    1, 3, gl.GL_FLOAT, vert_data_size, Vec3.sizeof()
                )
                self.vao.set_vertex_attribute_pointer(
                    2, 2, gl.GL_FLOAT, vert_data_size, 2 * Vec3.sizeof()
                )
            self.vao.set_num_indices(prim_data.size // floats_per_vertex)


class Primitives:
    """A static class for creating and drawing primitives."""

    # this is effectively a static class so we can use it to store data
    # and generate pipelines for drawing
    _primitives: Dict[str, _primitive] = {}
    _loaded: bool = False

    @classmethod
    def create(cls, type: str, name: str, *args: object, **kwargs: object) -> None:
        """Creates and stores a primitive object of the specified type.

        Prims.SPHERE : (radius: float, precision: int).
        Prims.TORUS : (radius: float, tube_radius: float, precision: int).
        Prims.LINE_GRID : (width: float, depth: float, steps: int).
        Prims.TRIANGLE_PLANE : ( width: float, depth: float, w_p: int, d_p: int, v_n: Vec3).
        Prims.CYLINDER : (radius: float, height: float, slices: int, stacks: int).
        Prims.CAPSULE : (radius: float, height: float, slices: int, stacks: int).
        Prims.CONE : (radius: float, height: float, slices: int, stacks: int).

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
        # line primitives are position-only GL_LINES data; everything else is
        # 8-float (position, normal, uv) triangle data
        prim_layouts = {
            Prims.LINE_GRID: (gl.GL_LINES, 3),
        }
        try:
            method = prim_methods[type]
        except KeyError:
            raise ValueError(f"Unknown primitive: {name}")

        draw_mode, floats_per_vertex = prim_layouts.get(type, (gl.GL_TRIANGLES, 8))
        cls._primitives[name] = _primitive(
            method(*args, **kwargs), draw_mode, floats_per_vertex
        )

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

    @classmethod
    def draw(cls, name: str | Prims) -> None:
        """Draws the specified primitive.

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
