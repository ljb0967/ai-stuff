#!/usr/bin/env python3
"""교안 빌드: YAML 원고 → HTML (A4 고정 페이지).

  python harness/build.py                      # 전체 교안 → dist/book.html
  python harness/build.py --theme a --src design/candidates/sample.yaml --out design/candidates/A.html

PDF·PNG 출력과 레이아웃 검사는 harness/render.mjs 가 맡는다.
"""
from __future__ import annotations

import argparse
import html
import json
import math
import pathlib
import re
import sys

import jinja2
import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC = ROOT / "textbook" / "src"
TPL = ROOT / "textbook" / "templates"
ASSETS = ROOT / "textbook" / "assets"

BOOK_TITLE = "처음 배우는 AI 리터러시"

# ------------------------------------------------------------------ inline markup

_INLINE = [
    (re.compile(r"\*\*(.+?)\*\*"), r"<strong>\1</strong>"),
    (re.compile(r"==(.+?)=="), r"<mark>\1</mark>"),
    (re.compile(r"`(.+?)`"), r'<span class="kbd">\1</span>'),
    (re.compile(r"\[g\]"), '<span class="dot dot-g" aria-label="초록"></span>'),
    (re.compile(r"\[y\]"), '<span class="dot dot-y" aria-label="노랑"></span>'),
    (re.compile(r"\[r\]"), '<span class="dot dot-r" aria-label="빨강"></span>'),
    (re.compile(r"\(\(([^()]+?)\)\)"), r'<span class="blank">\1</span>'),  # 빈칸 ((   ))
]


def md_inline(text) -> str:
    if text is None:
        return ""
    s = html.escape(str(text).strip(), quote=False)
    for pat, rep in _INLINE:
        s = pat.sub(rep, s)
    return s.replace("\n", "<br>")


def md_block(text) -> str:
    """단락·글머리표(-)·번호 목록(1.)을 지원하는 작은 마크다운."""
    if text is None:
        return ""
    out, buf, mode = [], [], None

    def flush():
        nonlocal buf, mode
        if not buf:
            return
        if mode == "ul":
            out.append("<ul>" + "".join(f"<li>{md_inline(x)}</li>" for x in buf) + "</ul>")
        elif mode == "ol":
            out.append("<ol>" + "".join(f"<li>{md_inline(x)}</li>" for x in buf) + "</ol>")
        else:
            out.append(f"<p>{md_inline(' '.join(buf))}</p>")
        buf, mode = [], None

    for raw in str(text).strip().splitlines():
        line = raw.strip()
        if not line:
            flush()
            continue
        m_ul = re.match(r"^[-•]\s+(.*)", line)
        m_ol = re.match(r"^\d+[.)]\s+(.*)", line)
        kind = "ul" if m_ul else "ol" if m_ol else "p"
        if kind != mode:
            flush()
            mode = kind
        buf.append((m_ul or m_ol).group(1) if kind != "p" else line)
    flush()
    return "".join(out)


CIRCLED = "①②③④⑤⑥⑦⑧⑨⑩⑪⑫"

# ------------------------------------------------------------------ SVG figures


def svg_cycle(steps: list[dict], center: str = "", human: str | None = None) -> str:
    """에이전트 루프 같은 순환도. steps: [{title, desc}]"""
    n = len(steps)
    W, H, cx, cy, R = 560, 340, 280, 170, 118
    bw, bh = 150, 58
    parts = [f'<svg viewBox="0 0 {W} {H}" class="svg-fig" role="img">',
             '<defs><marker id="arr" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" '
             'orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" class="svg-arrowhead"/></marker></defs>']
    pts = []
    for i in range(n):
        ang = -math.pi / 2 + 2 * math.pi * i / n
        pts.append((cx + R * 1.55 * math.cos(ang), cy + R * math.sin(ang)))
    # 화살표(곡선)
    for i in range(n):
        (x1, y1), (x2, y2) = pts[i], pts[(i + 1) % n]
        a1 = math.atan2(y2 - cy, (x2 - cx) / 1.55)
        a0 = math.atan2(y1 - cy, (x1 - cx) / 1.55)
        if a1 <= a0:
            a1 += 2 * math.pi
        s = a0 + 0.42
        e = a1 - 0.42
        sx, sy = cx + R * 1.55 * math.cos(s), cy + R * math.sin(s)
        ex, ey = cx + R * 1.55 * math.cos(e), cy + R * math.sin(e)
        parts.append(f'<path d="M{sx:.1f},{sy:.1f} A{R*1.55:.1f},{R:.1f} 0 0 1 {ex:.1f},{ey:.1f}" '
                     f'class="svg-line" marker-end="url(#arr)"/>')
    for i, ((x, y), st) in enumerate(zip(pts, steps)):
        parts.append(f'<g class="svg-node"><rect x="{x-bw/2:.1f}" y="{y-bh/2:.1f}" width="{bw}" height="{bh}" rx="10"/>'
                     f'<text x="{x:.1f}" y="{y-6:.1f}" class="svg-t1">{CIRCLED[i]} {html.escape(st["title"])}</text>'
                     f'<text x="{x:.1f}" y="{y+15:.1f}" class="svg-t2">{html.escape(st.get("desc", ""))}</text></g>')
    if center:
        lines = center.split("\n")
        for j, ln in enumerate(lines):
            parts.append(f'<text x="{cx}" y="{cy + (j - (len(lines)-1)/2) * 20 + 6:.1f}" class="svg-center">{html.escape(ln)}</text>')
    if human:
        parts.append(f'<g class="svg-human"><rect x="{W-150}" y="{H-36}" width="146" height="30" rx="15"/>'
                     f'<text x="{W-77}" y="{H-16}" class="svg-t2">{html.escape(human)}</text></g>')
    parts.append("</svg>")
    return "".join(parts)


