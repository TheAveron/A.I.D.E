"""A small, defensive reader for Minecraft structure files (.nbt).

Create's schematics and the vanilla structure block both save the same format:
a gzip-compressed NBT compound holding `size` (3 ints), `palette` (the block
states) and `blocks` (one compound per block, pointing into the palette).

The files come from players, so nothing in them is trusted:
- the decompressed size is capped (a few kilobytes of gzip can expand to
  gigabytes);
- nesting depth and every length read from the file are bounded and checked
  against the bytes actually left;
- only what is needed is turned into Python objects (the size, the palette
  names, the state of each block); everything else is skipped without being
  built, so memory stays proportional to the useful data.
"""

import gzip
import io
import struct
import zlib
from dataclasses import dataclass
from typing import Optional

MAX_DECOMPRESSED_BYTES = 64 * 1024 * 1024
MAX_DEPTH = 64
# A structure larger than this on any axis is not a schematic anybody pastes
MAX_AXIS = 4096

# Tag ids
END, BYTE, SHORT, INT, LONG, FLOAT, DOUBLE = 0, 1, 2, 3, 4, 5, 6
BYTE_ARRAY, STRING, LIST, COMPOUND, INT_ARRAY, LONG_ARRAY = 7, 8, 9, 10, 11, 12

_FIXED_SIZE = {BYTE: 1, SHORT: 2, INT: 4, LONG: 8, FLOAT: 4, DOUBLE: 8}
_ARRAY_ITEM_SIZE = {BYTE_ARRAY: 1, INT_ARRAY: 4, LONG_ARRAY: 8}

AIR_BLOCKS = frozenset(
    {
        "minecraft:air",
        "minecraft:cave_air",
        "minecraft:void_air",
        "minecraft:structure_void",
    }
)


class NbtError(ValueError):
    """The file is not a readable structure file. The message is safe to
    show to the user (it never contains server paths)."""


@dataclass(frozen=True)
class StructureInfo:
    size_x: int
    size_y: int
    size_z: int
    block_count: int  # blocks that are not air
    data_version: Optional[int]


def decompress(raw: bytes) -> bytes:
    """The NBT bytes of a file: gzip (the usual case), zlib, or plain."""
    if raw[:2] == b"\x1f\x8b":
        try:
            with gzip.GzipFile(fileobj=io.BytesIO(raw)) as f:
                data = f.read(MAX_DECOMPRESSED_BYTES + 1)
        except (OSError, EOFError, zlib.error):
            raise NbtError("The file is compressed but cannot be read")
    elif raw[:1] == b"\x78":
        try:
            d = zlib.decompressobj()
            data = d.decompress(raw, MAX_DECOMPRESSED_BYTES + 1)
        except zlib.error:
            raise NbtError("The file is compressed but cannot be read")
    else:
        data = raw
    if len(data) > MAX_DECOMPRESSED_BYTES:
        raise NbtError("The file is too large once decompressed")
    return data


class _Reader:
    def __init__(self, data: bytes) -> None:
        self.data = data
        self.pos = 0

    def _need(self, n: int) -> None:
        if n < 0 or self.pos + n > len(self.data):
            raise NbtError("The file is truncated or corrupted")

    def take(self, n: int) -> bytes:
        self._need(n)
        chunk = self.data[self.pos : self.pos + n]
        self.pos += n
        return chunk

    def skip_bytes(self, n: int) -> None:
        self._need(n)
        self.pos += n

    def _unpack(self, fmt: str, size: int):
        self._need(size)
        (value,) = struct.unpack_from(fmt, self.data, self.pos)
        self.pos += size
        return value

    def u8(self) -> int:
        return self._unpack(">B", 1)

    def i32(self) -> int:
        return self._unpack(">i", 4)

    def string(self) -> str:
        length = self._unpack(">H", 2)
        # Java's "modified UTF-8": close enough to UTF-8 for block names
        return self.take(length).decode("utf-8", errors="replace")

    def skip_string(self) -> None:
        self.skip_bytes(self._unpack(">H", 2))

    def list_header(self) -> tuple[int, int]:
        item_type = self.u8()
        length = self.i32()
        if length < 0:
            raise NbtError("The file is corrupted (negative length)")
        if length and item_type == END:
            raise NbtError("The file is corrupted (list without a type)")
        return item_type, length

    def skip(self, tag: int, depth: int = 0) -> None:
        """Skip one payload of type `tag` without building it."""
        if depth > MAX_DEPTH:
            raise NbtError("The file is nested too deeply")
        if tag in _FIXED_SIZE:
            self.skip_bytes(_FIXED_SIZE[tag])
        elif tag in _ARRAY_ITEM_SIZE:
            length = self.i32()
            if length < 0:
                raise NbtError("The file is corrupted (negative length)")
            self.skip_bytes(length * _ARRAY_ITEM_SIZE[tag])
        elif tag == STRING:
            self.skip_string()
        elif tag == LIST:
            item_type, length = self.list_header()
            if item_type in _FIXED_SIZE:
                self.skip_bytes(length * _FIXED_SIZE[item_type])
            else:
                for _ in range(length):
                    self.skip(item_type, depth + 1)
        elif tag == COMPOUND:
            while True:
                child = self.u8()
                if child == END:
                    return
                self.skip_string()
                self.skip(child, depth + 1)
        else:
            raise NbtError("The file holds an unknown data type")

    def entries(self, depth: int):
        """Iterate over a compound's (type, name); the caller reads or skips
        each payload before asking for the next one."""
        if depth > MAX_DEPTH:
            raise NbtError("The file is nested too deeply")
        while True:
            tag = self.u8()
            if tag == END:
                return
            yield tag, self.string()


