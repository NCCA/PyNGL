"""
Note opengl_context created once in conftest.py
"""

import OpenGL.GL as gl
import pytest

from ngl import (
    Mat2,
    Mat3,
    Mat4,
    Shader,
    ShaderLib,
    ShaderProgram,
    ShaderType,
    Vec2,
    Vec3,
    Vec4,
)

sourcedir = "tests/files/"


def test_load_shader(opengl_context):
    assert ShaderLib.load_shader(
        "Test",
        sourcedir + "vert.glsl",
        sourcedir + "frag.glsl",
    )


def test_use(opengl_context):
    ShaderLib.use("Test")
    assert ShaderLib.get_current_shader_name() == "Test"


def test_use_null(opengl_context):
    ShaderLib.use("unknown")
    assert ShaderLib.get_current_shader_name() is None


def test_load_error_shader(opengl_context):
    assert not ShaderLib.load_shader(
        "Test",
        sourcedir + "vertErr.glsl",
        sourcedir + "fragErr.glsl",
        exit_on_error=False,
    )


def test_load_parts(opengl_context):
    shader_name = "Test2"
    ShaderLib.create_shader_program(shader_name)
    vertex = "Test2Vert"
    ShaderLib.attach_shader(vertex, ShaderType.VERTEX)
    ShaderLib.load_shader_source(vertex, sourcedir + "vert.glsl")
    assert ShaderLib.compile_shader(vertex)

    fragment = "Test2Frag"
    ShaderLib.attach_shader(fragment, ShaderType.FRAGMENT)
    ShaderLib.load_shader_source(fragment, sourcedir + "frag.glsl")
    assert ShaderLib.compile_shader(fragment)

    ShaderLib.attach_shader_to_program(shader_name, vertex)
    ShaderLib.attach_shader_to_program(shader_name, fragment)

    assert ShaderLib.link_program_object(shader_name)
    ShaderLib.use(shader_name)
    assert ShaderLib.get_current_shader_name() == shader_name


def test_load_parts_fail_vertex(opengl_context):
    shader_name = "Test3"
    ShaderLib.create_shader_program(shader_name, exit_on_error=False)
    vertex = "Test3Vert"
    ShaderLib.attach_shader(vertex, ShaderType.VERTEX, exit_on_error=False)
    ShaderLib.load_shader_source(vertex, sourcedir + "vertErr.glsl")
    assert not ShaderLib.compile_shader(vertex)


def test_load_parts_fail_fragment(opengl_context):
    shader_name = "Test4"
    ShaderLib.create_shader_program(shader_name, exit_on_error=False)
    fragment = "Test4Frag"
    ShaderLib.attach_shader(fragment, ShaderType.FRAGMENT, exit_on_error=False)
    ShaderLib.load_shader_source(fragment, sourcedir + "fragErr.glsl")
    assert not ShaderLib.compile_shader(fragment)


def test_fail_link(opengl_context):
    shader_name = "Test5"
    ShaderLib.create_shader_program(shader_name, exit_on_error=False)
    vertex = "Test5Vert"
    ShaderLib.attach_shader(vertex, ShaderType.VERTEX, exit_on_error=False)
    ShaderLib.load_shader_source(vertex, sourcedir + "vertLinkErr.glsl")
    assert ShaderLib.compile_shader(vertex)
    fragment = "Test5Frag"
    ShaderLib.attach_shader(fragment, ShaderType.FRAGMENT, exit_on_error=False)
    ShaderLib.load_shader_source(fragment, sourcedir + "fragLinkErr.glsl")
    assert ShaderLib.compile_shader(fragment)
    ShaderLib.attach_shader_to_program(shader_name, vertex)
    ShaderLib.attach_shader_to_program(shader_name, fragment)
    assert not ShaderLib.link_program_object(shader_name)


def test_default_shader(opengl_context):
    ShaderLib.use("nglColourShader")


