"""Build a Mathcad 13 worksheet from the xmcd.py line syntax + generated plots, recalc it, export plot images.

spec: list of xmcd.py spec lines; a line '@PLOT name' marks where plot `name` goes.
plots: {name: dict(ys=[...], xs=[...], traces=[...], ylim=(lo,hi), xlim=(lo,hi), size=(w,h), logx, logy, grid)}
"""
import json
import os
import re
import shutil
import subprocess
import sys

from lxml import etree

SKILL = os.path.dirname(os.path.abspath(__file__))  # папка scripts скилла, где бы он ни лежал
sys.path.insert(0, SKILL)
import xmcd  # noqa: E402

import mcplot  # noqa: E402

MC = os.path.join(SKILL, "mc.ps1")
WS = "{http://schemas.mathsoft.com/worksheet20}"


def mc(args, timeout=240):
    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", MC] + args
    p = subprocess.run(cmd, capture_output=True, timeout=timeout)
    out = p.stdout.decode("utf-8", "replace")
    m = re.search(r"\{.*\}\s*$", out, re.S)
    if not m:
        raise RuntimeError("mc.ps1 failed: " + out[-2000:] + p.stderr.decode("utf-8", "replace")[-2000:])
    return json.loads(m.group(0))


def build(spec, plots, out_xmcd, title=None, font_size=None):
    """font_size: math font (Variables/Constants) size in pt; also sets the size of plot tick numbers."""
    lines, order = [], []
    for ln in spec:
        m = re.match(r"\s*@PLOT\s+(\S+)", ln)
        if m:
            order.append(m.group(1))
            lines.append("@plot f(x) vs x")
        else:
            lines.append(ln)
    tmp_spec = out_xmcd + ".spec.txt"
    with open(tmp_spec, "w", encoding="utf-8") as fh:
        fh.write("\n".join(lines) + "\n")
    cmd = [sys.executable, os.path.join(SKILL, "xmcd.py"), "build", tmp_spec, out_xmcd]
    if title:
        cmd += ["--title", title]
    p = subprocess.run(cmd, capture_output=True)
    if p.returncode != 0:
        raise RuntimeError(p.stdout.decode("utf-8", "replace") + p.stderr.decode("utf-8", "replace"))
    tree = etree.parse(out_xmcd)
    root = tree.getroot()
    items = xmcd.binary_items(root)
    k = 0
    for reg in root.iter(WS + "region"):
        pl = reg.find(WS + "plot")
        if pl is None:
            continue
        spec_p = plots[order[k]]
        blob = mcplot.make_plot(**spec_p)
        items[pl.get("item-idref")].text = mcplot.encode(blob)
        w, h = spec_p.get("size", (80, 48))
        reg.set("width", "%.1f" % (w * 7.0 + 30))
        reg.set("height", "%.1f" % (h * 7.0 + 30))
        reg.set("tag", "plot_" + order[k])
        k += 1
    if font_size:
        for st in root.iter("{http://schemas.mathsoft.com/worksheet20}mathStyle"):
            if st.get("name") in ("Variables", "Constants"):
                st.set("font-size", str(font_size))
    tree.write(out_xmcd, xml_declaration=True, encoding="UTF-8")
    os.remove(tmp_spec)
    return out_xmcd


def recalc_layout(src, dst, passes=2):
    """Recalculate in Mathcad, then push overlapping regions apart (sizes known after saving)."""
    r = mc(["-Path", src, "-SaveAs", dst])
    for _ in range(passes):
        tmp = dst + ".tmp.xmcd"
        p = subprocess.run([sys.executable, os.path.join(SKILL, "xmcd.py"), "relayout", dst, tmp],
                           capture_output=True)
        msg = p.stdout.decode("utf-8", "replace")
        r = mc(["-Path", tmp, "-SaveAs", dst])
        os.remove(tmp)
        if "0 overlap" in msg:
            break
    return r


def export_plots(xmcd_path, outdir):
    """HTML export; return {plot_name: png_path} using region tags."""
    if os.path.isdir(outdir):
        shutil.rmtree(outdir)
    os.makedirs(outdir)
    htm = os.path.join(outdir, "export.htm")
    mc(["-Path", xmcd_path, "-SaveAs", htm])
    html = open(htm, encoding="utf-8", errors="replace").read()
    divs = re.findall(r"<div\s[^>]*>(.*?)</div>", html, re.S)
    root = etree.parse(xmcd_path).getroot()
    regs = [r for r in root.find(WS + "regions")]
    res = {}
    for reg, div in zip(regs, divs):
        tag = reg.get("tag") or ""
        if tag.startswith("plot_"):
            m = re.search(r'src="([^"]+)"', div)
            if m:
                res[tag[5:]] = os.path.normpath(os.path.join(outdir, m.group(1)))
    return res


def get_values(xmcd_path, names):
    r = mc(["-Path", xmcd_path, "-Get", ",".join(names)])
    return r.get("values", {}), r
