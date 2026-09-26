"""Generator of Mathcad 13 X-Y plot blobs (reverse-engineered MFC serialization).

A plot blob = template prefix (eqRegion/docRegion...) + expression tree + d2_graph_format (graphData:
size, axisFormat: axis flags, trace2D: 16 trace formats) + rest.

Expression tree: pre-order records  [id][40 40][op u16][00 00][side][parent] + extra:
  0x0f02 leaf        + 00 00 + value   (identifier: [len+1][len]name\\0, number: [len+1][01][len]digits\\0)
  0x0f00 empty       + 00 00 00
  0x4b95 unary minus + 00   (single right child)
  0x708e arg list    + 00   (single right child)
  0xce12 f(x): left = name leaf, right = 708e(arg)     0xc30a comma list (left-assoc)    0xc19f pair
  0xc119 root.  side: 0x40 left / 0x80 right (+0x24 identifiers, +0x34 numbers, +0x02 auto value).
After a childless node: one 00 per ancestor completed through right-child links (root excluded).
Node numbers (id, parent, trailer) >= 0x40 are escaped: written as 40 xx.
Trailer: [next id][00][02 00 00 00].
Axis record (axisFormat, x at +20, y at +42, 21 bytes + 0x2a): [0] flags 0x01 log, 0x02 grid lines, 0x04 numbered,
0x08 autoscale, 0x40 auto grid; [9] number of grid intervals (0 = auto, works with any flags);
[14..16] grid colour R G B.
graphData (+ after the name): [15] bit0 = legend below the plot; [23] axis style 0 none, 1 boxed, 2 crossed;
[27]/[31] int32 plot width/height (units ~7 pt).
Trace record: 29 [line: 0 none,1 solid,2 dot,3 dash,4 dadot] [R G B] [flags] {symbol}{weight}{type} 01 [idx] 01
flags bit0 = default symbol (else a symbol byte follows), bit2 = default weight, bit3 = default type.
"""
import base64
import gzip
import os
import re
import struct

HERE = os.path.dirname(os.path.abspath(__file__))
SKILL_TPL = os.path.join(HERE, "..", "templates", "plot_2fx.bin")

COLORS = {
    "red": (255, 0, 0), "blue": (0, 0, 255), "green": (0, 160, 0), "magenta": (255, 0, 255),
    "cyan": (0, 200, 200), "brown": (128, 64, 0), "black": (0, 0, 0), "orange": (255, 128, 0),
    "darkgreen": (0, 128, 0), "purple": (128, 0, 160), "gray": (128, 128, 128),
}
LINES = {"none": 0, "solid": 1, "dot": 2, "dash": 3, "dadot": 4}
SYMBOLS = {"none": 0, "x": 1, "plus": 2, "box": 3, "diamond": 4, "o": 5, "dot": 6, "circle": 5}


# ------------------------------------------------------------------------------------------------ tree
class N:
    def __init__(self, op, left=None, right=None, value=None, kind=None):
        self.op, self.left, self.right, self.value, self.kind = op, left, right, value, kind


def ident(name):
    return N(0x0F02, value=name, kind="id")


def number(s, auto=False):
    s = str(s)
    if s.startswith("-"):
        return N(0x4B95, right=number(s[1:], auto), kind="neg_auto" if auto else "neg")
    return N(0x0F02, value=s, kind="auto" if auto else "num")


def empty():
    return N(0x0F00)


def pair(a, b):
    return N(0xC19F, a, b)


def parse_item(s):
    """'f(t)', 'x', 'x.1', '0.95', '-1'."""
    s = s.strip()
    m = re.fullmatch(r"([A-Za-z][A-Za-z0-9_.]*)\(([A-Za-z][A-Za-z0-9_.]*)\)", s)
    if m:
        return N(0xCE12, ident(m.group(1)), N(0x708E, right=ident(m.group(2))))
    if re.fullmatch(r"-?\d+(\.\d+)?", s):
        return number(s)
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_.]*", s):
        return ident(s)
    raise ValueError("unsupported plot expression: %r" % s)


def comma_list(items):
    nodes = [parse_item(x) for x in items]
    cur = nodes[0]
    for n in nodes[1:]:
        cur = N(0xC30A, cur, n)
    return cur


def limits(lim):
    if lim is None:
        return pair(number("0", auto=True), number("0", auto=True))
    lo, hi = lim
    return pair(number(repr_num(hi)), number(repr_num(lo)))  # left = upper, right = lower


def repr_num(v):
    if isinstance(v, str):
        return v
    s = ("%.6g" % v)
    if "e" in s:
        s = ("%.10f" % v).rstrip("0").rstrip(".")
    return s


def axis_block(lim, exprs):
    # pair( pair( limits, markers ), exprs )
    return pair(pair(limits(lim), pair(empty(), empty())), exprs)


