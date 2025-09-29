"""
Note opengl_context created once in conftest.py
"""

import OpenGL.GL as gl
import pytest

from ncca.ngl import (
    DefaultShader,
    IndexVertexData,
    ShaderLib,
    VAOFactory,
    VAOType,
    VertexData,
)


def test_vao_factory(opengl_context):
    for vao_type in VAOType.SIMPLE, VAOType.MULTI_BUFFER, VAOType.SIMPLE_INDEX:
        vao = VAOFactory.create_vao(vao_type, gl.GL_TRIANGLES)
        assert vao is not None

    with pytest.raises(ValueError):
        VAOFactory.create_vao("nonExistentVAO", gl.GL_TRIANGLES)


def test_simple_vao(opengl_context):
    vertices = [-0.5, -0.5, 0.0, 0.5, -0.5, 0.0, 0.0, 0.5, 0.0]
    vao = VAOFactory.create_vao(VAOType.SIMPLE, gl.GL_TRIANGLES)
    vao.bind()
    data = VertexData(data=vertices, size=len(vertices) // 3)
    vao.set_data(data)
    vao.set_vertex_attribute_pointer(0, 3, gl.GL_FLOAT, 0, 0)
    ShaderLib.use(DefaultShader.COLOUR)
    vao.draw()
    vao.unbind()
    assert vao.get_id() != 0
    assert vao.get_buffer_id() != 0
    vao.remove_vao()


def test_multi_buffer_vao(opengl_context):
    verts = [-0.5, -0.5, 0.0, 0.5, -0.5, 0.0, 0.0, 0.5, 0.0]
    colors = [1.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 1.0]
    vao = VAOFactory.create_vao(VAOType.MULTI_BUFFER, gl.GL_TRIANGLES)
    vao.bind()
    vert_data = VertexData(data=verts, size=len(verts) // 3)
    vao.set_data(vert_data, 0)
    vao.set_vertex_attribute_pointer(0, 3, gl.GL_FLOAT, 0, 0)
    color_data = VertexData(data=colors, size=len(colors) // 3)
    vao.set_data(color_data, 1)
    vao.set_vertex_attribute_pointer(1, 3, gl.GL_FLOAT, 0, 0)
    ShaderLib.use(DefaultShader.COLOUR)
    vao.draw()
    vao.unbind()
    assert vao.get_buffer_id(0) != 0
    assert vao.get_buffer_id(1) != 0
    vao.remove_vao()


def test_simple_index_vao(opengl_context):
    vertices = [-0.5, -0.5, 0.0, 0.5, -0.5, 0.0, 0.0, 0.5, 0.0]
    indices = [0, 1, 2]
    vao = VAOFactory.create_vao(VAOType.SIMPLE_INDEX, gl.GL_TRIANGLES)
    vao.bind()
    data = IndexVertexData(
        data=vertices,
        size=len(vertices) // 3,
        indices=indices,
        index_type=gl.GL_UNSIGNED_INT,
    )
    vao.set_data(data)
    vao.set_vertex_attribute_pointer(0, 3, gl.GL_FLOAT, 0, 0)
    ShaderLib.use(DefaultShader.COLOUR)
    vao.draw()
    vao.unbind()
    assert vao.get_id() != 0
    assert vao.get_buffer_id() != 0
    vao.remove_vao()


def test_vao_context_manager(opengl_context):
    vertices = [-0.5, -0.5, 0.0, 0.5, -0.5, 0.0, 0.0, 0.5, 0.0]
    vao = VAOFactory.create_vao(VAOType.SIMPLE, gl.GL_TRIANGLES)
    with vao as v:
        assert v.bound is True
        data = VertexData(data=vertices, size=len(vertices) // 3)
        v.set_data(data)
        v.set_vertex_attribute_pointer(0, 3, gl.GL_FLOAT, 0, 0)
        ShaderLib.use(DefaultShader.COLOUR)
        v.draw()
    assert v.bound is False
    vao.remove_vao()


def test_abstract_vao_coverage(opengl_context):
    vao = VAOFactory.create_vao(VAOType.SIMPLE, gl.GL_LINES)

    # test set_vertex_attribute_pointer on unbound vao (line 56)
    # This should log an error and raise a GLError
    with pytest.raises(gl.GLError):
        vao.set_vertex_attribute_pointer(0, 3, gl.GL_FLOAT, 0, 0)

    # test get_mode (line 69)
    assert vao.get_mode() == gl.GL_LINES
    # test set_mode (line 72)
    vao.set_mode(gl.GL_TRIANGLES)
    assert vao.get_mode() == gl.GL_TRIANGLES

    vertices = [-0.5, -0.5, 0.0, 0.5, -0.5, 0.0, 0.0, 0.5, 0.0]
    data = VertexData(data=vertices, size=len(vertices) // 3)

    with vao:
        vao.set_data(data)  # covers line 46
        # test num_indices (line 66)
        assert vao.num_indices() == len(vertices) // 3
        # test map_buffer (line 80) and unmap_buffer (line 83)
        ptr = vao.map_buffer()
        assert ptr is not None
        vao.unmap_buffer()
        # test draw (line 42)
        ShaderLib.use(DefaultShader.COLOUR)
        vao.draw()

    # test get_buffer_id (line 76)
    assert vao.get_buffer_id() != 0
    # test remove_vao (line 50)
    vao.remove_vao()


def test_multi_buffer_vao_coverage(opengl_context):
    vao = VAOFactory.create_vao(VAOType.MULTI_BUFFER, gl.GL_TRIANGLES)

    # test draw on unbound and unallocated vao (line 17)
    vao.draw()

    # test set_data with invalid data type (lines 21, 22)
    with pytest.raises(TypeError):
        vao.set_data("not vertex data")

    # test creating one new buffer (line 30)
    verts = [-0.5, -0.5, 0.0, 0.5, -0.5, 0.0, 0.0, 0.5, 0.0]
    vert_data = VertexData(data=verts, size=len(verts) // 3)
    with vao:
        vao.set_data(vert_data, 0)  # this will create one buffer

    # test get_buffer_id with default index (lines 48-49)
    assert vao.get_buffer_id() != 0

    vao.remove_vao()
