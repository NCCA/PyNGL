#!/usr/bin/env -S uv run --active --script
"""OpenGL pipeline tour demo, mirroring `uv run python -m ncca.ngl.webgpu`.

Cycles through a series of small scenes every 1.5 seconds, each one built with a
different combination of techniques from the ncca.ngl.opengl stack: SimpleVAO
(points/lines/triangles, single and per-vertex colour), SimpleIndexVAO (indexed
mesh), MultiBufferVAO (separate position/normal buffers), and the Primitives
registry drawn with the DIFFUSE and CHECKER default shaders.
"""

import sys
import traceback
from pathlib import Path

import numpy as np
import OpenGL.GL as gl
from PySide6.QtCore import Qt, QTimer, QTimerEvent
from PySide6.QtGui import QKeyEvent, QSurfaceFormat
from PySide6.QtOpenGL import QOpenGLWindow
from PySide6.QtWidgets import QApplication

from ncca.ngl import (
    Mat3,
    Mat4,
    Prims,
    Transform,
    Vec3,
    calc_normal,
    logger,
    look_at,
    perspective,
)
from ncca.ngl.opengl import (
    DefaultShader,
    IndexVertexData,
    Primitives,
    PySideEventHandlingMixin,
    ShaderLib,
    Text,
    VAOFactory,
    VAOType,
    VertexData,
    __version__,
)

NUM_POINTS = 400
NUM_LINE_SEGMENTS = 60
NUM_TRIANGLES = 80
STAGE_DURATION_MS = 1500

# Reference icosahedron vertices with a fixed per-vertex colour, used to
# demonstrate SimpleIndexVAO with an interleaved position + colour buffer.
_ICOSAHEDRON_VERTS = [
    ((-0.262865, 0.0, 0.425325), (1.0, 0.0, 0.0)),
    ((0.262865, 0.0, 0.425325), (1.0, 0.55, 0.0)),
    ((-0.262865, 0.0, -0.425325), (1.0, 0.0, 1.0)),
    ((0.262865, 0.0, -0.425325), (0.0, 1.0, 0.0)),
    ((0.0, 0.425325, 0.262865), (0.0, 0.0, 1.0)),
    ((0.0, 0.425325, -0.262865), (0.29, 0.51, 0.0)),
    ((0.0, -0.425325, 0.262865), (0.5, 0.0, 0.5)),
    ((0.0, -0.425325, -0.262865), (1.0, 1.0, 1.0)),
    ((0.425325, 0.262865, 0.0), (0.0, 1.0, 1.0)),
    ((-0.425325, 0.262865, 0.0), (0.0, 0.0, 0.0)),
    ((0.425325, -0.262865, 0.0), (0.12, 0.56, 1.0)),
    ((-0.425325, -0.262865, 0.0), (0.86, 0.08, 0.24)),
]
_ICOSAHEDRON_INDICES = [
    0, 6, 1, 0, 11, 6, 1, 4, 0, 1, 8, 4, 1, 10, 8, 2, 5, 3,
    2, 9, 5, 2, 11, 9, 3, 7, 2, 3, 10, 7, 4, 8, 5, 4, 9, 0,
    5, 8, 3, 5, 9, 4, 6, 10, 1, 6, 11, 7, 7, 10, 6, 7, 11, 2,
    8, 10, 3, 9, 11, 0,
]  # fmt: skip

# A small "boid" mesh built from four triangles, used to demonstrate
# MultiBufferVAO with position and normal held in separate buffers.
_BOID_VERTS = [
    (0.0, 1.0, 1.0), (0.0, 0.0, -1.0), (-0.5, 0.0, 1.0),
    (0.0, 1.0, 1.0), (0.0, 0.0, -1.0), (0.5, 0.0, 1.0),
    (0.0, 1.0, 1.0), (0.0, 0.0, 1.5), (-0.5, 0.0, 1.0),
    (0.0, 1.0, 1.0), (0.0, 0.0, 1.5), (0.5, 0.0, 1.0),
]  # fmt: skip


