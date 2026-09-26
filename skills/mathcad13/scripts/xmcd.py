#!/usr/bin/env python3
"""xmcd.py - Mathcad 13 worksheet (.xmcd, XML) toolkit: linear math syntax <-> Math20 XML.

Commands
  read     FILE.xmcd [--xml] [--nores]        regions as readable text: formulas, saved results, text, plots
  build    SPEC.txt OUT.xmcd [--letter]       build a worksheet from a line-based spec (see SPEC SYNTAX)
  relayout IN.xmcd OUT.xmcd [--gap 8]         push overlapping regions down using the sizes Mathcad saved
  set      IN.xmcd OUT.xmcd NAME=EXPR ...     replace right-hand side of the first definition of NAME
  expr     "STATEMENT"                        print the <math> XML for one statement (for MathInterface.XML)

Typical loop: build -> mc.ps1 -SaveAs out.xmcd (Mathcad computes and stores sizes/results)
              -> relayout -> mc.ps1 -SaveAs final.xmcd / report.rtf -> read

SPEC SYNTAX (one region per line; blank lines add vertical space)
  # Heading / ## Subheading / > plain text      text regions (Cyrillic is fine in text)
      inline markup in text: **bold** *italic* _{sub} ^{sup};  a line "---" = page break
  y = MPa @prec=2 zeros                         per-formula number format: prec=N zeros gen|dec|sci|eng
                                                exp=N (exponential threshold) matrix|table (vector display)
  x := 2.5 m                                    definition (number followed by a unit = product)
  f(x, y) := x^2 + y                            function definition
  g :== 9.81 m/s^2                              global definition (also  g ≡ ...)
  y =            F/A = kPa                      evaluation; text after '=' is a unit override
  e ->           e -> simplify | factor         symbolic evaluation, commands separated by '|'
  solve(e) ...   e -> solve, x                  command with argument
  Given / x^2 + y^2 == 4 / s := Find(x, y)      solve block ('==' is the bold boolean equals)
  i := 0..10     t := 0, 0.1..1                 range variables (with step)
  M := [1, 2; 3, 4]    v := [1; 2; 3]           matrices (',' columns, ';' rows)
  v[i]  M[i, j]  col(M, j)                      indexing / column (MC13 has no row operator: use submatrix)
  sqrt(x) nthroot(n,x) abs(x) det(M) transpose(M) conj(z) cross(a,b) vectorize(e) x! vsum(v)
  sum(e, i) sum(e, i, a, b)  prod(...)  int(e, x) int(e, x, a, b)  diff(e, x[, n])  lim(e, x, a[, "left"])
  σ.max := ...                                  literal subscript (σ_max)
  f(n) := prog { s <- 0; for k in 0..n { s <- s + k }; s }     program (also multi-line inside { })
      statements: x <- e | if c { .. } | else { .. } | for k in r { .. } | while c { .. }
                  return e | break | continue | try { .. } catch { .. }  ('if c: stmt' short form)
  x := 2   // comment                           comment -> text region to the right of the formula
  !x := 2                                       disabled region (not evaluated)
  @plot Y vs X                                  XY plot of vectors (matrix Y -> one trace per column)
  @plot Y vs X points                           same, markers only (experimental data)
  @plot f(x) vs x                               function over a range variable x
  @plot f(t), g(t) vs t                         two functions, second one dotted
  @plot Yd, fit(z) vs Xd, z                     data points + fitted curve (fit over range z)
  ... logx | logy | loglog                      logarithmic axes (any variant), e.g. "@plot Y vs X points loglog"
      plots are cloned from binary templates (templates/plot_*.bin); names must be ASCII; axes autoscale
"""
import argparse
import base64
import gzip
import os
import re
import sys
import uuid
from decimal import Decimal
import xml.etree.ElementTree as ET

WS = "http://schemas.mathsoft.com/worksheet20"
ML = "http://schemas.mathsoft.com/math20"
UN = "http://schemas.mathsoft.com/units10"
PV = "http://schemas.mathsoft.com/provenance10"
WS10 = "http://schemas.mathsoft.com/worksheet10"
ML10 = "http://schemas.mathsoft.com/math10"
HERE = os.path.dirname(os.path.abspath(__file__))
TEMPLATE = os.path.join(HERE, "..", "templates", "minimal20.xmcd")
PLOT_DIR = os.path.join(HERE, "..", "templates")
# template -> identifiers of its expression tree, in the order plot_ids() returns them
PLOT_TEMPLATES = {
    "xy": ("plot_xy.bin", ["y", "x"]),                    # line: y vs x            (qsheet feat_04a #11)
    "pts": ("plot_pts.bin", ["population", "time"]),      # markers: y vs x         (feat_07 #19)
    "fx": ("plot_fx.bin", ["f", "x", "x"]),               # line: f(x) vs x         (feat_04a #70)
    "2fx": ("plot_2fx.bin", ["x", "t", "y", "t", "t"]),   # x(t) solid, y(t) dotted vs t (pendulum #28)
    "datafit": ("plot_datafit.bin", ["Y", "f", "z", "X", "z"]),  # markers Y vs X + line f(z) vs z (linfitlo #15)
}

for _p, _u in (("", WS), ("ml", ML), ("u", UN), ("p", PV)):
    ET.register_namespace(_p, _u)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ============================================================================ tokenizer
ID_START = r"A-Za-z_À-ɏͰ-ϿЀ-ӿ∞°ℏℵ∇$%∠⇒⇔≈±∙"
ID_REST = ID_START + r"0-9'"
TOKEN_RE = re.compile(
    r"(?P<ws>[ \t]+)"
    r"|(?P<nl>\r?\n)"
    r"|(?P<imag>(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?[ij](?![" + ID_REST + r"]))"
    r"|(?P<num>(?:\d+(?:\.\d+)?|\.\d+)(?:[eE][+-]?\d+)?)"
    r"|(?P<id>[" + ID_START + r"][" + ID_REST + r"]*(?:\.[" + ID_REST + r"]+)?)"
    r"|(?P<str>\"(?:[^\"\\]|\\.)*\")"
    r"|(?P<op>:==|:=|->|<-|==|!=|<=|>=|\.\.|[≡≠≤≥→←·×=+\-*/^()\[\],;<>!|{}:])"
)
OP_ALIASES = {"≡": ":==", "≠": "!=", "≤": "<=", "≥": ">=", "→": "->", "←": "<-", "·": "*"}
# 'in' (inch) and 'error' (built-in function) stay identifiers; 'in' is matched by value inside 'for'
WORD_OPS = {"and", "or", "xor", "not", "prog", "if", "else", "otherwise", "for", "while",
            "return", "break", "continue", "try", "catch"}


class Tok:
    __slots__ = ("kind", "val", "pos")

    def __init__(self, kind, val, pos):
        self.kind, self.val, self.pos = kind, val, pos

    def __repr__(self):
        return f"{self.kind}:{self.val}"


def tokenize(src):
    toks, i = [], 0
    while i < len(src):
        m = TOKEN_RE.match(src, i)
        if not m:
            raise SyntaxError(f"unexpected character {src[i]!r} at {i} in: {src}")
        kind = m.lastgroup
        val = m.group(kind)
        i = m.end()
        if kind == "ws":
            continue
        if kind == "op":
            val = OP_ALIASES.get(val, val)
        if kind == "id" and val in WORD_OPS:
            kind = "kw"
        toks.append(Tok(kind, val, m.start()))
    toks.append(Tok("eof", None, len(src)))
    return toks