def build_tree(ys, xs, ylim=None, xlim=None):
    y2 = pair(pair(pair(number("0", True), number("0", True)), pair(empty(), empty())), empty())
    root = N(0xC119, pair(axis_block(ylim, comma_list(ys)), y2), axis_block(xlim, comma_list(xs)))
    out = bytearray()
    counter = [6]

    def value_bytes(n):
        v = n.value.encode("ascii")
        if n.kind in ("num", "auto"):
            return bytes([len(v) + 1, 1, len(v)]) + v + b"\x00"
        return bytes([len(v) + 1, len(v)]) + v + b"\x00"

    def side_byte(n, is_right, parent_is_root_holder=False):
        base = 0x80 if is_right else 0x40
        if n.op == 0x0F02:
            if n.kind == "id":
                return base | 0x24
            if n.kind == "num":
                return base | 0x34
            return base | 0x36
        if n.op == 0x4B95:
            return base | (0x02 if n.kind == "neg_auto" else 0)
        return base

    # emit with explicit stack to compute closing zeros
    def enc(v):
        # node numbers >= 0x40 are written with an escape byte 0x40 (seen up to 0x7f in Mathcad's own plots)
        assert v < 0x100, "plot expression too large"
        return bytes([v]) if v < 0x40 else bytes([0x40, v])

    def emit(n, parent_id, is_right, ancestors):
        nid = counter[0]
        counter[0] += 1
        out.extend(enc(nid) + b"\x40\x40" + struct.pack("<H", n.op) + b"\x00\x00" +
                   bytes([side_byte(n, is_right)]) + enc(parent_id))
        if n.op == 0x0F02:
            out.extend(b"\x00\x00" + value_bytes(n))
        elif n.op == 0x0F00:
            out.extend(b"\x00\x00\x00")
        elif n.op in (0x4B95, 0x708E):
            out.extend(b"\x00")
        kids = [(n.left, False), (n.right, True)]
        has = [k for k in kids if k[0] is not None]
        if not has:
            # closing zeros: walk up through right-child links, excluding the root
            chain = ancestors + [(nid, is_right)]
            k = len(chain) - 1
            while k >= 1 and chain[k][1] and chain[k - 1][0] != 6:
                out.append(0)
                k -= 1
            return
        for child, right in has:
            emit(child, nid, right, ancestors + [(nid, is_right)])

    emit(root, 5, True, [])
    next_id = counter[0]
    out.extend(enc(next_id) + b"\x00\x02\x00\x00\x00")
    return bytes(out)


# ------------------------------------------------------------------------------------------------ traces
def trace_record(idx, line="solid", color="red", weight=None, symbol=None):
    r, g, b = COLORS[color] if isinstance(color, str) else color
    flags = 0x1F
    extra = b""
    if symbol and symbol != "none":
        flags &= ~0x01
        extra += bytes([SYMBOLS[symbol]])
    if weight and weight != 1:
        flags &= ~0x04
        extra += bytes([weight])
    return bytes([0x29, LINES[line], r, g, b, flags]) + extra + bytes([0x01, idx, 0x01])


DEFAULT_TRACES = [("solid", "red"), ("solid", "blue"), ("solid", "green"), ("solid", "magenta"),
                  ("solid", "cyan"), ("solid", "brown"), ("solid", "black"), ("dot", "red"), ("dot", "blue"),
                  ("dot", "green"), ("dot", "magenta"), ("dot", "cyan"), ("dot", "brown"), ("dot", "black"),
                  ("dash", "red"), ("dash", "blue")]


def _parse_traces(d, start):
    """Return end offset of the 16 trace records beginning at start."""
    pos = start
    for _ in range(16):
        assert d[pos] == 0x29, "trace record expected at %d: %s" % (pos, d[pos:pos + 12].hex(" "))
        flags = d[pos + 5]
        pos += 6
        if not flags & 0x01:
            pos += 1
        if not flags & 0x04:
            pos += 1
        if not flags & 0x08:
            pos += 1
        pos += 3
    return pos


# ------------------------------------------------------------------------------------------------ blob
def make_plot(ys, xs, traces=None, grid=True, size=(80, 48), ylim=None, xlim=None, logx=False, logy=False,
              axes="boxed", xgrids=None, ygrids=None, grid_color=(0, 255, 0), template=SKILL_TPL):
    """axes: 'boxed' | 'crossed' | 'none'; xgrids/ygrids: number of grid intervals (None = auto)."""
    d = open(template, "rb").read()
    t0 = d.find(b"tree") + 4 + 17
    t1 = d.find(b"\x0fd2_graph_format")
    # template tail after the tree trailer: find the trailer start = after last record; we rebuild whole tree
    tail = d[t1:]
    body = bytearray(d[:t0] + build_tree(ys, xs, ylim, xlim) + tail)
    # axis flags
    p = body.find(b"axisFormat") + 20
    assert body[p + 21] == 0x2A
    for off, is_log in ((0, logx), (22, logy)):
        f = body[p + off]
        f = (f | 0x02) if grid else (f & ~0x02)
        f = (f | 0x01) if is_log else (f & ~0x01)
        body[p + off] = f
        body[p + off + 14:p + off + 17] = bytes(grid_color)
    for off, n in ((0, xgrids), (22, ygrids)):
        if n:
            assert 2 <= n <= 99
            body[p + off + 9] = n
    # size
    g = body.find(b"graphData") + len(b"graphData")
    k = g + 27
    assert body[g + 19] == 3
    body[g + 23] = {"none": 0, "boxed": 1, "crossed": 2}[axes]
    body[k:k + 4] = struct.pack("<i", size[0])
    body[k + 4:k + 8] = struct.pack("<i", size[1])
    # traces
    j = body.find(b"trace2D") + len(b"trace2D") + 6 + 13
    end = _parse_traces(body, j)
    recs = b""
    traces = list(traces or [])
    for i in range(16):
        if i < len(traces):
            tr = traces[i]
            if isinstance(tr, dict):
                recs += trace_record(i + 1, **tr)
            else:
                recs += trace_record(i + 1, *tr)
        else:
            recs += trace_record(i + 1, *DEFAULT_TRACES[i])
    body[j:end] = recs
    return bytes(body)


# ------------------------------------------------------------------------------------------------ xmcd helpers
def encode(blob):
    return base64.b64encode(gzip.compress(blob)).decode()
