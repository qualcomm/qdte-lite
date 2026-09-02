# Copyright (c) Qualcomm Technologies, Inc. and/or its subsidiaries.
# SPDX-License-Identifier: BSD-3-Clause-Clear
"""libfdt-backed replacement for the pyfdt object-tree API used by QDTE.

Design: parse the flattened blob ONCE into an ordered Python tree of
FdtNode/FdtProperty objects (via pylibfdt's read API), mutate the tree
directly, and serialize with libfdt's sequential writer (FdtSw) walking
the tree in document order.  libfdt is the parser, emitter and validator;
the tree is the single mutable source of truth.

Consequences relied on by dtwrapper:
  * object identity is stable across mutations (undo machinery holds
    property objects and subtree snapshots);
  * child order is explicit, so positional insert/index -- and therefore
    positional delete-undo -- work exactly like pyfdt;
  * emission is deterministic: the same tree content and order always
    yields the same bytes, so sha256-of-bytes undo/redo verification
    keeps working (no content-based hashing needed);
  * to_dtb(mappings) fills {path: (start, end)} byte ranges from the
    emitted blob, restoring the hex-view highlighting that the PyPI
    pyfdt fallback had disabled.

Only the surface QDTE consumes is implemented; this is intentionally not
a general pyfdt drop-in.
"""

import struct

import libfdt

_QUIET_NOTFOUND = (libfdt.NOTFOUND,)


def _is_strings(raw):
    """Replicate dtc's heuristic: a property is a string list when it is
    non-empty, NUL-terminated, has no leading NUL, and every byte is either
    a NUL separator or a printable/whitespace character."""
    if not raw or raw[-1] != 0 or raw[0] == 0:
        return False
    for b in raw:
        if b == 0:
            continue
        if b < 0x20 or b >= 0x7F:
            if b not in (0x09, 0x0A, 0x0D):
                return False
    return True


# ---------------------------------------------------------------------------
# properties
# ---------------------------------------------------------------------------


class FdtProperty:
    """Empty (value-less) property; base class of the typed variants."""

    def __init__(self, name):
        self.name = name

    def raw_value(self):
        return b""

    def to_raw(self):
        return self.raw_value()

    def __str__(self):
        return self.name


class FdtPropertyWords(FdtProperty):
    """Property holding 32-bit big-endian cells (list of ints)."""

    def __init__(self, name, words):
        FdtProperty.__init__(self, name)
        words = list(words)
        for word in words:
            if not 0 <= word <= 0xFFFFFFFF:
                raise Exception(
                    "Invalid value for word %d, requires 0 <= number <= 4294967295"
                    % word
                )
        if not words:
            raise Exception("Invalid Words")
        self.words = words

    def raw_value(self):
        return struct.pack(">%dI" % len(self.words), *self.words)


class FdtPropertyStrings(FdtProperty):
    """Property holding NUL-terminated strings (list of str)."""

    def __init__(self, name, strings):
        FdtProperty.__init__(self, name)
        strings = list(strings)
        if not strings:
            raise Exception("Invalid Strings")
        self.strings = strings

    def raw_value(self):
        return b"\0".join(s.encode("ascii") for s in self.strings) + b"\0"

    def __getitem__(self, idx):
        return self.strings[idx]


class FdtPropertyBytes(FdtProperty):
    """Property holding raw bytes (pyfdt compatibility: SIGNED ints)."""

    def __init__(self, name, bytez):
        FdtProperty.__init__(self, name)
        bytez = list(bytez)
        for byte in bytez:
            if not -128 <= byte <= 255:
                raise Exception(
                    "Invalid value for byte %d, requires -128 <= number <= 255" % byte
                )
        if not bytez:
            raise Exception("Invalid Bytes")
        self.bytes = bytez

    def raw_value(self):
        return bytes((b & 0xFF) for b in self.bytes)