# ============================================================================ parser -> AST
# AST nodes are tuples: ('num',s) ('imag',s) ('id',name,sub) ('str',s) ('parens',e)
# ('op',name,args) ('call',fexpr,args) ('matrix',rows,cols,rowmajor) ('range',a,b[,step2])
# ('prog',stmts) and statements ('local',lhs,e) ('if',c,body) ('else',body) ('for',var,rng,body)
# ('while',c,body) ('return',e) ('break',) ('continue',) ('try',a,b)
BIN = {  # token -> (left bp, right bp, ml element)
    "or": (10, 11, "or"), "xor": (10, 11, "xor"), "and": (20, 21, "and"),
    "==": (30, 31, "equal"), "!=": (30, 31, "notEqual"), "<": (30, 31, "lessThan"), ">": (30, 31, "greaterThan"),
    "<=": (30, 31, "lessOrEqual"), ">=": (30, 31, "greaterOrEqual"),
    "+": (40, 41, "plus"), "-": (40, 41, "minus"),
    "*": (50, 51, "mult"), "/": (50, 51, "div"), "×": (50, 51, "crossProduct"),
    "^": (71, 70, "pow"),
}
SPECIAL_OPS = {  # function-call syntax mapped to dedicated Math20 operators
    "sqrt": ("sqrt", 1), "nthroot": ("nthRoot", 2), "abs": ("absval", 1), "det": ("determinant", 1),
    "transpose": ("transpose", 1), "conj": ("conjugate", 1), "cross": ("crossProduct", 2),
    "vectorize": ("vectorize", 1), "vsum": ("vectorSum", 1), "col": ("matcol", 2),  # no row operator in MC13
    "not": ("not", 1),
}
SOLVER_OPS = {"Find", "Minerr", "Maximize", "Minimize", "Odesolve", "polyroots", "genfit", "Pdesolve", "numol"}
SOLVER_DEFAULT_ATTRS = {
    "Find": 'auto-method="true" method="conjugate" derivative-estimation="central" variable-estimation="tangent" '
            'linear-check="false" multistart="false" evolutionary="false"',
    "polyroots": 'method="laguerre"',
    "Odesolve": 'method="adaptive"',
    "genfit": 'method="optimized levenberg-marquardt"',   # required by Math20.xsd: without it the FILE is "corrupted"
}
for _n in ("Maximize", "Minimize"):
    SOLVER_DEFAULT_ATTRS[_n] = SOLVER_DEFAULT_ATTRS["Find"]
# Minerr with auto-method silently returns a WRONG least-squares answer (x==1, x==3 -> 1 instead of 2);
# Levenberg-Marquardt gives the true least-squares solution (checked 2026-09-25)
SOLVER_DEFAULT_ATTRS["Minerr"] = SOLVER_DEFAULT_ATTRS["Find"].replace(
    'auto-method="true" method="conjugate"', 'auto-method="false" method="levenberg"')


class Parser:
    def __init__(self, src):
        self.src = src
        self.t = [x for x in tokenize(src)]
        self.i = 0
        self.skip_nl = True

    # -- token helpers
    def peek(self, k=0):
        j = self.i
        n = 0
        while True:
            tok = self.t[j]
            if self.skip_nl and tok.kind == "nl":
                j += 1
                continue
            if n == k:
                return tok
            n += 1
            j += 1

    def next(self):
        while self.skip_nl and self.t[self.i].kind == "nl":
            self.i += 1
        tok = self.t[self.i]
        self.i += 1
        return tok

    def at(self, val, kind=None):
        tok = self.peek()
        return tok.val == val and (kind is None or tok.kind == kind)

    def expect(self, val):
        tok = self.next()
        if tok.val != val:
            raise SyntaxError(f"expected {val!r} but got {tok.val!r} at {tok.pos} in: {self.src}")
        return tok

    def accept(self, val):
        if self.at(val):
            return self.next()
        return None

    # -- expressions
    def expr(self, rbp=0):
        tok = self.next()
        left = self.nud(tok)
        while True:
            tok = self.peek()
            # implicit multiplication: number/closing bracket followed by identifier -> "10 kN", "2 m^2"
            if tok.kind == "id" and left[0] in ("num", "imag") and rbp < 50:
                right = self.expr(51)
                left = ("op", "mult", [left, right])
                continue
            if tok.kind == "op" and tok.val == "!" and rbp < 80:
                self.next()
                left = ("op", "factorial", [left])
                continue
            if tok.kind == "op" and tok.val == "(" and rbp < 80:
                self.next()
                args = self.arglist(")")
                left = self.make_call(left, args)
                continue
            if tok.kind == "op" and tok.val == "[" and rbp < 80:
                self.next()
                idx = self.arglist("]")
                left = ("op", "indexer", [left, idx[0] if len(idx) == 1 else ("seq", idx)])
                continue
            key = tok.val if tok.kind in ("op", "kw") else None
            if key in BIN:
                lbp, rbp2, name = BIN[key]
                if lbp <= rbp:
                    break
                self.next()
                if key == "^":
                    right = self.expr(rbp2 - 1)  # right assoc, allow unary minus in exponent
                else:
                    right = self.expr(rbp2)
                left = ("op", name, [left, right])
                continue
            break
        return left

    def nud(self, tok):
        if tok.kind == "num":
            return ("num", tok.val)
        if tok.kind == "imag":
            return ("imag", tok.val[:-1], tok.val[-1])
        if tok.kind == "str":
            return ("str", bytes(tok.val[1:-1], "utf-8").decode("unicode_escape") if "\\" in tok.val else tok.val[1:-1])
        if tok.kind == "id":
            name, _, sub = tok.val.partition(".")
            return ("id", name, sub or None)
        if tok.kind == "kw" and tok.val != "not" and self.peek().val == "(":
            return ("id", tok.val, None)          # built-in function if(c, a, b) etc.
        if tok.kind == "kw" and tok.val == "not":
            return ("op", "not", [self.expr(60)])
        if tok.kind == "kw" and tok.val == "prog":
            return self.program_block()
        if tok.kind == "kw" and tok.val == "try":      # f(x) := try { 1/x } catch { 0 }
            a = self.body()
            self.expect("catch")
            return ("tryexpr", a, self.body())
        if tok.kind == "op":
            if tok.val == "-":
                return ("op", "neg", [self.expr(60)])
            if tok.val == "+":
                return self.expr(60)
            if tok.val == "(":
                e = self.expr()
                self.expect(")")
                return ("parens", e)
            if tok.val == "[":
                return self.matrix()
            if tok.val == "{":
                self.i -= 1
                return self.program_block()
        raise SyntaxError(f"unexpected {tok.val!r} at {tok.pos} in: {self.src}")

    def arglist(self, close):
        args = []
        if self.accept(close):
            return args
        while True:
            args.append(self.range_or_expr(allow_step=False))
            if self.accept(close):
                return args
            self.expect(",")

    def matrix(self):
        rows, cur = [], []
        while True:
            cur.append(self.expr())
            tok = self.next()
            if tok.val == ",":
                continue
            if tok.val == ";":
                rows.append(cur)
                cur = []
                continue
            if tok.val == "]":
                rows.append(cur)
                break
            raise SyntaxError(f"bad matrix syntax near {tok.val!r} in: {self.src}")
        ncols = len(rows[0])
        if any(len(r) != ncols for r in rows):
            raise SyntaxError(f"ragged matrix in: {self.src}")
        return ("matrix", len(rows), ncols, [e for r in rows for e in r])

    def range_or_expr(self, allow_step=True):
        e = self.expr()
        if self.at(".."):
            self.next()
            return ("range", e, self.expr())
        if allow_step and self.at(","):
            save = self.i
            self.next()
            e2 = self.expr()
            if self.at(".."):
                self.next()
                return ("range", ("seq", [e, e2]), self.expr())
            self.i = save
        return e

    def make_call(self, f, args):
        if f[0] == "id" and f[2] is None:
            name = f[1]
            if name in SPECIAL_OPS:
                el, n = SPECIAL_OPS[name]
                if len(args) != n:
                    raise SyntaxError(f"{name}() takes {n} argument(s)")
                return ("op", el, args)
            if name in ("sum", "prod"):
                el = "summation" if name == "sum" else "product"
                body, var = args[0], args[1]
                bounds = args[2:4] if len(args) >= 4 else None
                return ("bigop", el, var, body, bounds, None)
            if name == "int":
                return ("bigop", "integral", args[1], args[0], args[2:4] if len(args) >= 4 else None, None)
            if name == "diff":
                return ("bigop", "derivative", args[1], args[0], None, args[2] if len(args) > 2 else None)
            if name == "lim":
                direction = None
                if len(args) > 3 and args[3][0] == "str":
                    direction = args[3][1]
                return ("limit", args[1], args[0], args[2], direction)
            if name in SOLVER_OPS:
                return ("solver", name, args)
        return ("call", f, args)

    # -- statements
    def statement(self):
        """Top-level region statement."""
        disabled = False
        if self.at("!"):
            self.next()
            disabled = True
        tok = self.peek()
        if tok.kind == "id" and tok.val == "Given" and self.peek(1).kind == "eof":
            self.next()
            return ("given",), disabled
        lhs = self.expr()
        tok = self.peek()
        if tok.val in (":=", ":=="):
            self.next()
            rhs = self.range_or_expr()
            node = ("define" if tok.val == ":=" else "gdefine", self.def_lhs(lhs), rhs)
        elif tok.val == "->":
            self.next()
            cmds = []
            while self.peek().kind != "eof":
                parts = [self.expr()]
                while self.accept(","):
                    parts.append(self.expr())
                cmds.append(parts)
                if not self.accept("|"):
                    break
            node = ("symeval", lhs, cmds)
        elif tok.val == "=":
            self.next()
            unit = None if self.peek().kind == "eof" else self.expr()
            node = ("eval", lhs, unit)
        else:
            node = ("expr", lhs)
        if self.peek().kind != "eof":
            raise SyntaxError(f"unexpected {self.peek().val!r} at {self.peek().pos} in: {self.src}")
        return node, disabled

    def def_lhs(self, lhs):
        if lhs[0] == "call" and lhs[1][0] == "id" and all(a[0] == "id" for a in lhs[2]):
            return ("fundef", lhs[1], lhs[2])
        return lhs

    def program_block(self):
        self.expect("{")
        return ("prog", self.block_body())

    def block_body(self):
        old = self.skip_nl
        self.skip_nl = False
        stmts = []
        try:
            while True:
                while self.t[self.i].kind == "nl" or self.t[self.i].val == ";":
                    self.i += 1
                if self.t[self.i].val == "}":
                    self.i += 1
                    break
                stmts.append(self.prog_stmt())
        finally:
            self.skip_nl = old
        return stmts

    def body(self):
        """Body of if/for/while: '{ ... }' or ': stmt'."""
        if self.accept(":"):
            return [self.prog_stmt()]
        self.expect("{")
        return self.block_body()

    def prog_stmt(self):
        tok = self.t[self.i]
        if tok.kind == "kw":
            v = tok.val
            if v == "if":
                self.i += 1
                c = self.expr()
                return ("if", c, self.body())
            if v in ("else", "otherwise"):
                self.i += 1
                return ("else", self.body())
            if v == "for":
                self.i += 1
                var = self.next()
                self.expect("in")
                r = self.range_or_expr()
                return ("for", ("id", var.val, None), r, self.body())
            if v == "while":
                self.i += 1
                c = self.expr()
                return ("while", c, self.body())
            if v == "return":
                self.i += 1
                return ("return", self.expr())
            if v in ("break", "continue"):
                self.i += 1
                return (v,)
            if v == "try":
                self.i += 1
                a = self.body()
                self.expect("catch")
                return ("try", a, self.body())
        e = self.expr()
        if self.accept("<-"):
            return ("local", self.def_lhs(e), self.range_or_expr())
        return ("value", e)