def test_set_uniform(opengl_context):
    shader_name = "TestUniform"
    assert ShaderLib.load_shader(
        shader_name,
        sourcedir + "testUniformVertex.glsl",
        sourcedir + "testUniformFragment.glsl",
        exit_on_error=False,
    )
    ShaderLib.use(shader_name)
    ShaderLib.set_uniform("testFloat", 2.25)
    result = ShaderLib.get_uniform_1f("testFloat")
    assert result == pytest.approx(2.25)

    ShaderLib.set_uniform("testVec2", 0.5, 2.0)
    result = ShaderLib.get_uniform_2f("testVec2")
    assert result[0] == pytest.approx(0.5)
    assert result[1] == pytest.approx(2.0)

    ShaderLib.set_uniform("testVec3", 0.5, 2.0, -22.2)
    result = ShaderLib.get_uniform_3f("testVec3")
    assert result[0] == pytest.approx(0.5)
    assert result[1] == pytest.approx(2.0)
    assert result[2] == pytest.approx(-22.2)

    ShaderLib.set_uniform("testVec4", 0.5, 2.0, -22.2, 1230.4)
    result = ShaderLib.get_uniform_4f("testVec4")
    assert result[0] == pytest.approx(0.5)
    assert result[1] == pytest.approx(2.0)
    assert result[2] == pytest.approx(-22.2)
    assert result[3] == pytest.approx(1230.4)

    mat = Mat2([1.0, 2.0, 3.0, 4.0])
    ShaderLib.set_uniform("testMat2", mat.to_list())
    result = ShaderLib.get_uniform_mat2("testMat2")
    assert result == mat.to_list()

    mat = Mat3.from_list([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])
    ShaderLib.set_uniform("testMat3", mat.to_list())
    result = ShaderLib.get_uniform_mat3("testMat3")
    # assert np.array_equal(result, mat.get_numpy())
    assert result == mat.to_list()
    # fmt: off
    mat = Mat4.from_list([1.0, 2.0, 3.0, 4.0,  5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0,13.0, 14.0, 15.0, 16.0,])
    #fmt :on
    ShaderLib.set_uniform("testMat4", mat.to_list())
    result = ShaderLib.get_uniform_mat4("testMat4")
    # assert np.array_equal(result, mat.to_list())
    assert result == mat.to_list()


def test_edit_shader(opengl_context):
    shader_name = "Edit"
    ShaderLib.create_shader_program(shader_name, exit_on_error=False)
    vertex = "EditVert"
    ShaderLib.attach_shader(vertex, ShaderType.VERTEX, exit_on_error=False)
    ShaderLib.load_shader_source(vertex, sourcedir + "EditVert.glsl")
    assert ShaderLib.edit_shader(vertex, "@breakMe", "1.0")
    assert ShaderLib.edit_shader(vertex, "@numLights", "2")
    assert ShaderLib.compile_shader(vertex)
    fragment = "EditFrag"
    ShaderLib.attach_shader(fragment, ShaderType.FRAGMENT, exit_on_error=False)
    ShaderLib.load_shader_source(fragment, sourcedir + "EditFrag.glsl")
    assert ShaderLib.edit_shader(fragment, "@numLights", "2")
    assert ShaderLib.compile_shader(fragment)
    ShaderLib.attach_shader_to_program(shader_name, vertex)
    ShaderLib.attach_shader_to_program(shader_name, fragment)
    assert ShaderLib.link_program_object(shader_name)
    ShaderLib.use(shader_name)
    assert ShaderLib.get_current_shader_name() == shader_name
    # Now re-edit
    ShaderLib.reset_edits(vertex)
    ShaderLib.reset_edits(fragment)
    assert ShaderLib.edit_shader(vertex, "@numLights", "5")
    assert ShaderLib.edit_shader(vertex, "@breakMe", "1.0")
    assert ShaderLib.edit_shader(fragment, "@numLights", "5")
    assert ShaderLib.compile_shader(vertex)
    assert ShaderLib.compile_shader(fragment)
    assert ShaderLib.link_program_object(shader_name)


@pytest.fixture
def simple_shader(opengl_context):
    vert = Shader("simple_vert", ShaderType.VERTEX.value)
    vert.load(sourcedir + "vert.glsl")
    vert.compile()
    frag = Shader("simple_frag", ShaderType.FRAGMENT.value)
    frag.load(sourcedir + "frag.glsl")
    frag.compile()
    program = ShaderProgram("simple")
    program.attach_shader(vert)
    program.attach_shader(frag)
    assert program.link()
    return program


def test_shaderprogram_use(opengl_context, simple_shader):
    simple_shader.use()
    assert gl.glGetIntegerv(gl.GL_CURRENT_PROGRAM) == simple_shader.get_id()


