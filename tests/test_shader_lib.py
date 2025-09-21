from unittest.mock import MagicMock, patch

from src.ngl.shader_lib import DefaultShader, ShaderLib, _ShaderLib


def test_edit_shader_returns_false_if_missing():
    # Line 48-49: edit_shader returns False if shader not found
    result = ShaderLib.edit_shader("missing_shader", "foo", "bar")
    assert result is False


def test_reset_edits_noop_if_missing():
    # Line 60-61: reset_edits does nothing if shader not found
    # Should not raise
    ShaderLib.reset_edits("missing_shader")


def test_print_registered_uniforms_logs_error_if_missing(caplog):
    # Line 65-66: print_registered_uniforms logs error if shader not found
    ShaderLib.print_registered_uniforms("missing_shader")
    assert any("not found" in r for r in caplog.text.splitlines())


def test_print_registered_uniforms_logs_for_current_shader(caplog):
    # Line 65-66: print_registered_uniforms logs error if current shader not found
    lib = _ShaderLib()
    lib._current_shader = "not_a_shader"
    lib.print_registered_uniforms()
    assert any("not found" in r for r in caplog.text.splitlines())


def test_print_properties_warns_if_no_active_shader(caplog):
    # Line 91: print_properties warns if no active shader
    lib = _ShaderLib()
    lib._current_shader = None
    lib.print_properties()
    assert any("Warning no currently active shader" in r for r in caplog.text.splitlines())


def test_print_properties_warns_if_shader_not_in_programs(caplog):
    # Line 91: print_properties warns if current shader not in programs
    lib = _ShaderLib()
    lib._current_shader = "not_a_shader"
    lib.print_properties()
    assert any("Warning no currently active shader" in r for r in caplog.text.splitlines())


def test_load_default_shaders_loads_and_sets_flag(monkeypatch):
    # Line 172: _load_default_shaders sets _default_shaders_loaded True
    lib = _ShaderLib()
    called = {}

    def fake_load_shader(name, vert, frag, geo=None, exit_on_error=True):
        called[name] = (vert, frag)
        return True

    monkeypatch.setattr(lib, "load_shader", fake_load_shader)
    lib._load_default_shaders()
    assert lib._default_shaders_loaded is True
    # Should have loaded all DefaultShader keys
    for key in DefaultShader:
        assert key in called


def test_use_loads_default_shaders_if_needed(monkeypatch):
    # Line 209-215: use loads default shaders if not loaded
    lib = _ShaderLib()
    lib._default_shaders_loaded = False
    lib._shader_programs = {}
    called = {}

    def fake_load_default_shaders():
        called["loaded"] = True
        lib._default_shaders_loaded = True

    monkeypatch.setattr(lib, "_load_default_shaders", fake_load_default_shaders)
    monkeypatch.setattr(lib, "get_current_shader_name", lambda: None)
    with patch("src.ngl.shader_lib.gl") as fake_gl:
        lib.use("missing_shader")
    assert called.get("loaded", False)


def test_use_sets_current_shader_and_calls_use(monkeypatch):
    # Line 218-233: use sets current shader and calls use on ShaderProgram
    lib = _ShaderLib()
    prog = MagicMock()
    lib._shader_programs["my_shader"] = prog
    lib._default_shaders_loaded = True
    lib.use("my_shader")
    assert lib._current_shader == "my_shader"
    prog.use.assert_called_once()


def test_use_handles_missing_shader(monkeypatch):
    # Line 218-233: use handles missing shader, logs error, sets current_shader None
    lib = _ShaderLib()
    lib._shader_programs = {}
    lib._default_shaders_loaded = True
    with patch("src.ngl.shader_lib.gl") as fake_gl, patch("src.ngl.shader_lib.logger") as fake_logger:
        lib.use("missing_shader")
        fake_logger.error.assert_called()
        fake_gl.glUseProgram.assert_called_with(0)
    assert lib._current_shader is None


def test_load_shader_fragment_compile_fail(monkeypatch, caplog):
    lib = _ShaderLib()
    monkeypatch.setattr("src.ngl.shader_lib.ShaderProgram", MagicMock())
    fake_shader = MagicMock()
    fake_shader.compile.return_value = True
    monkeypatch.setattr("src.ngl.shader_lib.Shader", lambda *a, **kw: fake_shader)
    # Simulate fragment shader compile fail
    fake_shader.compile.side_effect = [True, False]
    result = lib.load_shader("fail_frag", "vert", "frag")
    assert result is False
    assert any("Failed to compile fragment shader" in r for r in caplog.text.splitlines())


def test_load_shader_geometry_compile_fail(monkeypatch, caplog):
    lib = _ShaderLib()
    monkeypatch.setattr("src.ngl.shader_lib.ShaderProgram", MagicMock())
    fake_shader = MagicMock()
    fake_shader.compile.return_value = True
    monkeypatch.setattr("src.ngl.shader_lib.Shader", lambda *a, **kw: fake_shader)
    # Simulate geometry shader compile fail
    fake_shader.compile.side_effect = [True, True, False]
    result = lib.load_shader("fail_geo", "vert", "frag", geo="geo")
    assert result is False
    assert any("Failed to compile geometry shader" in r for r in caplog.text.splitlines())


def test_load_shader_link_fail(monkeypatch, caplog):
    lib = _ShaderLib()
    fake_program = MagicMock()
    fake_program.link.return_value = False
    monkeypatch.setattr("src.ngl.shader_lib.ShaderProgram", lambda *a, **kw: fake_program)
    fake_shader = MagicMock()
    fake_shader.compile.return_value = True
    monkeypatch.setattr("src.ngl.shader_lib.Shader", lambda *a, **kw: fake_shader)
    result = lib.load_shader("fail_link", "vert", "frag")
    assert result is False
    assert any("Failed to link shader program" in r for r in caplog.text.splitlines())


def test_get_program_id_returns_id(monkeypatch):
    lib = _ShaderLib()
    prog = MagicMock()
    prog.get_id.return_value = 42
    lib._shader_programs["myprog"] = prog
    assert lib.get_program_id("myprog") == 42
    assert lib.get_program_id("missing") is None


def test_print_registered_uniforms_calls_method(monkeypatch):
    lib = _ShaderLib()
    prog = MagicMock()
    lib._shader_programs["myprog"] = prog
    lib.print_registered_uniforms("myprog")
    prog.print_registered_uniforms.assert_called_once()


def test_print_properties_calls_method(monkeypatch, caplog):
    lib = _ShaderLib()
    prog = MagicMock()
    lib._shader_programs["myprog"] = prog
    lib._current_shader = "myprog"
    lib.print_properties()
    prog.print_properties.assert_called_once()
    # Should log info about printing properties
    assert any("Printing Properties for ShaderProgram" in r for r in caplog.text.splitlines())
