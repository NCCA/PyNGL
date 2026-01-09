# PyNGL

This is the code for the full python version of [NGL](https://github.com/NCCA/NGL) the ncca graphics library.

This project is available on PyPI and can be installed using uv.

For the current build status see our CI logs here 

[![UV Tests](https://github.com/NCCA/PyNGL/actions/workflows/uv.yml/badge.svg)](https://github.com/NCCA/PyNGL/actions/workflows/uv.yml)[![Sonar Scanner](https://github.com/NCCA/PyNGL/actions/workflows/sonar-scan.yml/badge.svg)](https://github.com/NCCA/PyNGL/actions/workflows/sonar-scan.yml)

[![Quality Gate Status](https://sonarcloud.io/api/project_badges/measure?project=NCCA_PyNGL&metric=alert_status)](https://sonarcloud.io/summary/new_code?id=NCCA_PyNGL)[![Bugs](https://sonarcloud.io/api/project_badges/measure?project=NCCA_PyNGL&metric=bugs)](https://sonarcloud.io/summary/new_code?id=NCCA_PyNGL)[![Code Smells](https://sonarcloud.io/api/project_badges/measure?project=NCCA_PyNGL&metric=code_smells)](https://sonarcloud.io/summary/new_code?id=NCCA_PyNGL)[![Coverage](https://sonarcloud.io/api/project_badges/measure?project=NCCA_PyNGL&metric=coverage)](https://sonarcloud.io/summary/new_code?id=NCCA_PyNGL)[![Duplicated Lines (%)](https://sonarcloud.io/api/project_badges/measure?project=NCCA_PyNGL&metric=duplicated_lines_density)](https://sonarcloud.io/summary/new_code?id=NCCA_PyNGL)

## Test

use

```
uv run pytest
```

To run tests,

```
uv run pytest --cov=src --cov-report=term-missing
```

For coverage reports.

## Classes

### [`abstract_vao.py`](src/ncca/ngl/abstract_vao.py)
*   [`VertexData`](src/ncca/ngl/abstract_vao.py): A simple data structure to hold vertex data for a VAO. It stores the data as a numpy array, the size of the data, and the drawing mode.
*   [`AbstractVAO`](src/ncca/ngl/abstract_vao.py): An abstract base class for Vertex Array Objects (VAOs). It defines the interface for different VAO implementations, including methods for binding, drawing, setting data, and managing the VAO's lifecycle.

### [`base_mesh.py`](src/ncca/ngl/base_mesh.py)
*   [`Face`](src/ncca/ngl/base_mesh.py): A simple data structure for a mesh face, holding indices for vertices, UVs, and normals.
*   [`BaseMesh`](src/ncca/ngl/base_mesh.py): A base class for mesh geometry. It provides storage for vertices, normals, UVs, and faces, and includes methods for creating a VAO from the mesh data, calculating dimensions, and drawing the mesh.

### [`bbox.py`](src/ncca/ngl/bbox.py)
*   [`BBox`](src/ncca/ngl/bbox.py): Represents a 3D bounding box. It stores the center, dimensions, and extents of the box, and provides methods to calculate these values and retrieve the box's vertices and normals.

### [`bezier_curve.py`](src/ncca/ngl/bezier_curve.py)
*   [`BezierCurve`](src/ncca/ngl/bezier_curve.py): A class for creating and evaluating Bézier curves. It stores control points and knots, and can calculate points on the curve using the Cox-de Boor algorithm.

### [`first_person_camera.py`](src/ncca/ngl/first_person_camera.py)
*   [`FirstPersonCamera`](src/ncca/ngl/first_person_camera.py): Implements a first-person camera with movement, rotation, and projection matrix calculation. It handles mouse and keyboard input for camera control.

### [`image.py`](src/ncca/ngl/image.py)
*   [`Image`](src/ncca/ngl/image.py): A class for loading, saving, and manipulating images. It uses the Pillow library to handle different image formats and stores image data as a NumPy array.

### [`log.py`](src/ncca/ngl/log.py)
*   [`ColoredFormatter`](src/ncca/ngl/log.py): A custom logging formatter that adds color to log messages based on their severity level.
*   [`setup_logger`](src/ncca/ngl/log.py): A function to set up a logger with both file and console handlers.

### [`mat2.py`](src/ncca/ngl/mat2.py)
*   [`Mat2`](src/ncca/ngl/mat2.py): A 2x2 matrix class with support for identity, multiplication (matrix-matrix and matrix-vector), and conversion to a NumPy array.

### [`mat3.py`](src/ncca/ngl/mat3.py)
*   [`Mat3`](src/ncca/ngl/mat3.py): A 3x3 matrix class for 3D transformations. It includes methods for identity, zero, scale, rotation, transpose, inverse, and matrix multiplication.

### [`mat4.py`](src/ncca/ngl/mat4.py)
*   [`Mat4`](src/ncca/ngl/mat4.py): A 4x4 matrix class for 3D transformations. It supports creation of identity, zero, scale, translation, and rotation matrices, as well as matrix multiplication and inversion.

### [`multi_buffer_vao.py`](src/ncca/ngl/multi_buffer_vao.py)
*   [`MultiBufferVAO`](src/ncca/ngl/multi_buffer_vao.py): A VAO implementation that can manage multiple vertex buffers. This is useful for separating different types of vertex attributes (e.g., positions, colors, normals) into different buffers.

### [`obj.py`](src/ncca/ngl/obj.py)
*   [`Obj`](src/ncca/ngl/obj.py): A class for loading and saving Wavefront OBJ files. It extends `BaseMesh` and handles parsing of vertices, normals, UVs, and faces from an OBJ file, including support for negative indices.

### [`plane.py`](src/ncca/ngl/plane.py)
*   [`Plane`](src/ncca/ngl/plane.py): Represents a mathematical plane in 3D space. It can be defined by three points or a normal and a point, and can calculate the distance from a point to the plane.

### [`prim_data.py`](src/ncca/ngl/prim_data.py)
*   [`Prims`](src/ncca/ngl/prim_data.py): An enum of available primitive types.
*   [`PrimData`](src/ncca/ngl/prim_data.py): A class that provides static methods to generate vertex data for various geometric primitives like spheres, cubes, and tori.

### [`primitives.py`](src/ncca/ngl/primitives.py)
*   [`Primitives`](src/ncca/ngl/primitives.py): A static class for creating and drawing pre-defined geometric primitives. It uses `PrimData` to generate the vertex data and `VAOFactory` to create VAOs for rendering.

### [`pyside_event_handling_mixin.py`](src/ncca/ngl/pyside_event_handling_mixin.py)
*   [`PySideEventHandlingMixin`](src/ncca/ngl/pyside_event_handling_mixin.py): A mixin class for PySide6 applications that provides common event handling for mouse-based camera control (rotation, translation, zoom) and keyboard shortcuts.

### [`quaternion.py`](src/ncca/ngl/quaternion.py)
*   [`Quaternion`](src/ncca/ngl/quaternion.py): A class for representing rotations using quaternions. It includes methods for converting from a rotation matrix, multiplication, normalization, and applying the rotation to a vector.

### [`random.py`](src/ncca/ngl/random.py)
*   [`Random`](src/ncca/ngl/random.py): A static class for generating random numbers and vectors. It provides methods to get random floats, integers, and vectors of different dimensions.

### [`shader.py`](src/ncca/ngl/shader.py)
*   [`Shader`](src/ncca/ngl/shader.py): Represents a single OpenGL shader object (e.g., vertex, fragment). It handles loading source from a file, compiling the shader, and checking for errors.

### [`shader_lib.py`](src/ncca/ngl/shader_lib.py)
*   [`ShaderLib`](src/ncca/ngl/shader_lib.py): A singleton class that manages a library of shader programs. It provides a global point of access for loading, compiling, linking, and using shaders, as well as for setting uniform variables.

### [`shader_program.py`](src/ncca/ngl/shader_program.py)
*   [`ShaderProgram`](src/ncca/ngl/shader_program.py): A wrapper for an OpenGL shader program. It manages attaching shaders, linking the program, and provides an interface for setting uniform variables.

### [`simple_index_vao.py`](src/ncca/ngl/simple_index_vao.py)
*   [`SimpleIndexVAO`](src/ncca/ngl/simple_index_vao.py): A VAO implementation that uses an index buffer for indexed drawing. This is more efficient for meshes where vertices are shared between multiple faces.

### [`simple_vao.py`](src/ncca/ngl/simple_vao.py)
*   [`SimpleVAO`](src/ncca/ngl/simple_vao.py): A basic VAO implementation that uses a single buffer for non-indexed drawing.

### [`text.py`](src/ncca/ngl/text.py)
*   [`Text`](src/ncca/ngl/text.py): A class for rendering text in OpenGL. It uses `freetype-py` to create a texture atlas of font glyphs and renders text using a geometry shader to create quads for each character.

### [`texture.py`](src/ncca/ngl/texture.py)
*   [`Texture`](src/ncca/ngl/texture.py): A class for loading image files and creating OpenGL textures from them.

### [`transform.py`](src/ncca/ngl/transform.py)
*   [`Transform`](src/ncca/ngl/transform.py): A class to represent a 3D transformation with position, rotation, and scale components. It can generate a transformation matrix based on a specified rotation order.

### [`util.py`](src/ncca/ngl/util.py)
*   [`util.py`](src/ncca/ngl/util.py): This module contains various utility functions for 3D math, including `lookAt`, `perspective`, `ortho`, and `frustum` matrix generation, as well as `clamp` and `lerp` functions.

### [`vao_factory.py`](src/ncca/ngl/vao_factory.py)
*   [`VAOFactory`](src/ncca/ngl/vao_factory.py): A factory class for creating different types of VAOs. It allows for registering custom VAO creators and creating VAO instances by name.

### [`vec2.py`](src/ncca/ngl/vec2.py), [`vec3.py`](src/ncca/ngl/vec3.py), [`vec4.py`](src/ncca/ngl/vec4.py)
*   [`Vec2`](src/ncca/ngl/vec2.py), [`Vec3`](src/ncca/ngl/vec3.py), [`Vec4`](src/ncca/ngl/vec4.py): Classes for 2D, 3D, and 4D vectors, respectively. They provide standard vector operations such as addition, subtraction, dot product, cross product, normalization, and length calculation.

### [`vec2_array.py`](src/ncca/ngl/vec2_array.py), [`vec3_array.py`](src/ncca/ngl/vec3_array.py), [`vec4_array.py`](src/ncca/ngl/vec4_array.py)
*   [`Vec2Array`](src/ncca/ngl/vec2_array.py), [`Vec3Array`](src/ncca/ngl/vec3_array.py), [`Vec4Array`](src/ncca/ngl/vec4_array.py): Container classes that act like `std::vector` for `Vec2`, `Vec3`, and `Vec4` objects, respectively. They provide methods for appending, extending, and converting the data to flat lists or NumPy arrays.