def test_shaderprogram_link_fail(opengl_context):
    vert = Shader("link_fail_vert", ShaderType.VERTEX.value, exit_on_error=False)
    vert.load(sourcedir + "vertLinkErr.glsl")
    vert.compile()
    frag = Shader("link_fail_frag", ShaderType.FRAGMENT.value, exit_on_error=False)
    frag.load(sourcedir + "fragLinkErr.glsl")
    frag.compile()
    program = ShaderProgram("link_fail", exit_on_error=False)
    program.attach_shader(vert)
    program.attach_shader(frag)
    assert not program.link()


def test_shaderprogram_link_fail_exit(opengl_context):
    vert = Shader("link_fail_exit_vert", ShaderType.VERTEX.value, exit_on_error=False)
    vert.load(sourcedir + "vertLinkErr.glsl")
    vert.compile()
    frag = Shader("link_fail_exit_frag", ShaderType.FRAGMENT.value, exit_on_error=False)
    frag.load(sourcedir + "fragLinkErr.glsl")
    frag.compile()
    program = ShaderProgram("link_fail_exit", exit_on_error=True)
    program.attach_shader(vert)
    program.attach_shader(frag)
    with pytest.raises(SystemExit):
        program.link()


@pytest.fixture
def uniform_shader(opengl_context):
    vert = Shader("uniform_vert", ShaderType.VERTEX.value)
    vert.load(sourcedir + "testUniformVertex.glsl")
    vert.compile()
    frag = Shader("uniform_frag", ShaderType.FRAGMENT.value)
    frag.load(sourcedir + "testUniformFragment.glsl")
    frag.compile()
    program = ShaderProgram("uniforms")
    program.attach_shader(vert)
    program.attach_shader(frag)
    assert program.link()
    return program


def test_shaderprogram_set_uniforms(opengl_context, uniform_shader):
    uniform_shader.use()
    uniform_shader.set_uniform("testInt", 12)
    # Note getUniform1i doesn't exist we use the float version as it works
    assert uniform_shader.get_uniform_1f("testInt") == 12

    mat = Mat2([1.0, 2.0, 3.0, 4.0])
    uniform_shader.set_uniform("testMat2", mat)
    assert uniform_shader.get_uniform_mat2("testMat2") == mat.to_list()

    vec = Vec2(0.1, 0.2)
    uniform_shader.set_uniform("testVec2", vec)
    assert uniform_shader.get_uniform_2f("testVec2") == pytest.approx(list(vec))

    vec = Vec3(0.1, 0.2, 0.3)
    uniform_shader.set_uniform("testVec3", vec)
    assert uniform_shader.get_uniform_3f("testVec3") == pytest.approx(vec.to_list())

    vec = Vec4(0.1, 0.2, 0.3, 0.4)
    uniform_shader.set_uniform("testVec4", vec)
    assert uniform_shader.get_uniform_4f("testVec4") == pytest.approx(vec.to_list())

    # test list based matrix
    mat_list = [1.0, 2.0, 3.0, 4.0]
    uniform_shader.set_uniform("testMat2", mat_list)
    assert uniform_shader.get_uniform_mat2("testMat2") == [1.0, 2.0, 3.0, 4.0]

    mat_list = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]
    uniform_shader.set_uniform("testMat3", mat_list)
    assert uniform_shader.get_uniform_mat3("testMat3") == [
        1.0,
        2.0,
        3.0,
        4.0,
        5.0,
        6.0,
        7.0,
        8.0,
        9.0,
    ]
    # fmt: off
    mat_list = [ 1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0, 11.0, 12.0, 13.0, 14.0, 15.0, 16.0]
    uniform_shader.set_uniform("testMat4", mat_list)
    assert uniform_shader.get_uniform_mat4("testMat4") == [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0,8.0,9.0,10.0,11.0,12.0,13.0,14.0,15.0,16.0,]
    #fmt: off

    # test unknown uniform
    assert uniform_shader.get_uniform_location("nonexistent") == -1
    uniform_shader.set_uniform("nonexistent", 1.0)  # should not raise

    # test unknown type
    uniform_shader.set_uniform("testFloat", "a string")  # should warn but not raise


def test_shaderprogram_get_uniforms_not_found(opengl_context, simple_shader):
    assert simple_shader.get_uniform_1f("nonexistent") == 0.0
    assert simple_shader.get_uniform_2f("nonexistent") == [0.0, 0.0]
    assert simple_shader.get_uniform_3f("nonexistent") == [0.0, 0.0, 0.0]
    assert simple_shader.get_uniform_4f("nonexistent") == [0.0, 0.0, 0.0, 0.0]
    assert simple_shader.get_uniform_mat2("nonexistent") == [0.0] * 4
    assert simple_shader.get_uniform_mat3("nonexistent") == [0.0] * 9
    assert simple_shader.get_uniform_mat4("nonexistent") == [0.0] * 16
    assert simple_shader.get_uniform_mat4x3("nonexistent") == [0.0] * 12