def _property_from_raw(name, raw):
    """Classify a property's raw value with the dtc heuristic (matching
    pyfdt): empty -> EMPTY, string-shaped -> STRINGS, multiple-of-4 ->
    WORDS, anything else -> BYTES."""
    if len(raw) == 0:
        return FdtProperty(name)
    if _is_strings(raw):
        return FdtPropertyStrings(
            name, [s.decode("ascii") for s in bytes(raw).split(b"\0")[:-1]]
        )
    if len(raw) % 4 == 0:
        return FdtPropertyWords(
            name, list(struct.unpack(">%dI" % (len(raw) // 4), raw))
        )
    return FdtPropertyBytes(name, list(struct.unpack("%db" % len(raw), raw)))


# ---------------------------------------------------------------------------
# nodes
# ---------------------------------------------------------------------------


class FdtNode:
    """A device-tree node with an ordered children list (properties and
    subnodes interleaved in document order, exposed as ``subdata``)."""

    def __init__(self, name):
        self.name = name
        self.parent = None
        self.subdata = []

    def get_name(self):
        return self.name

    def set_parent_node(self, node):
        self.parent = node

    def __str__(self):
        return self.name

    def append(self, item):
        if isinstance(item, FdtNode):
            item.parent = self
        self.subdata.append(item)

    def insert(self, idx, item):
        if isinstance(item, FdtNode):
            item.parent = self
        self.subdata.insert(idx, item)

    def index(self, name):
        for i, child in enumerate(self.subdata):
            if child.name == name:
                return i
        raise ValueError("%s not found" % name)

    def remove(self, name):
        del self.subdata[self.index(name)]

    def walk(self):
        """Yield (path, item) for every descendant, pre-order, with paths
        relative to this node (leading '/')."""
        for child in self.subdata:
            yield ("/" + child.name, child)
            if isinstance(child, FdtNode):
                for sub_path, sub_item in child.walk():
                    yield ("/" + child.name + sub_path, sub_item)

    def to_raw(self):
        return self.name


# ---------------------------------------------------------------------------
# tree container
# ---------------------------------------------------------------------------


class Fdt:
    """The parsed device tree: root node plus blob-level metadata that must
    survive a load -> emit round trip."""

    def __init__(self, root, memrsv=None, boot_cpuid=0):
        self.root = root
        self.memrsv = list(memrsv or [])
        self.boot_cpuid = boot_cpuid

    def resolve_path(self, path):
        """Resolve an absolute path to a node/property, or None. First
        match wins for duplicate sibling names (pyfdt semantics)."""
        if path in ("", "/"):
            return self.root
        current = self.root
        for part in path.split("/"):
            if not part:
                continue
            if not isinstance(current, FdtNode):
                return None
            for child in current.subdata:
                if child.name == part:
                    current = child
                    break
            else:
                return None
        return current

    # -- serialization ------------------------------------------------------

    def _emit_node(self, sw, node):
        # FDT structure requires properties before subnodes within a node;
        # partition stably so list order is preserved within each group.
        for child in node.subdata:
            if not isinstance(child, FdtNode):
                sw.property(child.name, child.raw_value())
        for child in node.subdata:
            if isinstance(child, FdtNode):
                sw.begin_node(child.name)
                self._emit_node(sw, child)
                sw.end_node()

    def to_dtb(self, mappings=None):
        """Serialize deterministically via libfdt's sequential writer.
        When ``mappings`` is a dict, fill it with {path: (start, end)}
        byte ranges of each node header / property record in the blob."""
        # FdtSw grows its buffer in INC_SIZE steps, and every write method
        # retries through check_space() when it runs out.  as_fdt() does not:
        # it calls fdt_finish() once and raises FDT_ERR_NOSPACE if the strings
        # block and header fixups do not fit in what is left.  A tree whose
        # serialized size lands on a multiple of INC_SIZE leaves zero slack
        # and fails, which makes this a size lottery rather than a real limit.
        #
        # Seed the buffer past the point where that can happen and retry with
        # more room if it still does.
        size_hint = libfdt.FdtSw.INC_SIZE
        while True:
            sw = libfdt.FdtSw(size_hint)
            for addr, size in self.memrsv:
                sw.add_reservemap_entry(addr, size)
            sw.finish_reservemap()
            sw.begin_node("")
            self._emit_node(sw, self.root)
            sw.end_node()
            try:
                fdt = sw.as_fdt()
                break
            except libfdt.FdtException as ex:
                if ex.err != -libfdt.NOSPACE:
                    raise
                # len(sw) is the grown buffer; ask for meaningfully more than
                # the increment so this terminates in one further attempt.
                size_hint = len(sw.as_bytearray()) + libfdt.FdtSw.INC_SIZE * 16
        fdt.pack()
        buf = bytearray(fdt.as_bytearray())
        if self.boot_cpuid:
            # fdt_header.boot_cpuid_phys lives at byte offset 28; FdtSw has
            # no setter for it.
            struct.pack_into(">I", buf, 28, self.boot_cpuid)
        blob = bytes(buf)
        if mappings is not None:
            self._fill_mappings(blob, mappings)
        return blob

    @staticmethod
    def _fill_mappings(blob, mappings):
        fdt = libfdt.Fdt(blob)
        base = fdt.off_dt_struct()

        def visit(offset, path):
            name = fdt.get_name(offset)
            name_padded = (len(name) + 1 + 3) & ~3
            mappings[path or "/"] = (base + offset, base + offset + 4 + name_padded)
            poff = fdt.first_property_offset(offset, quiet=_QUIET_NOTFOUND)
            while poff >= 0:
                prop = fdt.get_property_by_offset(poff)
                record = 12 + ((len(bytes(prop)) + 3) & ~3)
                mappings["%s/%s" % (path, prop.name)] = (
                    base + poff,
                    base + poff + record,
                )
                poff = fdt.next_property_offset(poff, quiet=_QUIET_NOTFOUND)
            soff = fdt.first_subnode(offset, quiet=_QUIET_NOTFOUND)
            while soff >= 0:
                visit(soff, "%s/%s" % (path, fdt.get_name(soff)))
                soff = fdt.next_subnode(soff, quiet=_QUIET_NOTFOUND)

        visit(0, "")

    def to_dts(self):
        """Native DTS emitter (libfdt has none)."""
        lines = ["/dts-v1/;", ""]
        for addr, size in self.memrsv:
            lines.append("/memreserve/ 0x%016x 0x%016x;" % (addr, size))
        if self.memrsv:
            lines.append("")

        def escape(s):
            return s.replace("\\", "\\\\").replace('"', '\\"')

        def emit(node, depth, label):
            indent = "\t" * depth
            lines.append("%s%s {" % (indent, label))
            for child in node.subdata:
                cindent = "\t" * (depth + 1)
                if isinstance(child, FdtNode):
                    continue
                if isinstance(child, FdtPropertyStrings):
                    vals = ", ".join('"%s"' % escape(s) for s in child.strings)
                    lines.append("%s%s = %s;" % (cindent, child.name, vals))
                elif isinstance(child, FdtPropertyWords):
                    vals = " ".join("0x%x" % w for w in child.words)
                    lines.append("%s%s = <%s>;" % (cindent, child.name, vals))
                elif isinstance(child, FdtPropertyBytes):
                    vals = " ".join("%02x" % (b & 0xFF) for b in child.bytes)
                    lines.append("%s%s = [%s];" % (cindent, child.name, vals))
                else:
                    lines.append("%s%s;" % (cindent, child.name))
            for child in node.subdata:
                if isinstance(child, FdtNode):
                    emit(child, depth + 1, child.name)
            lines.append("%s};" % indent)

        emit(self.root, 0, "/")
        return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# loader
# ---------------------------------------------------------------------------


class FdtBlobParse:
    """Parse a DTB blob (from an open binary file) into an Fdt tree."""

    def __init__(self, infile):
        self._data = bytes(infile.read())

    def to_fdt(self):
        fdt = libfdt.Fdt(self._data)

        def parse_children(offset, node):
            poff = fdt.first_property_offset(offset, quiet=_QUIET_NOTFOUND)
            while poff >= 0:
                prop = fdt.get_property_by_offset(poff)
                node.subdata.append(_property_from_raw(prop.name, bytes(prop)))
                poff = fdt.next_property_offset(poff, quiet=_QUIET_NOTFOUND)
            soff = fdt.first_subnode(offset, quiet=_QUIET_NOTFOUND)
            while soff >= 0:
                child = FdtNode(fdt.get_name(soff))
                node.append(child)
                parse_children(soff, child)
                soff = fdt.next_subnode(soff, quiet=_QUIET_NOTFOUND)

        root = FdtNode("/")
        parse_children(0, root)
        memrsv = [tuple(fdt.get_mem_rsv(i)) for i in range(fdt.num_mem_rsv())]
        return Fdt(root, memrsv, fdt.boot_cpuid_phys())