class OpenGLPipelineDemo(PySideEventHandlingMixin, QOpenGLWindow):
    """Cycles through OpenGL VAO/shader techniques, one scene at a time."""

    def __init__(self) -> None:
        """Set up event handling, window state, and demo stages."""
        super().__init__()
        self.setup_event_handling(
            rotation_sensitivity=0.5,
            translation_sensitivity=0.01,
            zoom_sensitivity=0.1,
            initial_position=Vec3(0, 0, -2),
        )
        self.setTitle(f"ncca-ngl OpenGL Pipeline Demo {__version__}")
        self.window_width = 1024
        self.window_height = 720
        self.view = Mat4()
        self.project = Mat4()
        self.animate = True
        self.rotation = 0.0
        self.stage_index = 0
        self.stages = []
        self.stage_timer: QTimer | None = None

    def initializeGL(self) -> None:
        """Initialize the GL context, shaders, primitives, and stage list."""
        self.makeCurrent()
        # Qt's own context/surface setup can leave a stale error in the queue
        # before user code runs its first GL call; drain it so PyOpenGL's
        # per-call error checking doesn't misattribute it to glEnable below.
        while gl.glGetError() != gl.GL_NO_ERROR:
            pass
        gl.glEnable(gl.GL_DEPTH_TEST)
        gl.glEnable(gl.GL_MULTISAMPLE)
        self.view = look_at(Vec3(0, 1, 10), Vec3(0, 0, 0), Vec3(0, 1, 0))

        shader_dir = Path(__file__).parent / "pipeline_demo_shaders"
        ShaderLib.load_shader(
            "PerVertexColour",
            str(shader_dir / "pervertex_colour_vertex.glsl"),
            str(shader_dir / "pervertex_colour_fragment.glsl"),
        )

        Primitives.load_default_primitives()
        Primitives.create(Prims.SPHERE, "demo_sphere", 0.6, 32)
        Primitives.create(Prims.TORUS, "demo_torus", 0.3, 0.8, 32, 32)

        font_path = (
            Path(__file__).resolve().parents[4] / "tests" / "files" / "Arial.ttf"
        )
        Text.add_font("Arial", str(font_path), 22)
        Text.set_screen_size(self.window_width, self.window_height)

        self._build_geometry()
        self._build_vaos()

        self.stages = [
            ("SimpleVAO / GL_POINTS - multi-colour", (0.10, 0.10, 0.30, 1.0), self._draw_points_multi),
            ("SimpleVAO / GL_POINTS - single colour", (0.30, 0.10, 0.10, 1.0), self._draw_points_single),
            ("SimpleVAO / GL_LINES - multi-colour", (0.10, 0.30, 0.10, 1.0), self._draw_lines_multi),
            ("SimpleVAO / GL_LINES - single colour", (0.30, 0.30, 0.10, 1.0), self._draw_lines_single),
            ("SimpleVAO / GL_TRIANGLES - multi-colour", (0.30, 0.10, 0.30, 1.0), self._draw_triangles_multi),
            ("SimpleVAO / GL_TRIANGLES - single colour", (0.10, 0.30, 0.30, 1.0), self._draw_triangles_single),
            ("SimpleIndexVAO - indexed icosahedron", (0.20, 0.15, 0.05, 1.0), self._draw_indexed_mesh),
            ("MultiBufferVAO - separate position/normal buffers", (0.05, 0.15, 0.30, 1.0), self._draw_multi_buffer),
            ("Primitives - stock & parametric meshes (diffuse)", (0.15, 0.15, 0.15, 1.0), self._draw_primitives_diffuse),
            ("Primitives - checker shader", (0.20, 0.20, 0.05, 1.0), self._draw_primitives_checker),
        ]  # fmt: skip

        self.startTimer(16)
        self.stage_timer = QTimer()
        self.stage_timer.timeout.connect(self._advance_stage)
        self.stage_timer.start(STAGE_DURATION_MS)

    def _build_geometry(self) -> None:
        rng = np.random.default_rng()

        point_positions = rng.uniform(-3.0, 3.0, (NUM_POINTS, 3)).astype(np.float32)
        point_colours = rng.random((NUM_POINTS, 3)).astype(np.float32)
        self.points_interleaved = np.hstack([point_positions, point_colours])

        line_positions = rng.uniform(-3.0, 3.0, (NUM_LINE_SEGMENTS * 2, 3)).astype(
            np.float32
        )
        line_colours = rng.random((NUM_LINE_SEGMENTS * 2, 3)).astype(np.float32)
        self.lines_interleaved = np.hstack([line_positions, line_colours])

        triangle_positions = np.zeros((NUM_TRIANGLES * 3, 3), dtype=np.float32)
        triangle_colours = rng.random((NUM_TRIANGLES * 3, 3)).astype(np.float32)
        for i in range(NUM_TRIANGLES):
            centre = rng.uniform(-2.5, 2.5, 3)
            radius = rng.uniform(0.15, 0.45)
            offsets = rng.normal(size=(3, 3))
            offsets /= np.linalg.norm(offsets, axis=1, keepdims=True)
            triangle_positions[i * 3 : i * 3 + 3] = centre + offsets * radius
        self.triangles_interleaved = np.hstack(
            [triangle_positions.astype(np.float32), triangle_colours]
        )

        icosahedron_rows = [pos + colour for pos, colour in _ICOSAHEDRON_VERTS]
        self.icosahedron_interleaved = np.array(icosahedron_rows, dtype=np.float32)

        boid_positions = np.array(_BOID_VERTS, dtype=np.float32)
        boid_normals = np.zeros_like(boid_positions)
        for i in range(0, len(boid_positions), 3):
            v0 = Vec3(*boid_positions[i])
            v1 = Vec3(*boid_positions[i + 1])
            v2 = Vec3(*boid_positions[i + 2])
            n = calc_normal(v0, v1, v2)
            boid_normals[i] = boid_normals[i + 1] = boid_normals[i + 2] = n.to_list()
        self.boid_positions = boid_positions
        self.boid_normals = boid_normals

    def _build_vaos(self) -> None:
        self.vao_points = VAOFactory.create_vao(VAOType.SIMPLE, gl.GL_POINTS)
        with self.vao_points:
            data = VertexData(
                data=self.points_interleaved.flatten(),
                size=len(self.points_interleaved),
            )
            self.vao_points.set_data(data)
            self.vao_points.set_vertex_attribute_pointer(0, 3, gl.GL_FLOAT, 24, 0)
            self.vao_points.set_vertex_attribute_pointer(1, 3, gl.GL_FLOAT, 24, 12)

        self.vao_lines = VAOFactory.create_vao(VAOType.SIMPLE, gl.GL_LINES)
        with self.vao_lines:
            data = VertexData(
                data=self.lines_interleaved.flatten(), size=len(self.lines_interleaved)
            )
            self.vao_lines.set_data(data)
            self.vao_lines.set_vertex_attribute_pointer(0, 3, gl.GL_FLOAT, 24, 0)
            self.vao_lines.set_vertex_attribute_pointer(1, 3, gl.GL_FLOAT, 24, 12)

        self.vao_triangles = VAOFactory.create_vao(VAOType.SIMPLE, gl.GL_TRIANGLES)
        with self.vao_triangles:
            data = VertexData(
                data=self.triangles_interleaved.flatten(),
                size=len(self.triangles_interleaved),
            )
            self.vao_triangles.set_data(data)
            self.vao_triangles.set_vertex_attribute_pointer(0, 3, gl.GL_FLOAT, 24, 0)
            self.vao_triangles.set_vertex_attribute_pointer(1, 3, gl.GL_FLOAT, 24, 12)

        self.vao_index = VAOFactory.create_vao(VAOType.SIMPLE_INDEX, gl.GL_TRIANGLES)
        with self.vao_index:
            data = IndexVertexData(
                data=self.icosahedron_interleaved.flatten(),
                size=len(_ICOSAHEDRON_INDICES),
                indices=_ICOSAHEDRON_INDICES,
                index_type=gl.GL_UNSIGNED_SHORT,
            )
            self.vao_index.set_data(data)
            self.vao_index.set_vertex_attribute_pointer(0, 3, gl.GL_FLOAT, 24, 0)
            self.vao_index.set_vertex_attribute_pointer(1, 3, gl.GL_FLOAT, 24, 12)

        self.vao_multi_buffer = VAOFactory.create_vao(
            VAOType.MULTI_BUFFER, gl.GL_TRIANGLES
        )
        with self.vao_multi_buffer:
            data = VertexData(
                data=self.boid_positions.flatten(), size=len(self.boid_positions)
            )
            self.vao_multi_buffer.set_data(data)
            self.vao_multi_buffer.set_vertex_attribute_pointer(0, 3, gl.GL_FLOAT, 0, 0)
            data = VertexData(
                data=self.boid_normals.flatten(), size=len(self.boid_normals)
            )
            self.vao_multi_buffer.set_data(data)
            self.vao_multi_buffer.set_vertex_attribute_pointer(1, 3, gl.GL_FLOAT, 0, 0)

    def _current_mvp(self) -> Mat4:
        mv = self.view @ self.mouse_global_tx
        return self.project @ mv

    def _draw_points_multi(self) -> None:
        ShaderLib.use("PerVertexColour")
        ShaderLib.set_uniform("MVP", self._current_mvp())
        gl.glPointSize(8.0)
        with self.vao_points:
            self.vao_points.draw()

    def _draw_points_single(self) -> None:
        ShaderLib.use(DefaultShader.COLOUR)
        ShaderLib.set_uniform("Colour", 1.0, 1.0, 0.0, 1.0)
        ShaderLib.set_uniform("MVP", self._current_mvp())
        gl.glPointSize(6.0)
        with self.vao_points:
            self.vao_points.draw()

    def _draw_lines_multi(self) -> None:
        ShaderLib.use("PerVertexColour")
        ShaderLib.set_uniform("MVP", self._current_mvp())
        with self.vao_lines:
            self.vao_lines.draw()

    def _draw_lines_single(self) -> None:
        ShaderLib.use(DefaultShader.COLOUR)
        ShaderLib.set_uniform("Colour", 1.0, 0.0, 1.0, 1.0)
        ShaderLib.set_uniform("MVP", self._current_mvp())
        with self.vao_lines:
            self.vao_lines.draw()

    def _draw_triangles_multi(self) -> None:
        ShaderLib.use("PerVertexColour")
        ShaderLib.set_uniform("MVP", self._current_mvp())
        with self.vao_triangles:
            self.vao_triangles.draw()

    def _draw_triangles_single(self) -> None:
        ShaderLib.use(DefaultShader.COLOUR)
        ShaderLib.set_uniform("Colour", 1.0, 0.5, 0.0, 1.0)
        ShaderLib.set_uniform("MVP", self._current_mvp())
        with self.vao_triangles:
            self.vao_triangles.draw()

    def _draw_indexed_mesh(self) -> None:
        tx = Transform()
        tx.set_scale(4, 4, 4)
        ShaderLib.use("PerVertexColour")
        mv = self.view @ self.mouse_global_tx @ tx.matrix()
        ShaderLib.set_uniform("MVP", self.project @ mv)
        with self.vao_index:
            self.vao_index.draw()

    def _draw_multi_buffer(self) -> None:
        ShaderLib.use(DefaultShader.DIFFUSE)
        ShaderLib.set_uniform("lightPos", 1.0, 1.0, 1.0)
        ShaderLib.set_uniform("lightDiffuse", 1.0, 1.0, 1.0, 1.0)
        ShaderLib.set_uniform("Colour", 0.85, 0.65, 0.2, 1.0)
        mv = self.view @ self.mouse_global_tx
        mvp = self.project @ mv
        normal_matrix = Mat3.from_mat4(mv).inverse().transposed()
        ShaderLib.set_uniform("MVP", mvp)
        ShaderLib.set_uniform("MV", mv)
        ShaderLib.set_uniform("normalMatrix", normal_matrix)
        with self.vao_multi_buffer:
            self.vao_multi_buffer.draw()

    def _draw_primitives_diffuse(self) -> None:
        ShaderLib.use(DefaultShader.DIFFUSE)
        ShaderLib.set_uniform("lightPos", 1.0, 1.0, 1.0)
        ShaderLib.set_uniform("lightDiffuse", 1.0, 1.0, 1.0, 1.0)
        prims = [
            ("teapot", Vec3(-2.0, 0, 0), (1.0, 0.0, 0.0, 1.0)),
            ("demo_sphere", Vec3(0.0, 0, 0), (0.0, 0.3, 1.0, 1.0)),
            ("cube", Vec3(2.0, 0, 0), (0.0, 1.0, 0.0, 1.0)),
            ("demo_torus", Vec3(0.0, 1.6, 0), (1.0, 1.0, 0.0, 1.0)),
        ]
        for name, position, colour in prims:
            tx = Transform()
            tx.set_position(position)
            mv = self.view @ self.mouse_global_tx @ tx.matrix()
            mvp = self.project @ mv
            normal_matrix = Mat3.from_mat4(mv).inverse().transposed()
            ShaderLib.set_uniform("MVP", mvp)
            ShaderLib.set_uniform("MV", mv)
            ShaderLib.set_uniform("normalMatrix", normal_matrix)
            ShaderLib.set_uniform("Colour", *colour)
            Primitives.draw(name)

    def _draw_primitives_checker(self) -> None:
        ShaderLib.use(DefaultShader.CHECKER)
        ShaderLib.set_uniform("lightPos", 1.0, 1.0, 1.0)
        ShaderLib.set_uniform("lightDiffuse", 1.0, 1.0, 1.0, 1.0)
        ShaderLib.set_uniform("colour1", 1.0, 1.0, 1.0, 1.0)
        ShaderLib.set_uniform("colour2", 0.15, 0.15, 0.15, 1.0)
        ShaderLib.set_uniform("checkOn", True)
        ShaderLib.set_uniform("checkSize", 20.0)
        prims = [
            ("teapot", Vec3(-2.0, 0, 0)),
            ("demo_sphere", Vec3(0.0, 0, 0)),
            ("cube", Vec3(2.0, 0, 0)),
            ("demo_torus", Vec3(0.0, 1.6, 0)),
        ]
        for name, position in prims:
            tx = Transform()
            tx.set_position(position)
            mv = self.view @ self.mouse_global_tx @ tx.matrix()
            mvp = self.project @ mv
            normal_matrix = Mat3.from_mat4(mv).inverse().transposed()
            ShaderLib.set_uniform("MVP", mvp)
            ShaderLib.set_uniform("normalMatrix", normal_matrix)
            Primitives.draw(name)

    def paintGL(self) -> None:
        """Render the current demo stage."""
        self.makeCurrent()
        gl.glViewport(0, 0, self.window_width, self.window_height)
        label, background, draw_stage = self.stages[self.stage_index]
        gl.glClearColor(*background)
        gl.glClear(gl.GL_COLOR_BUFFER_BIT | gl.GL_DEPTH_BUFFER_BIT)

        rot_x = Mat4().rotate_x(self.spin_x_face)
        rot_y = Mat4().rotate_y(self.spin_y_face)
        auto_rotation = Mat4().rotate_y(self.rotation)
        self.mouse_global_tx = rot_y @ rot_x @ auto_rotation
        self.mouse_global_tx[3, 0] = self.model_position.x
        self.mouse_global_tx[3, 1] = self.model_position.y
        self.mouse_global_tx[3, 2] = self.model_position.z

        draw_stage()

        Text.render_text(
            "Arial",
            10,
            30,
            f"{self.stage_index + 1}/{len(self.stages)}  {label}",
            Vec3(1.0, 1.0, 0.2),
        )
        Text.render_text(
            "Arial",
            10,
            56,
            "Space: pause  Left/Right: switch  A: toggle auto-switch  Esc: quit",
            Vec3(0.8, 0.8, 0.8),
        )

    def resizeGL(self, w: int, h: int) -> None:
        """Update viewport size, projection matrix, and text screen size."""
        self.window_width = int(w * self.devicePixelRatio())
        self.window_height = int(h * self.devicePixelRatio())
        self.project = perspective(45.0, float(w) / h if h > 0 else 1.0, 0.01, 350.0)
        Text.set_screen_size(self.window_width, self.window_height)

    def timerEvent(self, event: QTimerEvent) -> None:
        """Advance the rotation animation on each timer tick."""
        if self.animate:
            self.rotation += 0.5
        self.update()

    def _advance_stage(self) -> None:
        self.stage_index = (self.stage_index + 1) % len(self.stages)
        logger.info(f"Switched to {self.stages[self.stage_index][0]}")
        self.update()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle demo shortcuts, delegating the rest to the mixin."""
        key = event.key()
        if key == Qt.Key_Space:
            self.animate = not self.animate
        elif key == Qt.Key_Left:
            self.stage_index = (self.stage_index - 1) % len(self.stages)
            logger.info(f"Switched to {self.stages[self.stage_index][0]}")
        elif key == Qt.Key_Right:
            self.stage_index = (self.stage_index + 1) % len(self.stages)
            logger.info(f"Switched to {self.stages[self.stage_index][0]}")
        elif key == Qt.Key_A:
            if self.stage_timer.isActive():
                self.stage_timer.stop()
                logger.info("Auto-switch disabled")
            else:
                self.stage_timer.start(STAGE_DURATION_MS)
                logger.info("Auto-switch enabled")
        else:
            super().keyPressEvent(event)
            return
        self.update()


class DebugApplication(QApplication):
    """QApplication that surfaces exceptions raised inside Qt event handlers."""

    def __init__(self, argv: list[str]) -> None:
        """Create the application in debug mode."""
        super().__init__(argv)
        logger.info("Running in full debug mode")

    def notify(self, receiver: object, event: object) -> bool:
        """Dispatch the event, printing any exception before re-raising."""
        try:
            return super().notify(receiver, event)
        except Exception:
            traceback.print_exc()
            raise


def main() -> None:
    """Configure the GL surface format and run the demo application."""
    surface_format = QSurfaceFormat()
    surface_format.setSamples(4)
    surface_format.setMajorVersion(4)
    surface_format.setMinorVersion(1)
    surface_format.setProfile(QSurfaceFormat.CoreProfile)
    surface_format.setDepthBufferSize(24)
    QSurfaceFormat.setDefaultFormat(surface_format)

    if len(sys.argv) > 1 and "--debug" in sys.argv:
        app = DebugApplication(sys.argv)
    else:
        app = QApplication(sys.argv)

    window = OpenGLPipelineDemo()
    window.resize(1024, 720)
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    print(f"ncca-ngl.OpenGL Pipeline Demo {__version__}")
    main()