# ============================================================================ AST -> Math20 XML
def number_text(s):
    if "e" in s or "E" in s:
        d = Decimal(s)
        return format(d, "f")
    if s.startswith("."):
        return "0" + s
    return s


def x_id(name, sub=None):
    a = f' subscript="{esc(sub)}"' if sub else ""
    return f'<ml:id xml:space="preserve"{a}>{esc(name)}</ml:id>'


def x_seq(items):
    return "<ml:sequence>" + "".join(items) + "</ml:sequence>"


def to_xml(n):
    k = n[0]
    if k == "num":
        return f"<ml:real>{number_text(n[1])}</ml:real>"
    if k == "imag":
        return f'<ml:imag symbol="{n[2]}">{number_text(n[1])}</ml:imag>'
    if k == "id":
        return x_id(n[1], n[2])
    if k == "str":
        return f'<ml:str xml:space="preserve">{esc(n[1])}</ml:str>'
    if k == "parens":
        return "<ml:parens>" + to_xml(n[1]) + "</ml:parens>"
    if k == "seq":
        return x_seq([to_xml(a) for a in n[1]])
    if k == "op":
        el = n[1]
        attr = ' style="default"' if el == "mult" else ""
        return f"<ml:apply><ml:{el}{attr}/>" + "".join(to_xml(a) for a in n[2]) + "</ml:apply>"
    if k == "call":
        args = n[2]
        inner = to_xml(args[0]) if len(args) == 1 else x_seq([to_xml(a) for a in args])
        return "<ml:apply>" + to_xml(n[1]) + inner + "</ml:apply>"
    if k == "solver":
        attrs = SOLVER_DEFAULT_ATTRS.get(n[1], "")
        args = n[2]
        inner = to_xml(args[0]) if len(args) == 1 else x_seq([to_xml(a) for a in args])
        return f"<ml:apply><ml:{n[1]} {attrs}/>" + inner + "</ml:apply>"
    if k == "matrix":
        rows, cols, elems = n[1], n[2], n[3]
        colmajor = [elems[r * cols + c] for c in range(cols) for r in range(rows)]
        return f'<ml:matrix rows="{rows}" cols="{cols}">' + "".join(to_xml(e) for e in colmajor) + "</ml:matrix>"
    if k == "range":
        return "<ml:range>" + to_xml(n[1]) + to_xml(n[2]) + "</ml:range>"
    if k == "bigop":
        _, el, var, body, bounds, degree = n
        s = f"<ml:apply><ml:{el}/><ml:lambda><ml:boundVars>{to_xml(var)}</ml:boundVars>{to_xml(body)}</ml:lambda>"
        if bounds:
            s += "<ml:bounds>" + to_xml(bounds[0]) + to_xml(bounds[1]) + "</ml:bounds>"
        if degree is not None:
            s += "<ml:degree>" + to_xml(degree) + "</ml:degree>"
        return s + "</ml:apply>"
    if k == "limit":
        _, var, body, point, direction = n
        d = f' direction="{direction}"' if direction else ""
        return (f"<ml:apply><ml:limit{d}/><ml:lambda><ml:boundVars>{to_xml(var)}</ml:boundVars>{to_xml(body)}"
                f"</ml:lambda>{to_xml(point)}</ml:apply>")
    if k == "fundef":
        return "<ml:function>" + to_xml(n[1]) + "<ml:boundVars>" + "".join(to_xml(a) for a in n[2]) + "</ml:boundVars></ml:function>"
    if k == "prog":
        return prog_xml(n[1], force=True)
    if k == "tryexpr":
        return stmt_xml(("try", n[1], n[2]))
    raise ValueError(f"cannot convert {n!r}")


def body_xml(stmts):
    return prog_xml(stmts, force=False)


