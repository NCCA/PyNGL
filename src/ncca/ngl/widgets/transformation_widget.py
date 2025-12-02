import sys

from OpenGL.GL import *
from PySide6.QtCore import Property, QEasingCurve, QPoint, QPropertyAnimation, Signal, Slot
from PySide6.QtGui import QQuaternion
from PySide6.QtOpenGLWidgets import QOpenGLWidget
from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from ncca.ngl.mat4 import Mat4
from ncca.ngl.prim_data import PrimData, Prims
from ncca.ngl.quaternion import Quaternion
from ncca.ngl.shader_lib import ShaderLib
from ncca.ngl.simple_vao import SimpleVAO, VertexData
from ncca.ngl.transform import Transform
from ncca.ngl.vec3 import Vec3


class TransformationWidget(QOpenGLWidget):
    matrix_updated = Signal(Mat4)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.transform = Transform()
        self.projection = Mat4()
        self.view = Mat4()
        self.mouse_pos = QPoint()
        self.vao = SimpleVAO()

        self.face_rotations = {
            "front": Quaternion.from_axis_angle(Vec3(0, 1, 0), 0),
            "back": Quaternion.from_axis_angle(Vec3(0, 1, 0), 180),
            "left": Quaternion.from_axis_angle(Vec3(0, 1, 0), -90),
            "right": Quaternion.from_axis_angle(Vec3(0, 1, 0), 90),
            "top": Quaternion.from_axis_angle(Vec3(1, 0, 0), -90),
            "bottom": Quaternion.from_axis_angle(Vec3(1, 0, 0), 90),
        }

        self.face_ids = {
            1: "right",
            2: "left",
            3: "top",
            4: "bottom",
            5: "front",
            6: "back",
        }
        self.picking_fbo = None
        self.picking_texture = None
        self.depth_texture = None

    def initializeGL(self):
        glClearColor(0.4, 0.4, 0.4, 1.0)
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_MULTISAMPLE)

        # ShaderLib.load_shader("picking", "glsl/picking.vert", "glsl/picking.frag")
        # ShaderLib.load_shader("phong", "glsl/phong.vert", "glsl/phong.frag")

        # cube_data = PrimData.primitive(Prims.CUBE)
        # print(f"Cube data size: {cube_data.size}")
        # print(f"Cube data shape: {cube_data.shape}")
        # with self.vao:
        #     data = VertexData(data=cube_data, size=cube_data.size)
        #     self.vao.set_data(data)
        #     vert_data_size = 8 * 4  # 4 is sizeof float and 8 is x,y,z,nx,ny,nz,uv
        #     self.vao.set_vertex_attribute_pointer(0, 3, GL_FLOAT, vert_data_size, 0)
        #     self.vao.set_vertex_attribute_pointer(1, 3, GL_FLOAT, vert_data_size, Vec3.sizeof())
        #     self.vao.set_vertex_attribute_pointer(2, 2, GL_FLOAT, vert_data_size, 2 * Vec3.sizeof())
        #     self.vao.set_num_indices(cube_data.size // 8)

        self.view.look_at(Vec3(0, 0, 3), Vec3(0, 0, 0), Vec3(0, 1, 0))
        self.setFocus()

    def resizeGL(self, w, h):
        if h == 0:
            h = 1
        # self.projection.perspective(45, w / h, 0.01, 20)
        # self._create_picking_buffer(w, h)

    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        # if self.picking_fbo is None:
        #     self._create_picking_buffer(self.width(), self.height())
        # self._render_picking_pass()
        # self._render_scene_pass()
        # self.matrix_updated.emit(self.transform.get_matrix())

    def _create_picking_buffer(self, w, h):
        if self.picking_fbo is not None:
            glDeleteFramebuffers(1, [self.picking_fbo])
            glDeleteTextures(1, [self.picking_texture])
            glDeleteTextures(1, [self.depth_texture])

        self.picking_fbo = glGenFramebuffers(1)
        glBindFramebuffer(GL_FRAMEBUFFER, self.picking_fbo)

        self.picking_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.picking_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_RGB, w, h, 0, GL_RGB, GL_UNSIGNED_BYTE, None)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_COLOR_ATTACHMENT0, GL_TEXTURE_2D, self.picking_texture, 0)

        self.depth_texture = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, self.depth_texture)
        glTexImage2D(GL_TEXTURE_2D, 0, GL_DEPTH_COMPONENT, w, h, 0, GL_DEPTH_COMPONENT, GL_FLOAT, None)
        glFramebufferTexture2D(GL_FRAMEBUFFER, GL_DEPTH_ATTACHMENT, GL_TEXTURE_2D, self.depth_texture, 0)

        if glCheckFramebufferStatus(GL_FRAMEBUFFER) != GL_FRAMEBUFFER_COMPLETE:
            print("Framebuffer is not complete")

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def _render_picking_pass(self):
        glBindFramebuffer(GL_FRAMEBUFFER, self.picking_fbo)
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        ShaderLib.use("picking")
        mvp = self.projection @ self.view @ self.transform.get_matrix()
        ShaderLib.set_uniform("MVP", mvp)
        with self.vao:
            for i, face_id in self.face_ids.items():
                r = (i & 0x0000FF) / 255.0
                g = ((i & 0x00FF00) >> 8) / 255.0
                b = ((i & 0xFF0000) >> 16) / 255.0
                ShaderLib.set_uniform("face_id", Vec3(r, g, b))
                glDrawArrays(GL_TRIANGLES, (i - 1) * 6, 6)

        glBindFramebuffer(GL_FRAMEBUFFER, 0)

    def _render_scene_pass(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        ShaderLib.use("phong")
        mvp = self.projection @ self.view @ self.transform.get_matrix()
        ShaderLib.set_uniform("MVP", mvp)
        ShaderLib.set_uniform("model", self.transform.get_matrix())
        ShaderLib.set_uniform("normal_matrix", self.transform.get_matrix().inverse().transpose())
        ShaderLib.set_uniform("light_pos", Vec3(0, 0, 3))
        ShaderLib.set_uniform("view_pos", Vec3(0, 0, 3))
        ShaderLib.set_uniform("light_color", Vec3(1, 1, 1))
        ShaderLib.set_uniform("object_color", Vec3(0.6, 0.6, 0.6))

        with self.vao:
            self.vao.draw()

    def mousePressEvent(self, event):
        self.mouse_pos = event.pos()

        glBindFramebuffer(GL_FRAMEBUFFER, self.picking_fbo)
        x, y = int(event.position().x()), int(self.height() - event.position().y())
        pixel = glReadPixels(x, y, 1, 1, GL_RGB, GL_UNSIGNED_BYTE)
        face_id = pixel[0] + (pixel[1] << 8) + (pixel[2] << 16)
        glBindFramebuffer(GL_FRAMEBUFFER, 0)

        if face_id in self.face_ids:
            face_name = self.face_ids[face_id]
            self.snap_to_face(face_name)

    def mouseMoveEvent(self, event):
        if event.buttons():
            diff = event.position() - self.mouse_pos
            self.mouse_pos = event.position()

            axis = Vec3(diff.y(), diff.x(), 0)
            angle = axis.length() * 0.5
            if angle > 0:
                rotation = Quaternion.from_axis_angle(axis.normalize(), angle)
                self.transform.add_rotation(rotation)
                self.update()

    def snap_to_face(self, face_name):
        target_rotation = self.face_rotations[face_name]

        animation = QPropertyAnimation(self, b"qrotation")
        animation.setDuration(400)
        animation.setStartValue(self.transform.get_rotation())
        animation.setEndValue(target_rotation)
        animation.setEasingCurve(QEasingCurve.InOutQuad)
        animation.start(QPropertyAnimation.DeletionPolicy.DeleteWhenStopped)

    @Property(QQuaternion)
    def qrotation(self):
        q = self.transform.get_rotation()
        return QQuaternion(q.w, q.x, q.y, q.z)

    @qrotation.setter
    def set_qrotation(self, rotation):
        q = Quaternion(rotation.scalar(), rotation.x(), rotation.y(), rotation.z())
        self.transform.set_rotation(q)
        self.update()


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("3D Transformation Widget")
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.gl_widget = TransformationWidget()
        layout.addWidget(self.gl_widget, 1)

        self.matrix_display = QTextEdit()
        self.matrix_display.setReadOnly(True)
        self.matrix_display.setFixedHeight(120)
        layout.addWidget(self.matrix_display)

        self.gl_widget.matrix_updated.connect(self.update_matrix_display)

    @Slot(Mat4)
    def update_matrix_display(self, matrix):
        self.matrix_display.setText(str(matrix))


if __name__ == "__main__":
    # We need to create some dummy shaders for this to run
    # as the shader lib will fail otherwise.
    import os

    from PySide6.QtGui import QSurfaceFormat

    if not os.path.exists("glsl"):
        os.makedirs("glsl")
    with open("glsl/picking.vert", "w") as f:
        f.write("""#version 330 core
layout (location = 0) in vec3 aPos;
uniform mat4 MVP;
void main()
{
    gl_Position = MVP * vec4(aPos, 1.0);
}""")
    with open("glsl/picking.frag", "w") as f:
        f.write("""#version 330 core
out vec3 FragColor;
uniform vec3 face_id;
void main()
{
    FragColor = face_id;
}""")
    with open("glsl/phong.vert", "w") as f:
        f.write("""#version 330 core
layout (location = 0) in vec3 aPos;
layout (location = 1) in vec3 aNormal;
out vec3 FragPos;
out vec3 Normal;
uniform mat4 model;
uniform mat4 MVP;
uniform mat3 normal_matrix;
void main()
{
    FragPos = vec3(model * vec4(aPos, 1.0));
    Normal = normal_matrix * aNormal;
    gl_Position = MVP * vec4(aPos, 1.0);
}""")
    with open("glsl/phong.frag", "w") as f:
        f.write("""#version 330 core
out vec4 FragColor;
in vec3 FragPos;
in vec3 Normal;
uniform vec3 light_pos;
uniform vec3 view_pos;
uniform vec3 light_color;
uniform vec3 object_color;
void main()
{
    // Ambient
    float ambient_strength = 0.1;
    vec3 ambient = ambient_strength * light_color;
    // Diffuse
    vec3 norm = normalize(Normal);
    vec3 light_dir = normalize(light_pos - FragPos);
    float diff = max(dot(norm, light_dir), 0.0);
    vec3 diffuse = diff * light_color;
    // Specular
    float specular_strength = 0.5;
    vec3 view_dir = normalize(view_pos - FragPos);
    vec3 reflect_dir = reflect(-light_dir, norm);
    float spec = pow(max(dot(view_dir, reflect_dir), 0.0), 32);
    vec3 specular = specular_strength * spec * light_color;
    vec3 result = (ambient + diffuse + specular) * object_color;
    FragColor = vec4(result, 1.0);
}""")

    app = QApplication(sys.argv)
    format = QSurfaceFormat()
    format.setProfile(QSurfaceFormat.CoreProfile)
    format.setVersion(4, 1)
    QSurfaceFormat.setDefaultFormat(format)

    main_win = MainWindow()
    main_win.show()
    sys.exit(app.exec())
