"""Wavefront OBJ file loading and saving without a rendering back end."""

from typing import TextIO

from .mesh import Face, MeshData
from .vec3 import Vec3


class ObjParseVertexError(Exception):
    """Raised when a vertex line in an OBJ file cannot be parsed."""


class ObjParseNormalError(Exception):
    """Raised when a normal line in an OBJ file cannot be parsed."""


class ObjParseUVError(Exception):
    """Raised when a UV line in an OBJ file cannot be parsed."""


class ObjParseFaceError(Exception):
    """Raised when a face line in an OBJ file cannot be parsed."""


class Obj(MeshData):
    """Load and save Wavefront OBJ geometry as CPU-side mesh data."""

    def _parse_vertex(self, tokens: list[str]) -> None:
        try:
            if len(tokens) not in (4, 7):
                raise ValueError
            self.vertex.append(
                Vec3(float(tokens[1]), float(tokens[2]), float(tokens[3]))
            )
            if len(tokens) == 7:
                self.colour.append(
                    Vec3(float(tokens[4]), float(tokens[5]), float(tokens[6]))
                )
        except (IndexError, ValueError) as error:
            raise ObjParseVertexError from error

    def _parse_normal(self, tokens: list[str]) -> None:
        try:
            self.normals.append(
                Vec3(float(tokens[1]), float(tokens[2]), float(tokens[3]))
            )
        except (IndexError, ValueError) as error:
            raise ObjParseNormalError from error

    def _parse_uv(self, tokens: list[str]) -> None:
        try:
            if len(tokens) not in (3, 4):
                raise ValueError
            self.uv.append(
                Vec3(
                    float(tokens[1]),
                    float(tokens[2]),
                    float(tokens[3]) if len(tokens) == 4 else 0.0,
                )
            )
        except (IndexError, ValueError) as error:
            raise ObjParseUVError from error

    @staticmethod
    def _index(value: str, length: int) -> int:
        index = int(value)
        if index == 0:
            raise ObjParseFaceError
        return length + index if index < 0 else index - 1

    def _parse_face(self, tokens: list[str]) -> None:
        if len(tokens) < 2:
            raise ObjParseFaceError
        parts = [token.split("/") for token in tokens[1:]]
        shapes = {len(part) for part in parts}
        if len(shapes) != 1 or shapes.pop() not in (1, 2, 3):
            raise ObjParseFaceError
        kind = len(parts[0])
        if any(
            not part[0] or (kind == 2 and not part[1]) or (kind == 3 and not part[2])
            for part in parts
        ):
            raise ObjParseFaceError
        if (
            kind == 3
            and any(part[1] == "" for part in parts)
            and not all(part[1] == "" for part in parts)
        ):
            raise ObjParseFaceError
        try:
            face = Face(
                vertex=[self._index(part[0], len(self.vertex)) for part in parts]
            )
            if kind == 2 or (kind == 3 and parts[0][1]):
                face.uv = [self._index(part[1], len(self.uv)) for part in parts]
            if kind == 3:
                face.normal = [
                    self._index(part[2], len(self.normals)) for part in parts
                ]
            self.faces.append(face)
        except (ValueError, IndexError, ObjParseFaceError) as error:
            raise ObjParseFaceError from error

    def load(self, file: str) -> bool:
        """Append geometry from an OBJ file and update its dimensions."""
        with open(file) as obj_file:
            for line in obj_file:
                tokens = line.strip().split()
                if not tokens:
                    continue
                if tokens[0] == "v":
                    self._parse_vertex(tokens)
                elif tokens[0] == "vn":
                    self._parse_normal(tokens)
                elif tokens[0] == "vt":
                    self._parse_uv(tokens)
                elif tokens[0] == "f":
                    self._parse_face(tokens)
        self.calc_dimensions()
        return True

    @classmethod
    def from_file(cls, fname: str) -> "Obj":
        """Create an Obj instance from a Wavefront file."""
        obj = cls()
        obj.load(fname)
        return obj

    def add_vertex(self, vertex: Vec3) -> None:
        """Append a vertex position."""
        self.vertex.append(vertex)

    def add_vertex_colour(self, vertex: Vec3, colour: Vec3) -> None:
        """Append a vertex position and its colour."""
        self.vertex.append(vertex)
        self.colour.append(colour)

    def add_normal(self, normal: Vec3) -> None:
        """Append a vertex normal."""
        self.normals.append(normal)

    def add_uv(self, uv: Vec3) -> None:
        """Append a texture coordinate."""
        self.uv.append(uv)

    def add_face(self, face: Face) -> None:
        """Append a face."""
        self.faces.append(face)

    def save(self, filename: str) -> None:
        """Save valid CPU mesh data as a Wavefront OBJ file."""
        self.validate()
        with open(filename, "w") as obj_file:
            obj_file.write("# This file was created by nccapy/Geo/Obj.py exporter\n")
            self._write_vertices(obj_file)
            self._write_uvs(obj_file)
            self._write_normals(obj_file)
            self._write_faces(obj_file)

    def _write_vertices(self, obj_file: TextIO) -> None:
        for index, vertex in enumerate(self.vertex):
            values = f"v {vertex.x} {vertex.y} {vertex.z}"
            if self.colour:
                colour = self.colour[index]
                values += f" {colour.x} {colour.y} {colour.z}"
            obj_file.write(f"{values}\n")

    def _write_uvs(self, obj_file: TextIO) -> None:
        for uv in self.uv:
            obj_file.write(f"vt {uv.x} {uv.y}\n")

    def _write_normals(self, obj_file: TextIO) -> None:
        for normal in self.normals:
            obj_file.write(f"vn {normal.x} {normal.y} {normal.z}\n")

    def _write_faces(self, obj_file: TextIO) -> None:
        for face in self.faces:
            corners = []
            for index, vertex in enumerate(face.vertex):
                corner = str(vertex + 1)
                if face.uv:
                    corner += f"/{face.uv[index] + 1}"
                if face.normal:
                    corner += (
                        f"/{face.normal[index] + 1}"
                        if face.uv
                        else f"//{face.normal[index] + 1}"
                    )
                corners.append(corner)
            obj_file.write(f"f {' '.join(corners)}\n")