def prog_xml(stmts, force):
    parts = [stmt_xml(s) for s in stmts]
    if len(parts) == 1 and not force:
        return parts[0]
    return "<ml:program>" + "".join(parts) + "</ml:program>"


def stmt_xml(s):
    k = s[0]
    if k == "local":
        return "<ml:localDefine>" + to_xml(s[1]) + to_xml(s[2]) + "</ml:localDefine>"
    if k == "if":
        return "<ml:ifThen>" + to_xml(s[1]) + body_xml(s[2]) + "</ml:ifThen>"
    if k == "else":
        return "<ml:otherwise>" + body_xml(s[1]) + "</ml:otherwise>"
    if k == "for":
        return "<ml:for>" + to_xml(s[1]) + to_xml(s[2]) + body_xml(s[3]) + "</ml:for>"
    if k == "while":
        return "<ml:while>" + to_xml(s[1]) + body_xml(s[2]) + "</ml:while>"
    if k == "return":
        return "<ml:return>" + to_xml(s[1]) + "</ml:return>"
    if k in ("break", "continue"):
        return f"<ml:{k}/>"
    if k == "try":
        return "<ml:tryCatch>" + body_xml(s[1]) + body_xml(s[2]) + "</ml:tryCatch>"
    if k == "value":
        return to_xml(s[1])
    raise ValueError(s)


def statement_xml(node):
    k = node[0]
    if k == "given":
        return x_id("Given")
    if k == "define":
        return "<ml:define>" + to_xml(node[1]) + to_xml(node[2]) + "</ml:define>"
    if k == "gdefine":
        return "<ml:globalDefine>" + to_xml(node[1]) + to_xml(node[2]) + "</ml:globalDefine>"
    if k == "eval":
        u = "<ml:unitOverride>" + to_xml(node[2]) + "</ml:unitOverride>" if node[2] is not None else ""
        return "<ml:eval>" + to_xml(node[1]) + u + "</ml:eval>"
    if k == "symeval":
        cmds = ""
        for parts in node[2]:
            inner = to_xml(parts[0]) if len(parts) == 1 else x_seq([to_xml(p) for p in parts])
            cmds += "<ml:command>" + inner + "</ml:command>"
        return ('<ml:symEval style="default" hide-keywords="false" hide-lhs="false">' + to_xml(node[1]) + cmds
                + "</ml:symEval>")
    if k == "expr":
        return to_xml(node[1])
    raise ValueError(node)


def parse_statement(src):
    return Parser(src).statement()


FORMAT_KINDS = {"gen": "general", "dec": "decimal", "sci": "scientific", "eng": "engineering"}


def result_format_xml(opts):
    """'@prec=2 zeros dec exp=6 table' -> <resultFormat> (per-region result display, Worksheet20.xsd)."""
    kind, prec, zeros, expo, mstyle = "general", None, False, None, "auto"
    for o in opts.split():
        k, _, v = o.partition("=")
        if k in FORMAT_KINDS:
            kind = FORMAT_KINDS[k]
        elif k == "prec":
            prec = int(v)
        elif k == "zeros":
            zeros = True
        elif k == "exp":
            expo = int(v)
        elif k in ("matrix", "table"):
            mstyle = k
        else:
            raise SyntaxError(f"unknown format option {o!r} (prec=N zeros gen|dec|sci|eng exp=N matrix|table)")
    a = f'precision="{3 if prec is None else prec}" show-trailing-zeros="{"true" if zeros else "false"}" ' \
        'radix="dec" complex-threshold="10"'
    if kind == "general":
        a += f' exponential-threshold="{3 if expo is None else expo}"'
    if kind == "scientific":
        a += ' use-e-notation="false"'
    return (f'<resultFormat><{kind} {a}/><matrix display-style="{mstyle}" expand-nested-arrays="false"/>'
            '<unit format-units="true" simplify-units="true"/></resultFormat>')


def math_region_xml(src):
    fmt = ""
    m = re.search(r"\s@(\w+(?:=\w+)?(?:\s+\w+(?:=\w+)?)*)\s*$", src)
    if m:                                 # "σ = MPa @prec=2 zeros" -> per-region number format
        fmt, src = result_format_xml(m.group(1)), src[:m.start()]
    node, disabled = parse_statement(src)
    return (f'<math optimize="false" disable-calc="{"true" if disabled else "false"}">'
            + statement_xml(node) + fmt + "</math>"), node


# ============================================================================ XML -> linear text
PREC = {"or": 10, "xor": 10, "and": 20, "equal": 30, "notEqual": 30, "lessThan": 30, "greaterThan": 30,
        "lessOrEqual": 30, "greaterOrEqual": 30, "plus": 40, "minus": 40, "mult": 50, "div": 50,
        "crossProduct": 50, "neg": 60, "not": 60, "pow": 70, "factorial": 80, "indexer": 90}
BIN_SYM = {"or": " or ", "xor": " xor ", "and": " and ", "equal": " == ", "notEqual": " != ", "lessThan": " < ",
           "greaterThan": " > ", "lessOrEqual": " <= ", "greaterOrEqual": " >= ", "plus": " + ", "minus": " - ",
           "mult": "*", "div": "/", "crossProduct": " × ", "pow": "^"}
UNARY_FN = {v[0]: k for k, v in SPECIAL_OPS.items()}
UNIT_ABBR = {"meter": "m", "kilogram": "kg", "gram": "g", "second": "s", "ampere": "A", "kelvin": "K",
             "mole": "mol", "candela": "cd", "radian": "rad", "steradian": "sr", "degree": "deg", "dollar": "$",
             "newton": "N", "pascal": "Pa", "joule": "J", "watt": "W", "volt": "V", "ohm": "Ω", "hertz": "Hz",
             "coulomb": "C", "farad": "F", "henry": "H", "tesla": "T", "weber": "Wb", "liter": "L", "minute": "min",
             "hour": "hr", "day": "day", "bar": "bar", "atmosphere": "atm", "tonne": "tonne", "inch": "in",
             "foot": "ft", "pound_force": "lbf", "pound": "lb", "kip": "kip", "ksi": "ksi", "psi": "psi"}
UNIT_PREFIX = {"kilo": "k", "mega": "M", "giga": "G", "milli": "m", "micro": "μ", "nano": "n", "centi": "c",
               "deci": "d", "hecto": "h", "tera": "T", "pico": "p"}


def unit_abbr(name):
    if name in UNIT_ABBR:
        return UNIT_ABBR[name]
    for p, s in UNIT_PREFIX.items():
        if name.startswith(p) and name[len(p):] in UNIT_ABBR:
            return s + UNIT_ABBR[name[len(p):]]
    return name
DERIVED = {  # base-SI exponent signature (kg, m, s, A, K) -> name
    (1, 1, -2, 0, 0): "N", (1, -1, -2, 0, 0): "Pa", (1, 2, -2, 0, 0): "J", (1, 2, -3, 0, 0): "W",
    (1, 2, -3, -1, 0): "V", (1, 2, -3, -2, 0): "Ω", (0, 0, 1, 1, 0): "C", (1, 0, -2, 0, 0): "N/m",
    (0, 1, -1, 0, 0): "m/s", (0, 1, -2, 0, 0): "m/s^2", (1, -3, 0, 0, 0): "kg/m^3", (0, 0, -1, 0, 0): "Hz",
    (1, 3, -2, 0, 0): "N·m^2", (1, 2, -2, 0, -1): "J/K",
}


def local(tag):
    return tag.rsplit("}", 1)[-1]


def ids_text(el):
    name = el.text or ""
    sub = el.get("subscript")
    return name + ("." + sub if sub else "")


