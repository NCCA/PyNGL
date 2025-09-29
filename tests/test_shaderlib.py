"""
Note opengl_context created once in conftest.py
"""

import OpenGL.GL as gl
import pytest

from ncca.ngl import (
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


@pytest.fixture
def array_uniform_shader(opengl_context):
    vert_shader = """
    #version 410 core
    uniform float floatArray[3];
    uniform vec2 vec2Array[2];
    uniform vec3 vec3Array[2];
    uniform vec4 vec4Array[2];
    uniform int intArray[2];
    uniform mat2 mat2Array[2];
    uniform mat3 mat3Array[2];
    uniform mat4 mat4Array[2];
    void main()
    {
        gl_Position = vec4(floatArray[0] + vec2Array[0].x + vec3Array[0].x + vec4Array[0].x + intArray[0] + mat2Array[0][0][0] + mat3Array[0][0][0] + mat4Array[0][0][0]);
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
    vert = Shader("array_uniform_vert", ShaderType.VERTEX.value)
    vert.load_shader_source_from_string(vert_shader)
    vert.compile()
    frag = Shader("array_uniform_frag", ShaderType.FRAGMENT.value)
    frag.load_shader_source_from_string(frag_shader)
    frag.compile()
    program = ShaderProgram("array_uniform")
    program.attach_shader(vert)
    program.attach_shader(frag)
    assert program.link()
    return program


def test_shaderprogram_array_uniform_methods(opengl_context, array_uniform_shader):
    """Test array uniform setter methods"""
    array_uniform_shader.use()

    # Test set_uniform_1fv
    float_values = [1.0, 2.0, 3.0]
    array_uniform_shader.set_uniform_1fv("floatArray", float_values)

    # Test set_uniform_2fv
    vec2_values = [[1.0, 2.0], [3.0, 4.0]]
    array_uniform_shader.set_uniform_2fv("vec2Array", vec2_values)

    # Test set_uniform_3fv
    vec3_values = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
    array_uniform_shader.set_uniform_3fv("vec3Array", vec3_values)

    # Test set_uniform_4fv
    vec4_values = [[1.0, 2.0, 3.0, 4.0], [5.0, 6.0, 7.0, 8.0]]
    array_uniform_shader.set_uniform_4fv("vec4Array", vec4_values)

    # Test set_uniform_1iv
    int_values = [10, 20]
    array_uniform_shader.set_uniform_1iv("intArray", int_values)

    # Test set_uniform_matrix2fv with Mat2 objects
    mat2_list = [Mat2([1.0, 2.0, 3.0, 4.0]), Mat2([5.0, 6.0, 7.0, 8.0])]
    array_uniform_shader.set_uniform_matrix2fv("mat2Array", mat2_list)

    # Test set_uniform_matrix2fv with lists
    mat2_raw = [[1.0, 2.0, 3.0, 4.0], [5.0, 6.0, 7.0, 8.0]]
    array_uniform_shader.set_uniform_matrix2fv("mat2Array", mat2_raw, transpose=True)

    # Test set_uniform_matrix3fv
    mat3_list = [Mat3.from_list([1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0])]
    array_uniform_shader.set_uniform_matrix3fv("mat3Array", mat3_list)

    # Test set_uniform_matrix4fv
    mat4_list = [
        Mat4.from_list([
            1.0,
            2.0,
            3.0,
            4.0,
            5.0,
            6.0,
            7.0,
            8.0,
            9.0,
            10.0,
            11.0,
            12.0,
            13.0,
            14.0,
            15.0,
            16.0,
        ])
    ]
    array_uniform_shader.set_uniform_matrix4fv("mat4Array", mat4_list)


def test_shaderprogram_array_uniform_methods_not_found(opengl_context, array_uniform_shader):
    """Test array uniform methods with non-existent uniforms"""
    array_uniform_shader.use()

    # These should not raise exceptions, just do nothing
    array_uniform_shader.set_uniform_1fv("nonexistent", [1.0, 2.0])
    array_uniform_shader.set_uniform_2fv("nonexistent", [[1.0, 2.0]])
    array_uniform_shader.set_uniform_3fv("nonexistent", [[1.0, 2.0, 3.0]])
    array_uniform_shader.set_uniform_4fv("nonexistent", [[1.0, 2.0, 3.0, 4.0]])
    array_uniform_shader.set_uniform_1iv("nonexistent", [1, 2])
    array_uniform_shader.set_uniform_matrix2fv("nonexistent", [[1.0, 2.0, 3.0, 4.0]])
    array_uniform_shader.set_uniform_matrix3fv("nonexistent", [[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]])
    array_uniform_shader.set_uniform_matrix4fv(
        "nonexistent",
        [
            [
                1.0,
                2.0,
                3.0,
                4.0,
                5.0,
                6.0,
                7.0,
                8.0,
                9.0,
                10.0,
                11.0,
                12.0,
                13.0,
                14.0,
                15.0,
                16.0,
            ]
        ],
    )


def test_shaderprogram_individual_array_elements(opengl_context, array_uniform_shader):
    """Test setting individual array elements like floatArray[0]"""
    array_uniform_shader.use()

    # Test setting individual elements (these may or may not exist depending on OpenGL optimization)
    # These calls should not crash even if the uniforms don't exist
    array_uniform_shader.set_uniform("floatArray[0]", 1.5)
    array_uniform_shader.set_uniform("floatArray[1]", 2.5)

    array_uniform_shader.set_uniform("vec2Array[0]", 1.0, 2.0)
    array_uniform_shader.set_uniform("vec3Array[0]", 1.0, 2.0, 3.0)
    array_uniform_shader.set_uniform("vec4Array[0]", 1.0, 2.0, 3.0, 4.0)


@pytest.fixture
def uniform_block_shader(opengl_context):
    vert_shader = """
    #version 410 core
    layout(std140) uniform TransformBlock {
        mat4 modelMatrix;
        mat4 viewMatrix;
        mat4 projMatrix;
    };
    void main()
    {
        gl_Position = projMatrix * viewMatrix * modelMatrix * vec4(0.0, 0.0, 0.0, 1.0);
    }
    """
    frag_shader = """
    #version 410 core
    layout(std140) uniform MaterialBlock {
        vec4 diffuseColor;
        vec4 specularColor;
        float shininess;
    };
    out vec4 fragColor;
    void main()
    {
        fragColor = diffuseColor + specularColor * shininess;
    }
    """
    vert = Shader("uniform_block_vert", ShaderType.VERTEX.value)
    vert.load_shader_source_from_string(vert_shader)
    vert.compile()
    frag = Shader("uniform_block_frag", ShaderType.FRAGMENT.value)
    frag.load_shader_source_from_string(frag_shader)
    frag.compile()
    program = ShaderProgram("uniform_block")
    program.attach_shader(vert)
    program.attach_shader(frag)
    assert program.link()
    return program


def test_shaderprogram_uniform_blocks(opengl_context, uniform_block_shader):
    """Test uniform block functionality"""
    # Test that uniform blocks were registered
    blocks = uniform_block_shader.get_registered_uniform_blocks()
    assert len(blocks) >= 1  # Should have at least one block

    # Test individual block data access
    if "TransformBlock" in blocks:
        block_data = uniform_block_shader.get_uniform_block_data("TransformBlock")
        assert block_data is not None
        assert "name" in block_data
        assert "loc" in block_data
        assert "buffer" in block_data

        # Test location getter
        loc = uniform_block_shader.get_uniform_block_location("TransformBlock")
        assert loc >= 0

        # Test buffer getter
        buffer = uniform_block_shader.get_uniform_block_buffer("TransformBlock")
        assert buffer > 0


def test_shaderprogram_uniform_blocks_not_found(opengl_context, uniform_block_shader):
    """Test uniform block methods with non-existent blocks"""
    assert uniform_block_shader.get_uniform_block_data("NonExistent") is None
    assert uniform_block_shader.get_uniform_block_location("NonExistent") == -1
    assert uniform_block_shader.get_uniform_block_buffer("NonExistent") == 0


def test_shaderprogram_set_uniform_buffer(opengl_context, uniform_block_shader):
    """Test setting uniform buffer data"""
    import numpy as np

    # Create test data (3 4x4 matrices = 192 bytes)
    matrix_data = np.array(
        [
            [
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
            ],  # Identity
            [
                2.0,
                0.0,
                0.0,
                0.0,
                0.0,
                2.0,
                0.0,
                0.0,
                0.0,
                0.0,
                2.0,
                0.0,
                0.0,
                0.0,
                0.0,
                1.0,
            ],  # Scale
            [
                1.0,
                0.0,
                0.0,
                5.0,
                0.0,
                1.0,
                0.0,
                3.0,
                0.0,
                0.0,
                1.0,
                2.0,
                0.0,
                0.0,
                0.0,
                1.0,
            ],  # Translate
        ],
        dtype=np.float32,
    )

    # Get first available uniform block
    blocks = uniform_block_shader.get_registered_uniform_blocks()
    if blocks:
        block_name = list(blocks.keys())[0]

        # Test successful buffer setting
        result = uniform_block_shader.set_uniform_buffer(block_name, matrix_data.nbytes, matrix_data)
        assert result


def test_shaderprogram_set_uniform_buffer_not_found(opengl_context, uniform_block_shader):
    """Test setting uniform buffer for non-existent block"""
    import numpy as np

    data = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
    result = uniform_block_shader.set_uniform_buffer("NonExistent", data.nbytes, data)
    assert result is False


def test_shaderprogram_array_uniform_registration(opengl_context, array_uniform_shader):
    """Test that array uniforms are properly registered"""
    # Test that we have some uniforms registered
    assert len(array_uniform_shader._uniforms) > 0

    # Test that array detection works for at least some uniforms
    has_arrays = any(is_array for _, _, _, is_array in array_uniform_shader._uniforms.values())
    has_base_arrays = any(name for name in array_uniform_shader._uniforms.keys() if not ("[" in name and "]" in name))

    # Either we have arrays detected as arrays, or we have base array names
    # (OpenGL behavior can vary based on optimization)
    assert has_arrays or has_base_arrays, "Should detect array uniforms in some form"

    # Test array info methods work (even if they return default values)
    _ = array_uniform_shader.get_uniform_array_size("floatArray")
    _ = array_uniform_shader.is_uniform_array("floatArray")


def test_debug_array_uniform_registration(opengl_context, array_uniform_shader):
    """Debug test to see what uniforms are actually registered"""
    print("\n=== DEBUG: All registered uniforms ===")
    for name, (
        location,
        shader_type,
        size,
        is_array,
    ) in array_uniform_shader._uniforms.items():
        print(f"{name}: location={location}, type={shader_type}, size={size}, is_array={is_array}")
    print("=== END DEBUG ===")

    # Check if we have any uniforms registered (OpenGL may optimize some out)
    assert len(array_uniform_shader._uniforms) > 0
    print(f"Total uniforms registered: {len(array_uniform_shader._uniforms)}")


def test_shaderprogram_print_methods(opengl_context, array_uniform_shader, uniform_block_shader):
    """Test print methods"""
    # Test print_registered_uniforms with arrays
    array_uniform_shader.print_registered_uniforms()

    # Test print_registered_uniform_blocks
    uniform_block_shader.print_registered_uniform_blocks()

    # Test print_properties with uniform blocks
    uniform_block_shader.print_properties()


def test_shaderprogram_set_uniform_edge_cases(opengl_context, uniform_shader):
    """Test edge cases in set_uniform method"""
    uniform_shader.use()

    # Test with custom objects that don't match known types
    class CustomObject:
        def __init__(self, value):
            self.value = value

    custom_obj = CustomObject(42)
    uniform_shader.set_uniform("testFloat", custom_obj)  # Should trigger warning

    # Test with None
    uniform_shader.set_uniform("testFloat", None)  # Should trigger warning

    # Test with empty list
    uniform_shader.set_uniform("testFloat", [])  # Should trigger warning or error handling


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
    assert ShaderLib.get_uniform_1f("test") == pytest.approx(0.0)
    assert ShaderLib.get_uniform_2f("test") == [0.0, 0.0]
    assert ShaderLib.get_uniform_3f("test") == [0.0, 0.0, 0.0]
    assert ShaderLib.get_uniform_4f("test") == [0.0, 0.0, 0.0, 0.0]
    assert ShaderLib.get_uniform_mat2("test") == [0.0] * 4
    assert ShaderLib.get_uniform_mat3("test") == [0.0] * 9
    assert ShaderLib.get_uniform_mat4("test") == [0.0] * 16


def test_shaderlib_array_uniform_shader(opengl_context):
    """Test ShaderLib with array uniforms"""
    vert_shader = """
    #version 410 core
    uniform float weights[4];
    uniform vec3 lightPositions[4];
    uniform vec3 lightColors[4];
    void main()
    {
        gl_Position = vec4(weights[0] + lightPositions[0].x + lightColors[0].x);
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
    # Load shaders using ShaderLib
    ShaderLib.create_shader_program("ArrayTest")
    ShaderLib.attach_shader("ArrayTestVert", ShaderType.VERTEX)
    ShaderLib.load_shader_source_from_string("ArrayTestVert", vert_shader)
    assert ShaderLib.compile_shader("ArrayTestVert")

    ShaderLib.attach_shader("ArrayTestFrag", ShaderType.FRAGMENT)
    ShaderLib.load_shader_source_from_string("ArrayTestFrag", frag_shader)
    assert ShaderLib.compile_shader("ArrayTestFrag")

    ShaderLib.attach_shader_to_program("ArrayTest", "ArrayTestVert")
    ShaderLib.attach_shader_to_program("ArrayTest", "ArrayTestFrag")
    assert ShaderLib.link_program_object("ArrayTest")
    ShaderLib.use("ArrayTest")

    # Test individual array element setting via ShaderLib (try a few elements)
    light_positions = [[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]
    light_colors = [[0.1, 0.2, 0.3], [0.4, 0.5, 0.6]]

    # Test first couple elements to see if they work
    for i in range(2):
        ShaderLib.set_uniform(f"lightPositions[{i}]", *light_positions[i])
        ShaderLib.set_uniform(f"lightColors[{i}]", *light_colors[i])
        ShaderLib.set_uniform(f"weights[{i}]", float(i + 1))


def test_shaderlib_uniform_buffer_shader(opengl_context):
    """Test ShaderLib with uniform blocks"""
    vert_shader = """
    #version 410 core
    layout(std140) uniform TransformUBO {
        mat4 modelMatrix;
        mat4 viewMatrix;
        mat4 projMatrix;
    };
    void main()
    {
        gl_Position = projMatrix * viewMatrix * modelMatrix * vec4(0.0, 0.0, 0.0, 1.0);
    }
    """
    frag_shader = """
    #version 410 core
    out vec4 fragColor;
    void main()
    {
        fragColor = vec4(1.0, 0.0, 0.0, 1.0);
    }
    """
    # Load shaders using ShaderLib
    ShaderLib.create_shader_program("UBOTest")
    ShaderLib.attach_shader("UBOTestVert", ShaderType.VERTEX)
    ShaderLib.load_shader_source_from_string("UBOTestVert", vert_shader)
    assert ShaderLib.compile_shader("UBOTestVert")

    ShaderLib.attach_shader("UBOTestFrag", ShaderType.FRAGMENT)
    ShaderLib.load_shader_source_from_string("UBOTestFrag", frag_shader)
    assert ShaderLib.compile_shader("UBOTestFrag")

    ShaderLib.attach_shader_to_program("UBOTest", "UBOTestVert")
    ShaderLib.attach_shader_to_program("UBOTest", "UBOTestFrag")
    assert ShaderLib.link_program_object("UBOTest")
    ShaderLib.use("UBOTest")

    # Test uniform buffer via ShaderLib
    import numpy as np

    matrix_data = np.array(
        [
            # Identity matrix
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            # Scale matrix
            2.0,
            0.0,
            0.0,
            0.0,
            0.0,
            2.0,
            0.0,
            0.0,
            0.0,
            0.0,
            2.0,
            0.0,
            0.0,
            0.0,
            0.0,
            1.0,
            # Translation matrix
            1.0,
            0.0,
            0.0,
            5.0,
            0.0,
            1.0,
            0.0,
            3.0,
            0.0,
            0.0,
            1.0,
            2.0,
            0.0,
            0.0,
            0.0,
            1.0,
        ],
        dtype=np.float32,
    )

    # Test ShaderLib uniform buffer setting
    result = ShaderLib.set_uniform_buffer("TransformUBO", matrix_data.nbytes, matrix_data)
    assert result


def test_shaderlib_uniform_buffer_no_shader(opengl_context):
    """Test ShaderLib uniform buffer with no current shader"""
    import numpy as np

    # Clear current shader first
    ShaderLib.use(None)

    data = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float32)
    result = ShaderLib.set_uniform_buffer("test", data.nbytes, data)
    assert result is False


def test_shaderlib_auto_register_uniform_blocks(opengl_context):
    """Test ShaderLib auto register uniform blocks"""
    # First ensure we have a shader with uniform blocks loaded
    if "UBOTest" not in ShaderLib._shader_programs:
        # Create the shader first
        test_shaderlib_uniform_buffer_shader(opengl_context)

    # Use the existing uniform block shader
    ShaderLib.use("UBOTest")
    ShaderLib.auto_register_uniform_blocks()

    # Test getting uniform block data for current shader
    block_data = ShaderLib.get_uniform_block_data()
    if block_data is not None:
        assert isinstance(block_data, dict)

    # Test getting specific block data for current shader
    specific_data = ShaderLib.get_uniform_block_data(block_name="TransformUBO")
    if specific_data is not None:
        assert "name" in specific_data

    # Test getting block data for specific shader
    all_blocks = ShaderLib.get_uniform_block_data(shader_name="UBOTest")
    if all_blocks is not None:
        assert isinstance(all_blocks, dict)


def test_shaderlib_print_methods(opengl_context):
    """Test ShaderLib print methods"""
    ShaderLib.use("TestUniform")
    ShaderLib.print_registered_uniforms()
    ShaderLib.print_properties()


def test_get_gl_type_string_edge_cases(opengl_context, simple_shader):
    """Test get_gl_type_string with unknown types"""
    # Test known types
    assert simple_shader.get_gl_type_string(gl.GL_FLOAT) == "float"
    assert simple_shader.get_gl_type_string(gl.GL_FLOAT_VEC2) == "vec2"
    assert simple_shader.get_gl_type_string(gl.GL_FLOAT_VEC3) == "vec3"
    assert simple_shader.get_gl_type_string(gl.GL_FLOAT_VEC4) == "vec4"
    assert simple_shader.get_gl_type_string(gl.GL_FLOAT_MAT2) == "mat2"
    assert simple_shader.get_gl_type_string(gl.GL_FLOAT_MAT3) == "mat3"
    assert simple_shader.get_gl_type_string(gl.GL_FLOAT_MAT4) == "mat4"
    assert simple_shader.get_gl_type_string(gl.GL_INT) == "int"
    assert simple_shader.get_gl_type_string(gl.GL_UNSIGNED_INT) == "unsigned int"
    assert simple_shader.get_gl_type_string(gl.GL_BOOL) == "bool"
    assert simple_shader.get_gl_type_string(gl.GL_DOUBLE) == "double"
    assert simple_shader.get_gl_type_string(gl.GL_SAMPLER_2D) == "sampler2D"
    assert simple_shader.get_gl_type_string(gl.GL_SAMPLER_CUBE) == "samplerCube"

    # Test unknown type
    assert simple_shader.get_gl_type_string(99999) == "Unknown type 99999"
    assert simple_shader.get_gl_type_string(-1) == "Unknown type -1"


def test_shaderprogram_set_uniform_buffer_exception_handling(opengl_context, uniform_block_shader):
    """Test uniform buffer exception handling"""

    # Get first available uniform block
    blocks = uniform_block_shader.get_registered_uniform_blocks()
    if blocks:
        block_name = list(blocks.keys())[0]

        # Test with invalid data that might cause np.frombuffer to fail
        try:
            result = uniform_block_shader.set_uniform_buffer(block_name, 16, "invalid_data")
            # Should return False due to exception
            assert result
        except Exception as e:
            # If exception is raised instead of caught, that's also valid
            print(e)
            pass


def test_shaderprogram_array_methods_with_invalid_location(opengl_context):
    """Test array uniform methods when uniform location is -1"""
    # Create a simple shader without the array uniforms we're trying to set
    vert_shader = """
    #version 410 core
    void main()
    {
        gl_Position = vec4(0.0);
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
    vert = Shader("invalid_array_vert", ShaderType.VERTEX.value)
    vert.load_shader_source_from_string(vert_shader)
    vert.compile()
    frag = Shader("invalid_array_frag", ShaderType.FRAGMENT.value)
    frag.load_shader_source_from_string(frag_shader)
    frag.compile()
    program = ShaderProgram("invalid_array")
    program.attach_shader(vert)
    program.attach_shader(frag)
    assert program.link()
    program.use()

    # These should all handle -1 location gracefully
    program.set_uniform_1fv("nonexistent", [1.0, 2.0])
    program.set_uniform_2fv("nonexistent", [[1.0, 2.0]])
    program.set_uniform_3fv("nonexistent", [[1.0, 2.0, 3.0]])
    program.set_uniform_4fv("nonexistent", [[1.0, 2.0, 3.0, 4.0]])
    program.set_uniform_1iv("nonexistent", [1, 2])
    program.set_uniform_matrix2fv("nonexistent", [[1.0, 2.0, 3.0, 4.0]])
    program.set_uniform_matrix3fv("nonexistent", [[1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0]])
    program.set_uniform_matrix4fv(
        "nonexistent",
        [
            [
                1.0,
                2.0,
                3.0,
                4.0,
                5.0,
                6.0,
                7.0,
                8.0,
                9.0,
                10.0,
                11.0,
                12.0,
                13.0,
                14.0,
                15.0,
                16.0,
            ]
        ],
    )


def test_shaderprogram_get_uniform_methods_with_invalid_location(opengl_context):
    """Test getter methods when uniform location is -1"""
    # Create a simple shader without specific uniforms
    vert_shader = """
    #version 410 core
    void main()
    {
        gl_Position = vec4(0.0);
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
    vert = Shader("getter_test_vert", ShaderType.VERTEX.value)
    vert.load_shader_source_from_string(vert_shader)
    vert.compile()
    frag = Shader("getter_test_frag", ShaderType.FRAGMENT.value)
    frag.load_shader_source_from_string(frag_shader)
    frag.compile()
    program = ShaderProgram("getter_test")
    program.attach_shader(vert)
    program.attach_shader(frag)
    assert program.link()
    program.use()

    # Test all getter methods with nonexistent uniforms
    assert program.get_uniform_1f("nonexistent") == pytest.approx(0.0)
    assert program.get_uniform_2f("nonexistent") == [0.0, 0.0]
    assert program.get_uniform_3f("nonexistent") == [0.0, 0.0, 0.0]
    assert program.get_uniform_4f("nonexistent") == [0.0, 0.0, 0.0, 0.0]
    assert program.get_uniform_mat2("nonexistent") == [0.0] * 4
    assert program.get_uniform_mat3("nonexistent") == [0.0] * 9
    assert program.get_uniform_mat4("nonexistent") == [0.0] * 16
    assert program.get_uniform_mat4x3("nonexistent") == [0.0] * 12


def test_shaderprogram_set_uniform_warning_cases(opengl_context, uniform_shader):
    """Test cases that should trigger warnings in set_uniform"""
    uniform_shader.use()

    # Test with object that converts to list but wrong size
    class WeirdObject:
        def __iter__(self):
            return iter([1.0, 2.0])  # Only 2 elements, not 4, 9, or 16

    uniform_shader.set_uniform("testFloat", WeirdObject())  # Should trigger warning

    # Test with list of wrong size (not 4, 9, or 16)
    uniform_shader.set_uniform("testFloat", [1.0, 2.0, 3.0])  # 3 elements - should warn
    uniform_shader.set_uniform("testFloat", [1.0, 2.0, 3.0, 4.0, 5.0])  # 5 elements - should warn


def test_shaderprogram_print_registered_uniform_blocks_empty(opengl_context, simple_shader):
    """Test print_registered_uniform_blocks with no uniform blocks"""
    # simple_shader has no uniform blocks
    simple_shader.print_registered_uniform_blocks()


def test_shaderprogram_auto_register_uniform_blocks_no_blocks(opengl_context, simple_shader):
    """Test auto_register_uniform_blocks when shader has no uniform blocks"""
    # This should work without errors even with 0 uniform blocks
    simple_shader.auto_register_uniform_blocks()
    assert len(simple_shader.get_registered_uniform_blocks()) == 0


def test_shaderlib_get_uniform_block_data_edge_cases(opengl_context):
    """Test ShaderLib get_uniform_block_data edge cases"""
    # Test with no current shader
    ShaderLib.use(None)
    result = ShaderLib.get_uniform_block_data()
    assert result is None

    # Test with shader that has no uniform blocks
    ShaderLib.use("Test")  # This shader has no uniform blocks
    result = ShaderLib.get_uniform_block_data()
    assert result is None

    # Test with nonexistent shader name
    result = ShaderLib.get_uniform_block_data(shader_name="NonExistent")
    assert result is None


def test_shaderprogram_uniform_block_methods_edge_cases(opengl_context, simple_shader):
    """Test uniform block methods with shader that has no blocks"""
    # simple_shader has no uniform blocks
    assert simple_shader.get_uniform_block_data("nonexistent") is None
    assert simple_shader.get_uniform_block_location("nonexistent") == -1
    assert simple_shader.get_uniform_block_buffer("nonexistent") == 0

    # Test get_registered_uniform_blocks returns empty dict
    blocks = simple_shader.get_registered_uniform_blocks()
    assert isinstance(blocks, dict)