def svg_nested(rings: list[dict]) -> str:
    """포함 관계 동심 타원. rings: 바깥→안 [{label, desc}]"""
    n = len(rings)
    W, H = 560, 300
    parts = [f'<svg viewBox="0 0 {W} {H}" class="svg-fig" role="img">']
    for i, rg in enumerate(rings):
        rx = 270 - i * 58
        ry = 145 - i * 30
        cx = 280 + i * 40
        cy = 150 + i * 6
        parts.append(f'<ellipse cx="{cx}" cy="{cy}" rx="{rx}" ry="{ry}" class="svg-ring svg-ring-{i}"/>')
        ty = cy - ry + 26
        parts.append(f'<text x="{cx - rx + 18 + i*4}" y="{ty}" class="svg-ring-label" text-anchor="start">{html.escape(rg["label"])}</text>')
        if rg.get("desc"):
            parts.append(f'<text x="{cx - rx + 18 + i*4}" y="{ty + 19}" class="svg-t2" text-anchor="start">{html.escape(rg["desc"])}</text>')
    parts.append("</svg>")
    return "".join(parts)


def svg_hub(center: str, nodes: list[str], caption_center: str = "") -> str:
    """가운데 허브(예: MCP)와 주변 서비스들."""
    W, H, cx, cy = 560, 260, 280, 130
    n = len(nodes)
    parts = [f'<svg viewBox="0 0 {W} {H}" class="svg-fig" role="img">']
    pos = []
    for i in range(n):
        ang = math.pi + math.pi * (i + 0.5) / n if False else (2 * math.pi * i / n) - math.pi / 2
        pos.append((cx + 210 * math.cos(ang), cy + 100 * math.sin(ang)))
    for x, y in pos:
        parts.append(f'<line x1="{cx}" y1="{cy}" x2="{x:.1f}" y2="{y:.1f}" class="svg-line"/>')
    for (x, y), label in zip(pos, nodes):
        parts.append(f'<g class="svg-node"><rect x="{x-58:.1f}" y="{y-18:.1f}" width="116" height="36" rx="18"/>'
                     f'<text x="{x:.1f}" y="{y+6:.1f}" class="svg-t1">{html.escape(label)}</text></g>')
    parts.append(f'<g class="svg-hub"><rect x="{cx-70}" y="{cy-30}" width="140" height="60" rx="12"/>'
                 f'<text x="{cx}" y="{cy-2}" class="svg-t1 inv">{html.escape(center)}</text>'
                 f'<text x="{cx}" y="{cy+19}" class="svg-t2 inv">{html.escape(caption_center)}</text></g>')
    parts.append("</svg>")
    return "".join(parts)


SVG_FIGS = {"cycle", "nested", "hub"}


def render_svg(fig: dict) -> str:
    k = fig["kind"]
    if k == "cycle":
        return svg_cycle(fig["steps"], fig.get("center", ""), fig.get("human"))
    if k == "nested":
        return svg_nested(fig["rings"])
    if k == "hub":
        return svg_hub(fig["center"], fig["nodes"], fig.get("center_desc", ""))
    raise ValueError(k)


# ------------------------------------------------------------------ model


def norm_block(b) -> dict:
    """`- p: "..."` 같은 한 키짜리 매핑을 {type: p, ...} 로 바꾼다."""
    if isinstance(b, str):
        return {"type": "p", "text": b}
    if "type" in b:
        return b
    (k, v), = b.items()
    if isinstance(v, dict):
        return {"type": k, **v}
    if isinstance(v, list):
        return {"type": k, "items": v}
    return {"type": k, "text": v}