def fmt_num(s):
    try:
        v = float(s)
    except ValueError:
        return s
    if v != v or v in (float("inf"), float("-inf")):  # NaN / inf (e.g. NaN placeholders in data files)
        return s
    if v == int(v) and abs(v) < 1e15:
        return str(int(v))
    return f"{v:.10g}"


def unit_text(mono):
    parts, sig = [], {}
    for ref in mono:
        unit = ref.get("unit", "?")
        num = int(ref.get("power-numerator", "1"))
        den = int(ref.get("power-denominator", "1"))
        sig[unit] = num / den
        p = "" if (num == 1 and den == 1) else ("^" + (str(num) if den == 1 else f"({num}/{den})"))
        parts.append(unit_abbr(unit) + p)
    key = tuple(int(sig.get(u, 0)) if float(sig.get(u, 0)).is_integer() else None
                for u in ("kilogram", "meter", "second", "ampere", "kelvin"))
    if set(sig) <= {"kilogram", "meter", "second", "ampere", "kelvin"} and key in DERIVED:
        return DERIVED[key]
    return "·".join(parts)


def result_text(res):
    kids = list(res)
    if not kids:
        return "?"
    return value_text(kids[0])


def value_text(el, raw=False):
    t = local(el.tag)
    if t == "real":
        return (el.text or "") if raw else fmt_num(el.text or "")
    if t == "unitedValue":
        kids = list(el)
        v = value_text(kids[0])
        mono = next((k for k in kids if local(k.tag) == "unitMonomial"), None)
        return v + (" " + unit_text(mono) if mono is not None and len(mono) else "")
    if t == "complex":
        re_, im_ = "0", "0"
        for k in el:
            if local(k.tag) == "real":
                re_ = fmt_num(k.text)
            elif local(k.tag) == "imag":
                im_ = fmt_num(k.text)
        return f"{re_}{'' if im_.startswith('-') else '+'}{im_}i" if re_ != "0" else f"{im_}i"
    if t == "matrix":
        rows, cols = int(el.get("rows")), int(el.get("cols"))
        vals = [value_text(k) for k in el]
        if rows * cols > 60:
            return f"[{rows}x{cols} matrix: " + ", ".join(vals[:8]) + ", ...]"
        grid = [[vals[c * rows + r] for c in range(cols)] for r in range(rows)]
        return "[" + "; ".join(", ".join(r) for r in grid) + "]"
    return lin(el)


PROVENANCE_META = {"originRef", "parentRef", "comment", "originComment", "contentHash", "hash"}


def unwrap(el):
    """<ml:provenance> (copy/paste origin tracking) wraps the real expression: return that expression."""
    while local(el.tag) == "provenance":
        # MC13 puts the bookkeeping in the provenance10 namespace, MC12 in math10 - skip it by name
        inner = [k for k in el if local(k.tag) not in PROVENANCE_META]
        if not inner:
            break
        el = inner[0]
    return el


def lin(el, parent_prec=0):
    """Math20 element -> linear text (inverse of the parser, best effort for anything Mathcad writes)."""
    el = unwrap(el)
    t = local(el.tag)
    kids = [unwrap(k) for k in el if local(k.tag) != "resultFormat"]
    if t == "real":
        return fmt_num(el.text or "") if el.get("base", "10") == "10" else (el.text or "")
    if t == "imag":
        return fmt_num(el.text or "") + el.get("symbol", "i")
    if t == "id":
        return ids_text(el)
    if t == "str":
        return '"' + (el.text or "") + '"'
    if t == "placeholder":
        return "■"
    if t == "parens":
        return "(" + lin(kids[0]) + ")"
    if t == "sequence":
        return ", ".join(lin(k) for k in kids)
    if t == "matrix":
        rows, cols = int(el.get("rows")), int(el.get("cols"))
        vals = [lin(k) for k in kids]
        grid = [[vals[c * rows + r] for c in range(cols)] for r in range(rows)]
        return "[" + "; ".join(", ".join(r) for r in grid) + "]"
    if t == "range":
        a = kids[0]
        if local(a.tag) == "sequence":
            s = lin(a)
        else:
            s = lin(a)
        return s + ".." + lin(kids[1])
    if t == "define":
        return lin(kids[0]) + " := " + lin(kids[1])
    if t == "globalDefine":
        return lin(kids[0]) + " :== " + lin(kids[1])
    if t == "localDefine":
        return lin(kids[0]) + " <- " + lin(kids[1])
    if t == "function":
        fn = kids[0]
        bv = next((k for k in kids if local(k.tag) == "boundVars"), None)
        return lin(fn) + "(" + ", ".join(lin(v) for v in bv) + ")"
    if t == "eval":
        s = lin(kids[0]) + " ="
        for k in kids[1:]:
            if local(k.tag) == "unitOverride":
                s += " " + lin(list(k)[0])
        return s
    if t == "symEval":
        s = lin(kids[0]) + " ->"
        cmds = [k for k in kids if local(k.tag) == "command"]
        if cmds:
            s += " " + " | ".join(lin(list(c)[0]) for c in cmds)
        res = next((k for k in kids if local(k.tag) == "symResult"), None)
        if res is not None and len(res):
            r0 = list(res)[0]
            s += "   ⇒ " + (value_text(r0, raw=True) if local(r0.tag) == "real" else lin(r0))
        return s
    if t == "program":
        return "prog { " + "; ".join(lin(k) for k in kids) + " }"
    if t == "ifThen":
        return "if " + lin(kids[0]) + ": " + lin(kids[1])
    if t == "otherwise":
        return "else: " + lin(kids[0])
    if t == "for":
        return "for " + lin(kids[0]) + " in " + lin(kids[1]) + ": " + lin(kids[2])
    if t == "while":
        return "while " + lin(kids[0]) + ": " + lin(kids[1])
    if t == "return":
        return "return " + lin(kids[0])
    if t in ("break", "continue"):
        return t
    if t == "tryCatch":
        return "try { " + lin(kids[0]) + " } catch { " + lin(kids[1]) + " }"
    if t == "lambda":
        return lin(kids[-1])
    if t == "mixed":
        w, nn, d = (lin(list(k)[0]) for k in kids)
        return f"{w} {nn}/{d}"
    if t == "apply":
        return lin_apply(el, kids, parent_prec)
    if t in ("result", "symResult", "unitedValue", "complex"):
        return value_text(el)
    return f"<{t}>"


def lin_apply(el, kids, parent_prec):
    op = kids[0]
    ot = local(op.tag)
    args = kids[1:]
    if ot in BIN_SYM and len(args) == 2:
        p = PREC[ot]
        right_p = p if ot == "pow" else p + 1
        left_p = p + 1 if ot == "pow" else p
        a1 = args[1]
        if ot in ("plus", "mult") and local(a1.tag) == "apply" and local(list(a1)[0].tag) == ot:
            right_p = p  # associative: a + (b + c) printed without parentheses
        s = lin(args[0], left_p) + BIN_SYM[ot] + lin(a1, right_p)
        return f"({s})" if p < parent_prec else s
    if ot in ("plus", "mult", "and", "or") and len(args) > 2:
        s = BIN_SYM[ot].join(lin(a, PREC[ot] + 1) for a in args)
        return f"({s})" if PREC[ot] < parent_prec else s
    if ot == "neg":
        s = "-" + lin(args[0], 60)
        return f"({s})" if 60 < parent_prec else s
    if ot == "factorial":
        return lin(args[0], 80) + "!"
    if ot == "indexer":
        idx = args[1]
        inner = lin(idx)
        return lin(args[0], 90) + "[" + inner + "]"
    if ot in ("summation", "product", "integral", "derivative"):
        lam = args[0]
        lk = list(lam)
        var = lin(list(lk[0])[0]) if local(lk[0].tag) == "boundVars" else "?"
        body = lin(lk[-1])
        name = {"summation": "sum", "product": "prod", "integral": "int", "derivative": "diff"}[ot]
        extra = ""
        for a in args[1:]:
            if local(a.tag) == "bounds":
                b = list(a)
                extra += ", " + lin(b[0]) + ", " + lin(b[1])
            elif local(a.tag) == "degree":
                extra += ", " + lin(list(a)[0])
        return f"{name}({body}, {var}{extra})"
    if ot == "limit":
        lk = list(args[0])
        var = lin(list(lk[0])[0])
        d = op.get("direction")
        return f"lim({lin(lk[-1])}, {var}, {lin(args[1])}" + (f', "{d}"' if d else "") + ")"
    if ot in UNARY_FN:
        return UNARY_FN[ot] + "(" + ", ".join(lin(a) for a in args) + ")"
    if ot in SOLVER_OPS:
        return ot + "(" + ", ".join(lin(a) for a in args) + ")"
    if ot == "id":
        # postfix/infix display forms (-10 °F, 2 ∠ 30) are printed as plain calls so they parse back;
        # Mathcad evaluates them the same way (only the display style attribute 'fixity' is lost)
        return ids_text(op) + "(" + ", ".join(lin(a) for a in args) + ")"
    if ot in ("apply", "parens", "function"):
        return lin(op, 90) + "(" + ", ".join(lin(a) for a in args) + ")"
    return f"{ot}(" + ", ".join(lin(a) for a in args) + ")"


