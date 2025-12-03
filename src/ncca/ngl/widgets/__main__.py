import sys

from PySide6.QtWidgets import QApplication, QDialog, QGridLayout, QLabel

from ncca.ngl import Vec2, Vec3, Vec4
from ncca.ngl.widgets import (
    LookAtWidget,
    RGBAColourWidget,
    RGBColourWidget,
    TransformWidget,
    Vec2Widget,
    Vec3Widget,
    Vec4Widget,
)


class SimpleDialog(QDialog):
    def __init__(self, parent=None):
        super(SimpleDialog, self).__init__(parent)
        self.setWindowTitle("PyNGL ncca.widgets library ")
        self.setMinimumWidth(200)
        layout = QGridLayout()

        self.vec2_widget = Vec2Widget(self, "Vec2 Widget", Vec2(1, 2))
        self.vec2_widget.set_x_range(-1, 1)
        self.vec2_widget.set_y_range(-2, 2)
        layout.addWidget(self.vec2_widget, 0, 0)
        self.vec2_label = QLabel("[0.0,0.0]")
        layout.addWidget(self.vec2_label, 0, 1)
        self.vec2_widget.valueChanged.connect(self._update_vec2)

        self.vec3_widget = Vec3Widget(self, "Vec3 Widget", Vec3(1, 2, 3))
        self.vec3_widget.set_y_range(-2, 2)
        self.vec3_widget.set_z_range(-3, 3)
        layout.addWidget(self.vec3_widget, 1, 0)
        self.vec3_label = QLabel("[0.0,0.0,0.0]")
        layout.addWidget(self.vec3_label, 1, 1)
        self.vec3_widget.valueChanged.connect(self._update_vec3)

        self.vec4_widget = Vec4Widget(self, "Vec4 Widget", Vec4(1, 2, 3, 1.0))
        self.vec4_widget.set_y_range(-2, 2)
        self.vec4_widget.set_z_range(-3, 3)
        layout.addWidget(self.vec4_widget, 2, 0)
        self.vec4_label = QLabel("[0.0,0.0,0.0,1.0]")
        layout.addWidget(self.vec4_label, 2, 1)
        self.vec4_widget.valueChanged.connect(self._update_vec4)

        self.transform_widget = TransformWidget(self, "Transform Widget")
        layout.addWidget(self.transform_widget, 3, 0)

        self.lookat = LookAtWidget(self, "Look At")
        layout.addWidget(self.lookat, 4, 0)

        self.rgb_colour_widget = RGBColourWidget(self, "RGB Colour Widget", 1.0, 0.0, 0.0)
        layout.addWidget(self.rgb_colour_widget, 5, 0)
        self.rgba_colour_widget = RGBAColourWidget(self, "RGB Colour Widget", 1.0, 0.0, 0.0, 1.0)
        layout.addWidget(self.rgba_colour_widget, 6, 0)

        self.setLayout(layout)

    def _update_vec3(self, value):
        self.vec3_label.setText(f"[{value.x:0.2f}, {value.y:0.2f}, {value.z:0.2f}]")

    def _update_vec2(self, value):
        self.vec2_label.setText(f"[{value.x:0.2f}, {value.y:0.2f}]")

    def _update_vec4(self, value):
        self.vec4_label.setText(f"[{value.x:0.2f}, {value.y:0.2f}, {value.z:0.2f}, {value.w:0.2f}]")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    print("NCCA Widgets")

    dialog = SimpleDialog()
    dialog.show()
    app.exec()
