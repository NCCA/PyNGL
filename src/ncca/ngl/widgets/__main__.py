"""Demo dialog showcasing all of the NGL PySide6 widgets."""

import sys

from PySide6.QtGui import QGuiApplication
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QGridLayout,
    QLabel,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ncca.ngl import Mat4, Vec2, Vec3, Vec4
from ncca.ngl.widgets import (
    LookAtWidget,
    Mat2Widget,
    Mat3Widget,
    Mat4Widget,
    RGBAColourWidget,
    RGBColourWidget,
    TransformWidget,
    Vec2Widget,
    Vec3Widget,
    Vec4Widget,
    __version__,
)


class SimpleDialog(QDialog):
    """Dialog laying out one of each NGL widget with live value labels."""

    def __init__(self, parent: QDialog | None = None) -> None:
        """Build the dialog and wire widget signals to labels."""
        super(SimpleDialog, self).__init__(parent)
        self.setWindowTitle(f"PyNGL ncca.widgets library {__version__}")
        self.setMinimumWidth(200)
        grid_layout = QGridLayout()

        self.vec2_widget = Vec2Widget(self, "Vec2 Widget", Vec2(1, 2))
        self.vec2_widget.set_x_range(-1, 1)
        self.vec2_widget.set_y_range(-2, 2)
        grid_layout.addWidget(self.vec2_widget, 0, 0)
        self.vec2_label = QLabel("[0.0,0.0]")
        grid_layout.addWidget(self.vec2_label, 0, 1)
        self.vec2_widget.valueChanged.connect(self._update_vec2)

        self.vec3_widget = Vec3Widget(self, "Vec3 Widget", Vec3(1, 2, 3))
        self.vec3_widget.set_y_range(-2, 2)
        self.vec3_widget.set_z_range(-3, 3)
        grid_layout.addWidget(self.vec3_widget, 1, 0)
        self.vec3_label = QLabel("[0.0,0.0,0.0]")
        grid_layout.addWidget(self.vec3_label, 1, 1)
        self.vec3_widget.valueChanged.connect(self._update_vec3)

        self.vec4_widget = Vec4Widget(self, "Vec4 Widget", Vec4(1, 2, 3, 1.0))
        self.vec4_widget.set_y_range(-2, 2)
        self.vec4_widget.set_z_range(-3, 3)
        grid_layout.addWidget(self.vec4_widget, 2, 0)
        self.vec4_label = QLabel("[0.0,0.0,0.0,1.0]")
        grid_layout.addWidget(self.vec4_label, 2, 1)
        self.vec4_widget.valueChanged.connect(self._update_vec4)

        self.transform_widget = TransformWidget(self, "Transform Widget")
        grid_layout.addWidget(self.transform_widget, 3, 0)

        self.lookat = LookAtWidget(self, "Look At")
        grid_layout.addWidget(self.lookat, 4, 0)

        self.rgb_colour_widget = RGBColourWidget(
            self, "RGB Colour Widget", 1.0, 0.0, 0.0
        )
        grid_layout.addWidget(self.rgb_colour_widget, 5, 0)
        self.rgba_colour_widget = RGBAColourWidget(
            self, "RGB Colour Widget", 1.0, 0.0, 0.0, 1.0
        )
        grid_layout.addWidget(self.rgba_colour_widget, 6, 0)

        self.mat2_widget = Mat2Widget(self, "Mat2 Widget")
        grid_layout.addWidget(self.mat2_widget, 0, 2)

        self.mat3_widget = Mat3Widget(self, "Mat3 Widget")
        grid_layout.addWidget(self.mat3_widget, 1, 2)

        self.mat4_widget = Mat4Widget(self, "Mat4 Widget")
        grid_layout.addWidget(self.mat4_widget, 2, 2)

        self.transform_matrix_widget = Mat4Widget(
            self, "Transform Output", read_only=True
        )
        grid_layout.addWidget(self.transform_matrix_widget, 3, 2)
        self.transform_widget.valueChanged.connect(self._update_transform_matrix)

        content = QWidget()
        content.setLayout(grid_layout)

        scroll_area = QScrollArea(self)
        scroll_area.setWidgetResizable(True)
        scroll_area.setWidget(content)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(0, 0, 0, 0)
        outer_layout.addWidget(scroll_area)

        self._resize_to_fit_screen()

    def _resize_to_fit_screen(self) -> None:
        """Size the dialog to fit comfortably within the available screen.

        Falls back to a fixed 1000x800 if no screen can be queried (e.g.
        a headless test environment).
        """
        screen = QGuiApplication.primaryScreen()
        if screen is None:
            self.resize(1000, 800)
            return
        available = screen.availableGeometry()
        margin = 80
        self.resize(
            min(1000, available.width() - margin),
            min(800, available.height() - margin),
        )

    def _update_vec3(self, value: Vec3) -> None:
        self.vec3_label.setText(f"[{value.x:0.2f}, {value.y:0.2f}, {value.z:0.2f}]")

    def _update_vec2(self, value: Vec2) -> None:
        self.vec2_label.setText(f"[{value.x:0.2f}, {value.y:0.2f}]")

    def _update_vec4(self, value: Vec4) -> None:
        self.vec4_label.setText(
            f"[{value.x:0.2f}, {value.y:0.2f}, {value.z:0.2f}, {value.w:0.2f}]"
        )

    def _update_transform_matrix(self, value: Mat4) -> None:
        self.transform_matrix_widget.set_value(value)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    print("NCCA Widgets")

    dialog = SimpleDialog()
    dialog.show()
    app.exec()
