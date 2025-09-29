from .base_mesh import BaseMesh, Face
from .texture import Texture
from .vec3 import Vec3


class ObjParseVertexError(Exception):
    pass


class ObjParseNormalError(Exception):
    pass


class ObjParseUVError(Exception):
    pass


class ObjParseFaceError(Exception):
    pass


class Obj(BaseMesh):
    """
    OBJ mesh loader and exporter.

    Inherits from BaseMesh and provides methods to parse, load, and save OBJ files,
    including support for vertices, normals, UVs, faces, and optional vertex colors.
    """

    def __init__(self):
        """
        Initialize an empty OBJ mesh.
        Tracks current offsets for vertices, normals, and UVs to handle negative indices.
        """
        super().__init__()
        # as faces can use negative index values keep track of index
        self._current_vertex_offset: int = 0
        self._current_normal_offset: int = 0
        self._current_uv_offset: int = 0

    def _parse_vertex(self, tokens: list[str]) -> None:
        """
        Parse a vertex line from the OBJ file.

        Args:
            tokens: List of string tokens from the line.
        Raises:
            ObjParseVertexError: If vertex parsing fails.
        """
        try:
            self.vertex.append(
                Vec3(float(tokens[1]), float(tokens[2]), float(tokens[3]))
            )
            self._current_vertex_offset += 1
            if len(tokens) == 7:  # we have the non standard colour
                if not hasattr(self, "colour"):
                    self.colour = []
                self.colour.append(
                    Vec3(float(tokens[4]), float(tokens[5]), float(tokens[6]))
                )
        except ValueError:
            raise ObjParseVertexError

    def _parse_normal(self, tokens: list[str]) -> None:
        """
        Parse a normal line from the OBJ file.

        Args:
            tokens: List of string tokens from the line.
        Raises:
            ObjParseNormalError: If normal parsing fails.
        """
        try:
            self.normals.append(
                Vec3(float(tokens[1]), float(tokens[2]), float(tokens[3]))
            )
            self._current_normal_offset += 1
        except ValueError:
            raise ObjParseNormalError

    def _parse_uv(self, tokens: list[str]) -> None:
        """
        Parse a UV line from the OBJ file.

        Args:
            tokens: List of string tokens from the line.
        Raises:
            ObjParseUVError: If UV parsing fails.
        """
        try:
            # some DCC's use vec3 for UV so may as well support
            z = 0.0
            if len(tokens) == 4:
                z = float(tokens[3])
            self.uv.append(Vec3(float(tokens[1]), float(tokens[2]), z))
            self._current_uv_offset += 1
        except ValueError:
            raise ObjParseUVError

    def _parse_face_vertex_normal_uv(self, tokens: list[str]) -> None:
        """
        Parse a face line with vertex/uv/normal indices (f v/vt/vn ...).

        Args:
            tokens: List of string tokens from the line.
        Raises:
            ObjParseFaceError: If face parsing fails.
        """
        f = Face()
        for token in tokens[1:]:  # skip f
            # each one of these should be v/vt/vn
            vn = token.split("/")
            try:
                # note we need to subtract one from the list as obj index from 1
                idx = int(vn[0]) - 1
                if idx < 0:  # negative index so grab the index
                    # note we index from 0 not 1 like obj so adjust
                    idx = self._current_vertex_offset + (idx + 1)
                f.vertex.append(idx)
                # same for UV
                idx = int(vn[1]) - 1
                if idx < 0:  # negative index so grab the index
                    # note we index from 0 not 1 like obj so adjust
                    idx = self._current_uv_offset + (idx + 1)
                f.uv.append(idx)
                # same for normals
                idx = int(vn[2]) - 1
                if idx < 0:  # negative index so grab the index
                    # note we index from 0 not 1 like obj so adjust
                    idx = self._current_normal_offset + (idx + 1)
                f.normal.append(idx)
            except ValueError:
                raise ObjParseFaceError
        self.faces.append(f)

    def _parse_face_vertex(self, tokens: list[str]) -> None:
        """
        Parse a face line with only vertex indices (f v v v ...).

        Args:
            tokens: List of string tokens from the line.
        Raises:
            ObjParseFaceError: If face parsing fails.
        """
        f = Face()
        for token in tokens[1:]:  # skip f
            # each one of these should be v v
            try:
                # note we need to subtract one from the list as obj index from 1
                idx = int(token) - 1
                if idx < 0:  # negative index so grab the index
                    # note we index from 0 not 1 like obj so adjust
                    idx = self._current_vertex_offset + (idx + 1)
                f.vertex.append(idx)
            except ValueError:
                raise ObjParseFaceError
        self.faces.append(f)

    def _parse_face_vertex_normal(self, tokens: list[str]) -> None:
        """
        Parse a face line with vertex//normal indices (f v//vn ...).

        Args:
            tokens: List of string tokens from the line.
        Raises:
            ObjParseFaceError: If face parsing fails.
        """
        f = Face()
        for token in tokens[1:]:  # skip f
            # each one of these should be v//vn
            vn = token.split("//")
            try:
                # note we need to subtract one from the list as obj index from 1
                idx = int(vn[0]) - 1
                if idx < 0:  # negative index so grab the index
                    # note we index from 0 not 1 like obj so adjust
                    idx = self._current_vertex_offset + (idx + 1)
                f.vertex.append(idx)
                # same for normals
                idx = int(vn[1]) - 1
                if idx < 0:  # negative index so grab the index
                    # note we index from 0 not 1 like obj so adjust
                    idx = self._current_normal_offset + (idx + 1)
                f.normal.append(idx)
            except ValueError:
                raise ObjParseFaceError
        self.faces.append(f)

    def _parse_face_vertex_uv(self, tokens: list[str]) -> None:
        """
        Parse a face line with vertex/uv indices (f v/vt ...).

        Args:
            tokens: List of string tokens from the line.
        Raises:
            ObjParseFaceError: If face parsing fails.
        """
        f = Face()
        for token in tokens[1:]:  # skip f
            # each one of these should be v/vt
            vn = token.split("/")
            try:
                # note we need to subtract one from the list as obj index from 1
                idx = int(vn[0]) - 1
                if idx < 0:  # negative index so grab the index
                    # note we index from 0 not 1 like obj so adjust
                    idx = self._current_vertex_offset + (idx + 1)
                f.vertex.append(idx)
                # same for uv
                idx = int(vn[1]) - 1
                if idx < 0:  # negative index so grab the index
                    # note we index from 0 not 1 like obj so adjust
                    idx = self._current_uv_offset + (idx + 1)
                f.uv.append(idx)
            except ValueError:
                raise ObjParseFaceError
        self.faces.append(f)

    def _parse_face(self, tokens: list[str]) -> None:
        """
        Parse a face line, dispatching to the correct face parser based on format.

        Args:
            tokens: List of string tokens from the line.
        """
        # first let's find what sort of face we are dealing with I assume most likely case is all
        if tokens[1].count("/") == 2 and tokens[1].find("//") == -1:
            self._parse_face_vertex_normal_uv(tokens)
        elif tokens[1].find("/") == -1:
            self._parse_face_vertex(tokens)
        elif tokens[1].find("//") != -1:
            self._parse_face_vertex_normal(tokens)
        # if we have 1 / it is a VertUV format
        elif tokens[1].count("/") == 1:
            self._parse_face_vertex_uv(tokens)

    def load(self, file: str) -> bool:
        """
        Load an OBJ file and parse its contents into the mesh.

        Args:
            file: Path to the OBJ file.

        Returns:
            bool: True if loading was successful.
        """
        with open(file, "r") as obj_file:
            lines = obj_file.readlines()
        for line in lines:
            line = line.strip()  # strip whitespace
            if len(line) > 0:  # skip empty lines
                tokens = line.split()
                if tokens[0] == "v":
                    self._parse_vertex(tokens)
                elif tokens[0] == "vn":
                    self._parse_normal(tokens)
                elif tokens[0] == "vt":
                    self._parse_uv(tokens)
                elif tokens[0] == "f":
                    self._parse_face(tokens)
        return True

    @classmethod
    def from_file(cls, fname: str) -> "Obj":
        """
        Create an Obj instance from a file.

        Args:
            fname: Path to the OBJ file.

        Returns:
            Obj: The loaded Obj instance.
        """
        obj = Obj()
        obj.load(fname)
        return obj

    def add_vertex(self, vertex: Vec3) -> None:
        """
        Add a vertex to the mesh.

        Args:
            vertex: The vertex to add.
        """
        self.vertex.append(vertex)

    def add_vertex_colour(self, vertex: Vec3, colour: Vec3) -> None:
        """
        Add a vertex and its color to the mesh.

        Args:
            vertex: The vertex to add.
            colour: The color to associate with the vertex.
        """
        self.vertex.append(vertex)
        if not hasattr(self, "colour"):
            self.colour = []
        self.colour.append(colour)

    def add_normal(self, normal: Vec3) -> None:
        """
        Add a normal to the mesh.

        Args:
            normal: The normal to add.
        """
        self.normals.append(normal)

    def add_uv(self, uv: Vec3) -> None:
        """
        Add a UV coordinate to the mesh.

        Args:
            uv: The UV coordinate to add.
        """
        self.uv.append(uv)

    def add_face(self, face: Face) -> None:
        """
        Add a face to the mesh.

        Args:
            face: The face to add.
        """
        self.faces.append(face)

    def save(self, filename: str) -> None:
        """
        Save the mesh to an OBJ file.

        Args:
            filename: Path to the output OBJ file.
        """
        with open(filename, "w") as obj_file:
            obj_file.write("# This file was created by nccapy/Geo/Obj.py exporter\n")
            self._write_vertices(obj_file)
            self._write_uvs(obj_file)
            self._write_normals(obj_file)
            self._write_faces(obj_file)

    def _write_vertices(self, obj_file) -> None:
        """
        Write vertices (and optional colors) to the OBJ file.

        Args:
            obj_file: Open file object for writing.
        """
        for i, v in enumerate(self.vertex):
            obj_file.write(f"v {v.x} {v.y} {v.z} ")
            if hasattr(self, "colour"):  # write colour if present
                obj_file.write(
                    f"{self.colour[i].x} {self.colour[i].y} {self.colour[i].z} "
                )
            obj_file.write("\n")

    def _write_uvs(self, obj_file) -> None:
        """
        Write UV coordinates to the OBJ file.

        Args:
            obj_file: Open file object for writing.
        """
        for v in self.uv:
            obj_file.write(f"vt {v.x} {v.y} \n")

    def _write_normals(self, obj_file) -> None:
        """
        Write normals to the OBJ file.

        Args:
            obj_file: Open file object for writing.
        """
        for v in self.normals:
            obj_file.write(f"vn {v.x} {v.y} {v.z} \n")

    def _write_faces(self, obj_file) -> None:
        """
        Write faces to the OBJ file.

        Args:
            obj_file: Open file object for writing.
        """
        for face in self.faces:
            obj_file.write("f")
            for i in range(len(face.vertex)):
                obj_file.write(f" {face.vertex[i] + 1}")
                if len(face.uv) != 0:
                    obj_file.write(f"/{face.uv[i] + 1}")
                if len(face.normal) != 0:
                    if len(face.uv) == 0:
                        obj_file.write("//")
                    else:
                        obj_file.write("/")
                    obj_file.write(f"{face.normal[i] + 1}")
            obj_file.write("\n")

    @classmethod
    def obj_with_vao(cls, mesh_name: str, texture_name: str = None) -> "Obj":
        """
        Load an OBJ mesh and optionally a texture, then create a VAO.

        Args:
            mesh_name: Path to the OBJ mesh file.
            texture_name: Optional path to the texture file.

        Returns:
            Obj: The loaded and VAO-initialized mesh.
        """
        mesh = Obj()
        mesh.load(mesh_name)
        if texture_name:
            texture = Texture(texture_name)
            mesh.texture_id = texture.set_texture_gl()
            print(f"{mesh.texture_id=}")
        mesh.create_vao()
        return mesh