# ============================================================================ plots (binary blobs)
# A plot region is <plot item-idref="N"/>; the plot itself is an MFC-serialized, gzip+base64 blob in
# <binaryContent>. Identifiers inside its expression tree are stored as [len+1][len]name\0 (numbers as
# [len+1][1][len]digits\0), so a template can be retargeted by renaming identifiers of any length.
PLOT_ID_RE = re.compile(rb"\x02\x0f\x00\x00..\x00\x00", re.S)


def _plot_name(name):
    b = name.encode("ascii")  # plot trees are single-byte; keep plot variable names ASCII
    if not 0 < len(b) < 250:
        raise ValueError(name)
    return bytes([len(b) + 1, len(b)]) + b + b"\x00"


PLOT_OPTIONS = {"points", "logx", "logy", "loglog"}


def rename_plot_ids(data, mapping):
    """Rename identifiers of a plot tree (one pass, so swapping names is safe)."""
    out, pos = bytearray(), 0
    for m in PLOT_ID_RE.finditer(data):
        j = m.end()
        if j + 2 >= len(data) or data[j] != data[j + 1] + 1 or data[j + 2] == 1:
            continue
        n = data[j + 1]
        name = data[j + 2:j + 2 + n].decode("latin1")
        if data[j + 2 + n] == 0 and name in mapping:
            out += data[pos:j] + _plot_name(mapping[name])
            pos = j + 2 + n + 1
    return bytes(out + data[pos:])


def set_log_axes(data, logx, logy):
    """axisFormat: flag byte of the x axis sits 10 bytes after the tag, the y axis 22 bytes later;
    bit 0x01 = logarithmic scale (found by diffing qsheet feat_04b plots #27 and #29)."""
    p = data.find(b"axisFormat") + len(b"axisFormat") + 10
    if p < 10 or data[p + 21:p + 22] != b"*":
        raise SyntaxError("@plot: unexpected axis format in template")
    d = bytearray(data)
    if logx:
        d[p] |= 1
    if logy:
        d[p + 22] |= 1
    return bytes(d)


def plot_blob(spec):
    """'Y vs X', 'f(x) vs x', 'f(t), g(t) vs t', 'Yd, fit(z) vs Xd, z' [+ points/logx/logy/loglog]."""
    words = spec.split()
    opts = set()
    while words and words[-1].lower() in PLOT_OPTIONS:
        opts.add(words.pop().lower())
    parts = re.split(r"\s+vs\s+", " ".join(words), maxsplit=1)
    if len(parts) != 2:
        raise SyntaxError("@plot: expected '<y expressions> vs <x expressions>'")
    ys, xs = (Parser(f"q({p})").expr()[2] for p in parts)

    def ident(e):
        return e[1] if e[0] == "id" and not e[2] else None

    def fcall(e):  # f(v) with plain identifiers -> (f, v)
        if e[0] == "call" and ident(e[1]) and len(e[2]) == 1 and ident(e[2][0]):
            return ident(e[1]), ident(e[2][0])
        return None

    kind, names = None, None
    if len(ys) == 1 and len(xs) == 1 and ident(ys[0]) and ident(xs[0]):
        kind = "pts" if "points" in opts else "xy"
        names = [ident(ys[0]), ident(xs[0])]
    elif len(ys) == 1 and len(xs) == 1 and fcall(ys[0]) and fcall(ys[0])[1] == ident(xs[0]):
        kind, (f, v) = "fx", fcall(ys[0])
        names = [f, v, v]
    elif len(ys) == 2 and len(xs) == 1 and fcall(ys[0]) and fcall(ys[1]) \
            and fcall(ys[0])[1] == fcall(ys[1])[1] == ident(xs[0]):
        kind, v = "2fx", ident(xs[0])
        names = [fcall(ys[0])[0], v, fcall(ys[1])[0], v, v]
    elif len(ys) == 2 and len(xs) == 2 and ident(ys[0]) and fcall(ys[1]) and ident(xs[0]) \
            and ident(xs[1]) == fcall(ys[1])[1]:
        kind = "datafit"
        names = [ident(ys[0]), fcall(ys[1])[0], ident(xs[1]), ident(xs[0]), ident(xs[1])]
    if kind is None:
        raise SyntaxError("@plot supports 'Y vs X', 'f(x) vs x', 'f(t), g(t) vs t', 'Yd, fit(z) vs Xd, z' "
                          "- define helper vectors/functions first")
    fname, tnames = PLOT_TEMPLATES[kind]
    data = open(os.path.join(PLOT_DIR, fname), "rb").read()
    mapping = {}
    for old, new in zip(tnames, names):
        if mapping.get(old, new) != new:
            raise SyntaxError(f"@plot: '{old}' of template {kind} mapped to both {mapping[old]} and {new}")
        mapping[old] = new
    try:
        data = rename_plot_ids(data, mapping)
    except UnicodeEncodeError:
        raise SyntaxError("@plot: variable names used in plots must be ASCII (no Greek/Cyrillic)")
    if plot_ids(data) != names:
        raise SyntaxError(f"@plot: renaming failed ({plot_ids(data)} != {names})")
    return set_log_axes(data, bool(opts & {"logx", "loglog"}), bool(opts & {"logy", "loglog"}))


def plot_ids(data):
    names = []
    for m in PLOT_ID_RE.finditer(data):
        j = m.end()
        if j + 2 < len(data) and data[j] == data[j + 1] + 1 and data[j + 2] != 1:
            s = data[j + 2:j + 2 + data[j + 1]].decode("latin1")
            if s != "_n_u_l_l_":
                names.append(s)
    return names


def binary_items(root):
    bc = next((k for k in root if local(k.tag) == "binaryContent"), None)
    return {} if bc is None else {it.get("item-id"): it for it in bc}


def item_bytes(item):
    raw = base64.b64decode("".join((item.text or "").split()))
    return gzip.decompress(raw) if item.get("content-encoding") == "gzip" else raw


# ============================================================================ worksheet read
def text_of(el):
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def iter_regions(parent):
    for reg in parent:
        if local(reg.tag) != "region":
            continue
        yield reg
        area = next((k for k in reg if local(k.tag) == "area"), None)
        if area is not None:
            yield from iter_regions(area)


def load(path):
    tree = ET.parse(path)
    root = tree.getroot()
    return tree, root