def test_shaderprogram_uniform_array(opengl_context):
    vert_shader = """
    #version 410 core
    void main()
    {
        gl_Position = vec4(0.0);
    }
    """
    frag_shader = """
    #version 410 core
    uniform vec4 colors[2];
    out vec4 fragColor;
    void main()
    {
        fragColor = colors[0] + colors[1];
    }
    """
    vert = Shader("uniform_array_vert", ShaderType.VERTEX.value)
    vert.load_shader_source_from_string(vert_shader)
    vert.compile()
    frag = Shader("uniform_array_frag", ShaderType.FRAGMENT.value)
    frag.load_shader_source_from_string(frag_shader)
    frag.compile()
    program = ShaderProgram("uniform_array")
    program.attach_shader(vert)
    program.attach_shader(frag)
    assert program.link()
    # auto_register_uniforms should have removed the "[0]"
    assert "colors" in program._uniforms


def test_shaderprogram_get_gl_type_string(opengl_context, simple_shader):
    assert simple_shader.get_gl_type_string(gl.GL_FLOAT) == "float"
    assert simple_shader.get_gl_type_string(0) == "Unknown type 0"


def test_shaderprogram_print_functions(opengl_context, uniform_shader):
    uniform_shader.print_registered_uniforms()
    uniform_shader.print_properties()


@pytest.fixture
def mat4x3_shader(opengl_context):
    vert_shader = """
    #version 410 core
    uniform mat4x3 testMat4x3;
    void main()
    {
        vec4 p = vec4(1.0,1.0,1.0,1.0);
        gl_Position = p * mat4(testMat4x3);
    }
    """
    frag_shader = """
    #version 410 core
    out vec4 fragColor;
    void main()
    {
        fragColor = vec4(1.0);
    }
    """
    vert = Shader("mat4x3_vert", ShaderType.VERTEX.value)
    vert.load_shader_source_from_string(vert_shader)
    vert.compile()
    frag = Shader("mat4x3_frag", ShaderType.FRAGMENT.value)
    frag.load_shader_source_from_string(frag_shader)
    frag.compile()
    program = ShaderProgram("mat4x3")
    program.attach_shader(vert)
    program.attach_shader(frag)
    assert program.link()
    return program


def test_shaderprogram_get_uniform_mat4x3(opengl_context, mat4x3_shader):
    mat4x3_shader.use()
    res = mat4x3_shader.get_uniform_mat4x3("testMat4x3")
    assert len(res) == 12


"""
Note opengl_context created once in conftest.py
"""


sourcedir = "tests/files/"


def test_load_shader_with_geo(opengl_context):
    assert ShaderLib.load_shader(
        "TestGeo",
        sourcedir + "vert.glsl",
        sourcedir + "frag.glsl",
        sourcedir + "geom.glsl",
    )


def test_get_program_id_non_existent(opengl_context):
    assert ShaderLib.get_program_id("nonExistent") is None


def test_load_shader_source_non_existent(opengl_context):
    ShaderLib.load_shader_source("nonExistent", "dummy.glsl")


def test_compile_shader_non_existent(opengl_context):
    assert not ShaderLib.compile_shader("nonExistent")


def test_attach_shader_to_program_non_existent(opengl_context):
    ShaderLib.attach_shader_to_program("nonExistentProgram", "nonExistentShader")


def test_link_program_object_non_existent(opengl_context):
    assert not ShaderLib.link_program_object("nonExistent")


def test_get_uniforms_no_current_shader(opengl_context):
    ShaderLib.use(None)
    assert ShaderLib.get_uniform_1f("test") == 0.0
    assert ShaderLib.get_uniform_2f("test") == [0.0, 0.0]
    assert ShaderLib.get_uniform_3f("test") == [0.0, 0.0, 0.0]
    assert ShaderLib.get_uniform_4f("test") == [0.0, 0.0, 0.0, 0.0]
    assert ShaderLib.get_uniform_mat2("test") == [0.0] * 4
    assert ShaderLib.get_uniform_mat3("test") == [0.0] * 9
    assert ShaderLib.get_uniform_mat4("test") == [0.0] * 16