def _read_size(r: _Reader, tag: int) -> tuple[int, int, int]:
    if tag != LIST:
        raise NbtError("The file's \"size\" field is invalid")
    item_type, length = r.list_header()
    if item_type != INT or length != 3:
        raise NbtError("The file's \"size\" field is invalid")
    x, y, z = r.i32(), r.i32(), r.i32()
    if not all(0 < v <= MAX_AXIS for v in (x, y, z)):
        raise NbtError("The file's dimensions are invalid")
    return x, y, z


def _read_palette(r: _Reader, depth: int) -> list[str]:
    """The block names of a palette (a list of compounds with a "Name")."""
    item_type, length = r.list_header()
    if length and item_type != COMPOUND:
        raise NbtError("The file's palette is invalid")
    names = []
    for _ in range(length):
        name = ""
        for tag, key in r.entries(depth + 1):
            if key == "Name" and tag == STRING:
                name = r.string()
            else:
                r.skip(tag, depth + 2)
        names.append(name)
    return names


def _read_block_states(r: _Reader, depth: int) -> list[int]:
    """The palette index ("state") of every block."""
    item_type, length = r.list_header()
    if length and item_type != COMPOUND:
        raise NbtError("The file's block list is invalid")
    states = []
    for _ in range(length):
        state = -1
        for tag, key in r.entries(depth + 1):
            if key == "state" and tag == INT:
                state = r.i32()
            else:
                r.skip(tag, depth + 2)
        states.append(state)
    return states


def read_structure(raw: bytes) -> StructureInfo:
    """Read the size and block count of a structure file, or raise NbtError."""
    if not raw:
        raise NbtError("The file is empty")
    r = _Reader(decompress(raw))
    if r.u8() != COMPOUND:
        raise NbtError("This file is not an NBT file")
    r.skip_string()  # the root's name, usually empty

    size = None
    palette: Optional[list[str]] = None
    states: Optional[list[int]] = None
    data_version = None
    for tag, key in r.entries(1):
        if key == "size":
            size = _read_size(r, tag)
        elif key == "palette" and tag == LIST:
            palette = _read_palette(r, 1)
        elif key == "palettes" and tag == LIST and palette is None:
            # Several palettes (random variants): the first one is enough
            item_type, length = r.list_header()
            if length and item_type != LIST:
                raise NbtError("The file's palette is invalid")
            for i in range(length):
                if i == 0:
                    palette = _read_palette(r, 2)
                else:
                    r.skip(LIST, 2)
        elif key == "blocks" and tag == LIST:
            states = _read_block_states(r, 1)
        elif key == "DataVersion" and tag == INT:
            data_version = r.i32()
        else:
            r.skip(tag, 1)

    if size is None or states is None:
        raise NbtError(
            "This NBT file is not a structure (Create schematic or structure block)"
        )
    palette = palette or []
    air = {i for i, name in enumerate(palette) if name in AIR_BLOCKS}
    blocks = sum(1 for s in states if 0 <= s < len(palette) and s not in air)
    return StructureInfo(*size, block_count=blocks, data_version=data_version)