def cmd_read(a):
    tree, root = load(a.file)
    ns = root.tag[1:].split("}")[0]
    regions = next((k for k in root if local(k.tag) == "regions"), None)
    if ns not in (WS, WS10):
        newer = re.search(r"worksheet(\d)0$", ns)
        if newer and int(newer.group(1)) >= 3:
            print(f"NOTE: {ns} = Mathcad 14/15 worksheet. Mathcad 13 cannot open or recalculate it; "
                  "formulas and saved results below are read directly from the XML.")
        else:
            print(f"unknown namespace {ns}")
    if regions is None:
        print("no regions")
        return
    items = binary_items(root)
    meta = next((k for k in root if local(k.tag) == "metadata"), None)
    if meta is not None:
        gen = meta.find(f"{{{ns}}}generator")
        title = meta.find(f"{{{ns}}}userData/{{{ns}}}title")
        print(f"# {os.path.basename(a.file)}  generator={gen.text if gen is not None else '?'}"
              f"  title={title.text if title is not None and title.text else ''}")
    for n, reg in enumerate(iter_regions(regions)):
        kids = [k for k in reg if local(k.tag) not in ("rendering",)]
        kind = local(kids[0].tag) if kids else "?"
        pos = f"({float(reg.get('left', 0)):.0f},{float(reg.get('top', 0)):.0f})"
        tag = f" tag={reg.get('tag')}" if reg.get("tag") else ""
        if kind == "math":
            math = kids[0]
            content = [unwrap(k) for k in math if local(k.tag) != "resultFormat"]
            if not content:
                continue
            top = content[0]
            try:
                s = lin(top)
            except Exception as e:  # never die on exotic content
                s = f"<unparsed {local(top.tag)}: {e}>"
            if local(top.tag) == "eval" and not a.nores:
                res = next((k for k in top if local(k.tag) == "result"), None)
                u = next((k for k in top if local(k.tag) == "unitOverride"), None)
                if res is not None:
                    if u is not None:  # result is stored in the override unit: "M = 10.5 kN*m"
                        rv = list(res)[0] if len(res) else None
                        num = value_text(list(rv)[0]) if rv is not None and local(rv.tag) == "unitedValue" else result_text(res)
                        s = lin(list(top)[0]) + " = " + num + " " + lin(list(u)[0])
                    else:
                        s += " " + result_text(res)
            off = " [disabled]" if math.get("disable-calc") == "true" else ""
            print(f"{n:3d} {pos:>12} math{tag}{off}  {s}")
            if a.xml:
                print("        " + ET.tostring(top, encoding="unicode")[:2000])
        elif kind == "text":
            print(f"{n:3d} {pos:>12} text{tag}  {text_of(kids[0])}")
        elif kind == "area":
            ar = kids[0]
            print(f"{n:3d} {pos:>12} area '{ar.get('name', '')}' collapsed={ar.get('is-collapsed')} locked={ar.get('is-locked')}")
        elif kind == "plot":
            ids = ""
            it = items.get(kids[0].get("item-idref"))
            if it is not None:
                try:
                    ids = "  ids: " + ", ".join(plot_ids(item_bytes(it)))
                except Exception:
                    pass
            print(f"{n:3d} {pos:>12} plot{tag} {float(reg.get('width', 0)):.0f}x{float(reg.get('height', 0)):.0f}{ids}")
        else:
            extra = " ".join(f"{k}={v}" for k, v in kids[0].attrib.items())[:120] if kids else ""
            print(f"{n:3d} {pos:>12} {kind}  {extra}")


# ============================================================================ worksheet build
REGION_ATTRS = ('show-border="false" show-highlight="false" is-protected="true" z-order="0" '
                'background-color="inherit"')


def est_height(n):
    """Rough height (pt) of a statement AST; relayout fixes it after Mathcad saved real sizes."""
    def h(x):
        if not isinstance(x, tuple):
            return 14
        k = x[0]
        if k == "op":
            if x[1] == "div":
                return h(x[2][0]) + h(x[2][1]) + 3
            if x[1] == "pow":
                return h(x[2][0]) + 5
            return max((h(a) for a in x[2]), default=14)
        if k == "matrix":
            return x[1] * 15 + 6
        if k in ("bigop", "limit"):
            return max(30, h(x[3]) + 10) if k == "bigop" else 30
        if k == "prog":
            return sum(stmt_h(s) for s in x[1]) + 4
        if k in ("call", "solver"):
            return max([14] + [h(a) for a in x[2]])
        if k == "parens":
            return h(x[1]) + 2
        if k == "range":
            return 14
        return 14

    def stmt_h(s):
        if s[0] in ("if", "for", "while", "else"):
            return sum(stmt_h(b) for b in s[-1]) + (0 if len(s[-1]) == 1 else 4)
        if s[0] == "try":
            return sum(stmt_h(b) for b in s[1]) + sum(stmt_h(b) for b in s[2])
        return max(16, h(s[-1]) + 2) if len(s) > 1 else 16

    k = n[0]
    if k in ("define", "gdefine"):
        return max(18, h(n[1]), h(n[2]) + 4)
    if k in ("eval", "symeval", "expr"):
        return max(18, h(n[1]) + 4)
    return 18


def text_markup(text):
    """**bold**  *italic*  _{sub}  ^{sup}  -> Mathcad text inline elements <b> <i> <sub> <sup>."""
    s = esc(text)
    s = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)
    s = re.sub(r"(?<![\w*])\*(?=\S)(.+?)(?<=\S)\*(?![\w*])", r"<i>\1</i>", s)
    s = re.sub(r"_\{(.+?)\}", r"<sub>\1</sub>", s)
    s = re.sub(r"\^\{(.+?)\}", r"<sup>\1</sup>", s)
    return s


def text_region_body(text, style="Normal"):
    return ('<text use-page-width="false" push-down="false" lock-width="false">'
            f'<p style="{style}" margin-left="inherit" margin-right="inherit" text-indent="inherit" '
            f'text-align="inherit" list-style-type="inherit" tabs="inherit">{text_markup(text)}</p></text>')


def split_comment(line):
    """'x := 2 // comment' -> ('x := 2', 'comment') ignoring '//' inside strings."""
    in_str = False
    for i, ch in enumerate(line):
        if ch == '"':
            in_str = not in_str
        if not in_str and line.startswith("//", i):
            return line[:i].rstrip(), line[i + 2:].strip()
    return line, None


def read_spec(path):
    """Yield logical lines; a line with unbalanced '{' continues until braces balance."""
    with open(path, encoding="utf-8-sig") as fh:
        lines = fh.read().splitlines()
    buf, depth = [], 0
    for raw in lines:
        if depth == 0 and not buf:
            if not raw.strip():
                yield ""
                continue
            if raw.lstrip().startswith(("#", ">")):
                yield raw.strip()
                continue
        code, _ = split_comment(raw)
        depth += code.count("{") - code.count("}")
        buf.append(raw)
        if depth <= 0:
            yield "\n".join(buf)
            buf, depth = [], 0
    if buf:
        raise SyntaxError("unbalanced braces at end of spec:\n" + "\n".join(buf))


def new_ids():
    return str(uuid.uuid4()), str(uuid.uuid4())