class _Loader(yaml.SafeLoader):
    """YAML 1.1의 yes/no/on/off → bool 변환을 끈다 (`no: 1` 키가 False가 되는 문제 방지)."""


_Loader.yaml_implicit_resolvers = {
    k: [(tag, rx) for tag, rx in v if tag != "tag:yaml.org,2002:bool"]
    for k, v in yaml.SafeLoader.yaml_implicit_resolvers.items()
}
_Loader.add_implicit_resolver("tag:yaml.org,2002:bool", re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
                              list("tTfF"))


def load_doc(path: pathlib.Path) -> dict:
    return yaml.load(path.read_text(encoding="utf-8"), Loader=_Loader)


class Book:
    def __init__(self, docs: list[dict], theme: str):
        self.docs = docs
        self.theme = theme
        self.pages: list[dict] = []
        self.answers: list[dict] = []
        self.toc: list[dict] = []
        self.glossary: list[dict] = []
        self.fig_counts: dict[str, int] = {}

    def paginate(self):
        for doc in self.docs:
            unit = doc.get("unit")
            for pg in doc.get("pages", []):
                pg = dict(pg)
                pg["doc"] = doc
                pg["blocks"] = [norm_block(b) for b in pg.get("blocks", [])]
                pg["side"] = [norm_block(b) for b in pg.get("side", [])]
                self.pages.append(pg)
                if pg.get("type") == "opener" and unit:
                    self.toc.append({"unit": unit, "title": doc["title"], "part": doc.get("part"),
                                     "part_title": doc.get("part_title"), "page": len(self.pages)})
                if pg.get("type") == "divider":
                    self.toc.append({"divider": True, "title": pg.get("title"), "page": len(self.pages)})
                for b in pg["blocks"]:
                    if b["type"] == "exercises":
                        for it in b["items"]:
                            self.answers.append({"unit": unit, "no": it.get("no"), "answer": it.get("answer"),
                                                 "explain": it.get("explain"), "kind": "확인 문제"})
                    if b["type"] == "similar":
                        self.answers.append({"unit": unit, "no": b.get("no"), "answer": b.get("answer"),
                                             "explain": b.get("explain"), "kind": "유제"})
            self.glossary += doc.get("glossary", [])
        for i, pg in enumerate(self.pages, 1):
            pg["no"] = i


class Env(jinja2.Environment):
    """YAML 원고의 키(items, keys 등)가 dict 메서드보다 먼저 보이도록 한다."""

    def getattr(self, obj, attribute):
        if isinstance(obj, dict) and attribute in obj:
            return obj[attribute]
        return super().getattr(obj, attribute)


def make_env() -> jinja2.Environment:
    env = Env(loader=jinja2.FileSystemLoader(str(TPL)), autoescape=False,
              trim_blocks=True, lstrip_blocks=True)
    env.filters["md"] = md_inline
    env.filters["mdb"] = md_block
    env.filters["svg"] = render_svg
    env.globals["CIRCLED"] = CIRCLED
    env.globals["BOOK_TITLE"] = BOOK_TITLE
    env.globals["SVG_FIGS"] = SVG_FIGS
    return env


def build(src_files: list[pathlib.Path], out: pathlib.Path, theme: str) -> dict:
    docs = [load_doc(p) for p in src_files]
    book = Book(docs, theme)
    book.paginate()
    env = make_env()
    css_rel = pathlib.Path(*[".."] * len(out.parent.relative_to(ROOT).parts)) / "textbook" / "assets" / "css"
    html_out = env.get_template("book.html.j2").render(
        book=book, pages=book.pages, theme=theme, css=css_rel.as_posix(),
        fonts=(css_rel.parent / "fonts").as_posix())
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_out, encoding="utf-8")
    meta = {"pages": len(book.pages), "answers": len(book.answers), "toc": book.toc,
            "page_index": [{"no": p["no"], "type": p.get("type"), "unit": p["doc"].get("unit"),
                            "title": p.get("title") or p["doc"].get("title")} for p in book.pages]}
    out.with_suffix(".meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    return meta


def default_sources() -> list[pathlib.Path]:
    order = sorted(SRC.glob("*.yaml"))
    return order


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--src", nargs="*", help="YAML 원고(기본: textbook/src/*.yaml 이름순)")
    ap.add_argument("--out", default=str(ROOT / "dist" / "book.html"))
    ap.add_argument("--theme", default="a")
    a = ap.parse_args()
    srcs = [pathlib.Path(s) for s in a.src] if a.src else default_sources()
    meta = build(srcs, pathlib.Path(a.out).resolve(), a.theme)
    print(f"built {a.out}: {meta['pages']} pages, {meta['answers']} answers")
    return 0


if __name__ == "__main__":
    sys.exit(main())
