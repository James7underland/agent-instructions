#!/usr/bin/env python3
"""helpdoc.py — поиск и чтение руководства Symmetry (MadCap HTML5, 703 страницы) как текста.

  python helpdoc.py search "heat exchanger UA" [-n 15]   # ранжированный поиск (все слова), со сниппетами
  python helpdoc.py show "Unit Operations/Heater/Heater.htm"   # текст страницы (таблицы → строки с |)
  python helpdoc.py show Heater                          # по заголовку (точное или первое вхождение)
  python helpdoc.py toc [ПОДСТРОКА]                      # список страниц: путь | заголовок | раздел TOC
  python helpdoc.py index OUT.md                         # сгенерировать индекс для references/help/
  python helpdoc.py dump OUT_DIR PATH...                 # сохранить тексты страниц в .md
Корень: C:\\Program Files\\VMG\\Symmetry\\Documentation\\Symmetry User Manual HTML5 (или env SYM_HELP).
"""
from __future__ import annotations

import html
import os
import re
import sys
from html.parser import HTMLParser

ROOT = os.environ.get("SYM_HELP", r"C:\Program Files\VMG\Symmetry\Documentation\Symmetry User Manual HTML5")
SKIP_DIRS = {"Skins", "Resources", "Data", "GeneratedImages"}


class _P(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out, self.skip, self.title, self.toc = [], 0, "", ""
        self.in_title = False
        self.cell = False

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "html":
            self.toc = a.get("data-mc-toc-path", "") or ""
        if tag in ("script", "style", "head") and tag != "head":
            self.skip += 1
        if tag == "title":
            self.in_title = True
        if tag in ("p", "div", "br", "li", "tr", "h1", "h2", "h3", "h4", "h5", "table"):
            self.out.append("\n")
        if tag in ("h1", "h2", "h3", "h4"):
            self.out.append("#" * int(tag[1]) + " ")
        if tag == "li":
            self.out.append("- ")
        if tag in ("td", "th"):
            self.out.append(" | ")
        if tag == "img" and a.get("alt"):
            self.out.append(f"[img: {a.get('alt')}]")

    def handle_endtag(self, tag):
        if tag in ("script", "style"):
            self.skip = max(0, self.skip - 1)
        if tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_title:
            self.title += data
            return
        if self.skip:
            return
        self.out.append(data)


def parse(path):
    p = _P()
    with open(path, encoding="utf-8", errors="replace") as f:
        p.feed(f.read())
    txt = "".join(p.out)
    txt = re.sub(r"[ \t\xa0]+", " ", txt)
    txt = re.sub(r"\n\s*\|", "\n|", txt)
    txt = re.sub(r"\n\s*\n+", "\n\n", txt).strip()
    return p.title.strip(), p.toc, txt


def pages():
    for d, dirs, files in os.walk(ROOT):
        dirs[:] = [x for x in dirs if x not in SKIP_DIRS]
        for f in files:
            if f.lower().endswith(".htm"):
                full = os.path.join(d, f)
                rel = os.path.relpath(full, ROOT).replace("\\", "/")
                if "/" not in rel and os.path.getsize(full) < 8000:
                    # корневые «тонкие» страницы-двойники — пропускаем, если есть настоящая в подпапке
                    continue
                yield rel, full


def find_page(q):
    cand = os.path.join(ROOT, q)
    if os.path.exists(cand):
        return q, cand
    ql = q.lower()
    best = None
    for rel, full in pages():
        base = os.path.splitext(os.path.basename(rel))[0].lower()
        if base == ql:
            return rel, full
        if best is None and ql in rel.lower():
            best = (rel, full)
    return best


def cmd_search(words, n=15):
    ws = [w.lower() for w in words]
    res = []
    for rel, full in pages():
        title, toc, txt = parse(full)
        low = (title + " " + txt).lower()
        if not all(w in low for w in ws):
            continue
        score = sum(low.count(w) for w in ws) + 20 * sum(w in title.lower() for w in ws)
        i = low.find(ws[0])
        snip = txt[max(0, i - 80): i + 160].replace("\n", " ") if i >= 0 else ""
        res.append((score, rel, title, snip))
    res.sort(reverse=True)
    for s, rel, title, snip in res[:n]:
        print(f"[{s}] {rel} — {title}\n      …{snip}…")
    print(f"# найдено страниц: {len(res)}")


def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    if len(sys.argv) < 2:
        print(__doc__); return
    c, args = sys.argv[1], sys.argv[2:]
    if c == "search":
        n = 15
        if "-n" in args:
            i = args.index("-n"); n = int(args[i + 1]); del args[i:i + 2]
        words = " ".join(args).split()
        cmd_search(words, n)
    elif c == "show":
        r = find_page(" ".join(args))
        if not r:
            sys.exit("страница не найдена")
        title, toc, txt = parse(r[1])
        print(f"# {title}\n({r[0]}; TOC: {toc})\n\n{txt}")
    elif c == "toc":
        q = " ".join(args).lower()
        for rel, full in sorted(pages()):
            title, toc, _ = parse(full)
            if q in (rel + title + toc).lower():
                print(f"{rel} | {title} | {toc}")
    elif c == "index":
        out = args[0]
        groups = {}
        for rel, full in sorted(pages()):
            title, toc, _ = parse(full)
            top = rel.split("/")[0] if "/" in rel else "(root)"
            groups.setdefault(top, []).append((rel, title))
        with open(out, "w", encoding="utf-8") as f:
            f.write("# Индекс руководства Symmetry 2023 (HTML5)\n\nКорень: `" + ROOT + "`. Читать: "
                    "`python scripts/helpdoc.py show \"<путь>\"`, искать: `helpdoc.py search слова`.\n")
            for g, items in groups.items():
                f.write(f"\n## {g} ({len(items)})\n")
                for rel, title in items:
                    f.write(f"- `{rel}` — {title}\n")
        print(f"index -> {out}")
    elif c == "dump":
        out = args[0]; os.makedirs(out, exist_ok=True)
        for q in args[1:]:
            r = find_page(q)
            if not r:
                print("нет:", q); continue
            title, toc, txt = parse(r[1])
            fn = os.path.join(out, re.sub(r"[^\w.-]+", "_", os.path.splitext(r[0])[0]) + ".md")
            with open(fn, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n(источник: {r[0]})\n\n{txt}\n")
            print(fn)
    else:
        print(__doc__)


if __name__ == "__main__":
    main()