def cmd_build(a):
    tpl = open(TEMPLATE, encoding="utf-8-sig").read()
    doc_id, ver_id = new_ids()
    tpl = tpl.replace("{DOCUMENT_ID}", doc_id).replace("{VERSION_ID}", ver_id)
    if a.letter:
        tpl = re.sub(r'paper-code="\d+"', 'paper-code="1"', tpl)
        tpl = re.sub(r'page-width="[^"]+" page-height="[^"]+"', 'page-width="612" page-height="792"', tpl)
    title = a.title or os.path.splitext(os.path.basename(a.out))[0]
    tpl = tpl.replace("<title/>", f"<title>{esc(title)}</title>")
    left, comment_left, y, gap = 12.0, float(a.comment_x), 12.0, 8.0
    regions, rid, errors, blobs = [], 0, 0, []
    for line in read_spec(a.spec):
        if line == "":
            y += 10
            continue
        rid += 1
        if line.startswith("@plot"):
            code, comment = split_comment(line[5:])
            try:
                blobs.append(plot_blob(code.strip()))
                body = f'<plot disable-calc="false" item-idref="{len(blobs)}"/>'
                regions.append(region_xml(rid, left, y, 220, 215, body))
                y += 215 + gap
                if comment:  # caption under the plot ("Рисунок 1 - ...")
                    rid += 1
                    regions.append(region_xml(rid, left, y, 300, 14, text_region_body(comment)))
                    y += 14 + gap
            except (SyntaxError, ValueError) as e:
                errors += 1
                print(f"SYNTAX ERROR: {e}", file=sys.stderr)
            continue
        if line.strip() == "---":  # page break
            regions.append(region_xml(rid, 0, y, 450, 4, "<pageBreak/>"))
            y += 12
            continue
        if line.startswith("#"):
            level = len(line) - len(line.lstrip("#"))
            style = {1: "Heading 1", 2: "Heading 2"}.get(level, "Heading 3")
            body, h = text_region_body(line.lstrip("#").strip(), style), 22 if level == 1 else 18
            regions.append(region_xml(rid, left, y, 450, h, body))
            y += h + gap
            continue
        if line.startswith(">"):
            txt = line[1:].strip()
            h = 14 * (1 + len(txt) // 90)
            regions.append(region_xml(rid, left, y, 450, h, text_region_body(txt)))
            y += h + gap
            continue
        code, comment = split_comment(line)
        code = code.strip()
        try:
            body, node = math_region_xml(code)
            h = est_height(node)
        except SyntaxError as e:
            errors += 1
            print(f"SYNTAX ERROR: {e}", file=sys.stderr)
            body, h = text_region_body("SYNTAX ERROR: " + code), 14
        regions.append(region_xml(rid, left, y, 150, h, body))
        if comment:
            rid += 1
            regions.append(region_xml(rid, comment_left, y + max(0, h / 2 - 7), 250, 14, text_region_body(comment)))
        y += h + gap
    out = tpl.replace("<regions/>", "<regions>\n" + "\n".join(regions) + "\n</regions>")
    if blobs:
        items = "".join(f'<item item-id="{i}" content-encoding="gzip">{base64.b64encode(gzip.compress(b)).decode()}</item>'
                        for i, b in enumerate(blobs, 1))
        out = out.replace("</worksheet>", f"<binaryContent>{items}</binaryContent>\n</worksheet>")
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(out)
    print(f"wrote {a.out}: {len(regions)} regions" + (f", {errors} syntax error(s)" if errors else ""))
    if errors:
        sys.exit(2)


def region_xml(rid, left, top, width, height, body):
    return (f'<region region-id="{rid}" left="{left:g}" top="{top:g}" width="{width:g}" height="{height:g}" '
            f'align-x="{left:g}" align-y="{top + height * 0.7:g}" {REGION_ATTRS} tag="">{body}</region>')


# ============================================================================ relayout / set
def strip_digest(text):
    return re.sub(r"<\?validation-md5-digest[^?]*\?>\s*", "", text)


def cmd_relayout(a):
    tree, root = load(a.inp)
    regions = next(k for k in root if local(k.tag) == "regions")
    regs = [r for r in regions if local(r.tag) == "region"]
    # Mathcad evaluates in order of the alignment point (align-y, then align-x), not of the top edge:
    # a tall result (matrix) starts above the definition written just before it. Sort by that key.
    regs.sort(key=lambda r: (float(r.get("align-y", r.get("top"))), float(r.get("align-x", r.get("left")))))
    # Cascade like Mathcad's "Separate Regions": when a region must move down, everything after it
    # (including its comment in the right column) moves by the same offset, so the evaluation order
    # and row alignment are preserved.
    placed, moved, offset, fixed = [], 0, 0.0, 0
    for r in regs:
        top, left = float(r.get("top")), float(r.get("left"))
        w, h = float(r.get("width")), float(r.get("height"))
        new_top = top + offset
        for (pt, pl, pw, ph) in placed:
            # 2 pt tolerance: Mathcad snaps positions to its grid on load, which creates harmless slivers
            if pl < left + w and left < pl + pw and pt < new_top + h - 2 and new_top < pt + ph - 2:
                extra = pt + ph + a.gap - new_top
                offset += extra
                new_top += extra
                fixed += 1
        if new_top != top:
            r.set("top", f"{new_top:g}")
            if r.get("align-y"):
                r.set("align-y", f"{float(r.get('align-y')) + new_top - top:g}")
            moved += 1
        placed.append((new_top, left, w, h))
    data = ET.tostring(root, encoding="unicode")
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + data)
    print(f"relayout: {fixed} overlap(s) fixed, {moved} of {len(regs)} region(s) shifted -> {a.out}")


def cmd_set(a):
    text = strip_digest(open(a.inp, encoding="utf-8").read())
    root = ET.fromstring(text.encode("utf-8"))
    changed = []
    for assign in a.assign:
        name, _, expr = assign.partition("=")
        name = name.strip()
        node = Parser(expr).range_or_expr()
        new_el = ET.fromstring(f'<root xmlns:ml="{ML}">' + to_xml(node) + "</root>")[0]
        hit = False
        for d in root.iter(f"{{{ML}}}define"):
            kids = list(d)
            lhs = kids[0]
            lname = ids_text(lhs) if local(lhs.tag) == "id" else (
                ids_text(list(lhs)[0]) if local(lhs.tag) == "function" else None)
            if lname == name:
                d.remove(kids[1])
                d.insert(1, new_el)
                hit = True
                break
        changed.append(f"{name}: {'ok' if hit else 'NOT FOUND'}")
    data = ET.tostring(root, encoding="unicode")
    with open(a.out, "w", encoding="utf-8", newline="\n") as fh:
        fh.write('<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n' + data)
    print("; ".join(changed) + f" -> {a.out} (recalculate with mc.ps1 to refresh results)")
    if any("NOT FOUND" in c for c in changed):
        sys.exit(2)


def cmd_expr(a):
    body, node = math_region_xml(a.statement)
    if a.inner:  # form accepted by Region.MathInterface.XML: top element with the ml namespace declared
        inner = re.sub(r"^<math[^>]*>|</math>$", "", body)
        print(re.sub(r"^<ml:(\w+)", lambda m: f'<ml:{m.group(1)} xmlns:ml="{ML}"', inner, count=1))
        return
    print(body)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("read"); p.add_argument("file"); p.add_argument("--xml", action="store_true")
    p.add_argument("--nores", action="store_true"); p.set_defaults(fn=cmd_read)
    p = sub.add_parser("build"); p.add_argument("spec"); p.add_argument("out")
    p.add_argument("--letter", action="store_true", help="US Letter instead of A4")
    p.add_argument("--title", default=""); p.add_argument("--comment-x", default="260")
    p.set_defaults(fn=cmd_build)
    p = sub.add_parser("relayout"); p.add_argument("inp"); p.add_argument("out")
    p.add_argument("--gap", type=float, default=6.0); p.set_defaults(fn=cmd_relayout)
    p = sub.add_parser("set"); p.add_argument("inp"); p.add_argument("out"); p.add_argument("assign", nargs="+")
    p.set_defaults(fn=cmd_set)
    p = sub.add_parser("expr"); p.add_argument("statement"); p.add_argument("--inner", action="store_true")
    p.set_defaults(fn=cmd_expr)
    a = ap.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
