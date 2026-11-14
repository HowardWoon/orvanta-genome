"""Editable PowerPoint version of the 15-page ORVANTA dashboard.

Usage: python scripts/make_pptx.py
Reads the rendered dashboard (outputs/pdf_build/dashboard.html) and rebuilds every page with native PowerPoint objects:
text boxes, tables, shapes and the pipeline's chart images. Slides are 16 x 9 in, the same size as the PDF. Every word and
table cell can be edited in PowerPoint, Keynote, Google Slides or Canva (import the .pptx).
Writes submission/ORVANTA_GENOME_DASHBOARD_EDITABLE.pptx
"""
from __future__ import annotations
import math, re
from pathlib import Path
from urllib.parse import unquote, urlparse
import lxml.html as LH
from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.enum.dml import MSO_LINE_DASH_STYLE
from pptx.util import Emu, Inches, Pt

ROOT = Path(__file__).resolve().parents[1]
HTML = ROOT / "outputs" / "pdf_build" / "dashboard.html"
OUT = ROOT / "submission" / "ORVANTA_GENOME_DASHBOARD_EDITABLE.pptx"

INK, PAPER, WHITE = "111827", "F5F0E6", "FFFFFF"
BLUE, YELLOW, CORAL, MUTED = "2479D8", "F4D52E", "EF5147", "6B7280"
LV = {"validated": (BLUE, WHITE), "strongly": ("9CC3EF", INK), "supported": (YELLOW, INK), "inconclusive": ("D6D1C4", INK)}
HEAD, BODY, MONO = "Bahnschrift", "Segoe UI", "Consolas"
LEVEL_NAMES = {"VALIDATED", "STRONGLY SUPPORTED", "SUPPORTED", "INCONCLUSIVE"}
CW = {BODY: .45, HEAD: .50, MONO: .55}        # average glyph width as a share of the font size (for height estimates)

PAGE_W, PAGE_H = 16.0, 9.0
MX, TOP, BOTTOM = .55, 1.78, 8.50           # side margin, content top, content bottom (footer sits below)


def rgb(h): return RGBColor.from_string(h)


def clean(t): return re.sub(r"\s+", " ", t or "").strip()


def runs_of(el):
    """Rich-text runs [(text, bold)] of an element, keeping <b>/<strong> as bold."""
    out = []
    def walk(e, bold):
        b = bold or e.tag in ("b", "strong")
        if e.text: out.append((e.text, b))
        for c in e:
            if isinstance(c.tag, str):
                if c.tag == "br": out.append(("\n", b))
                else: walk(c, b)
            if c.tail: out.append((c.tail, bold or e.tag in ("b", "strong")))
    walk(el, False)
    merged = []
    for t, b in out:
        t = re.sub(r"[ \t\r\f\v]+", " ", t.replace("\n", " "))
        if merged and merged[-1][1] == b: merged[-1] = (merged[-1][0] + t, b)
        else: merged.append((t, b))
    if merged: merged[0] = (merged[0][0].lstrip(), merged[0][1]); merged[-1] = (merged[-1][0].rstrip(), merged[-1][1])
    return [(t, b) for t, b in merged if t]


def lines(text, width_in, pt, font=BODY):
    """Estimated wrapped line count of text in a box of width_in at pt (greedy word wrap)."""
    per = max(1, int(0.95 * width_in * 72 / (pt * CW[font])))   # 5% safety for wider-than-average words
    n = 0
    for seg in text.split("\n"):
        cur, k = 0, 1
        for w in seg.split(" "):
            L = len(w)
            if cur and cur + 1 + L > per: k += 1; cur = L
            else: cur = cur + (1 if cur else 0) + L
            while cur > per: k += 1; cur -= per
        n += k
    return n


def lh(pt, k=1.22): return pt * k / 72        # line height in inches


# ------------------------------------------------------------------ drawing primitives
class Canvas:
    def __init__(self, slide): self.s = slide

    def rect(self, x, y, w, h, fill=WHITE, line=INK, lw=1.5, shadow=False, dash=False, shape=MSO_SHAPE.RECTANGLE, name=None):
        if shadow:   # the dashboard's hard offset shadow, drawn as a second rectangle (editable, renders everywhere)
            sh = self.s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x + .045), Inches(y + .045), Inches(w), Inches(h))
            sh.fill.solid(); sh.fill.fore_color.rgb = rgb(INK); sh.line.fill.background(); sh.shadow.inherit = False
            sh.name = (name or "box") + " shadow"
        r = self.s.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
        r.shadow.inherit = False
        if fill: r.fill.solid(); r.fill.fore_color.rgb = rgb(fill)
        else: r.fill.background()
        if line: r.line.color.rgb = rgb(line); r.line.width = Pt(lw)
        else: r.line.fill.background()
        if dash: r.line.dash_style = MSO_LINE_DASH_STYLE.DASH
        if name: r.name = name
        return r

    def text(self, x, y, w, h, paras, pt=10, font=BODY, color=INK, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, margin=0.0,
             bullets=False, name=None, space_after=0):
        """paras: list of paragraphs; each paragraph is a str or a list of (text, bold) runs."""
        tb = self.s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
        tf = tb.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
        tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = Inches(margin)
        for i, p in enumerate(paras):
            para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            para.alignment = align
            if space_after: para.space_after = Pt(space_after)
            rr = [(p, False)] if isinstance(p, str) else p
            if bullets: rr = [("• ", False)] + list(rr)
            for t, b in rr:
                r = para.add_run(); r.text = t
                f = r.font; f.size = Pt(pt); f.name = font; f.bold = b; f.color.rgb = rgb(color)
        if name: tb.name = name
        return tb


# ------------------------------------------------------------------ blocks: measure + draw
class Block:
    def height(self, w, s): raise NotImplementedError
    def draw(self, cv, x, y, w, s): raise NotImplementedError


class Heading(Block):
    def __init__(self, el): self.t = clean(el.text_content())
    def height(self, w, s): return lines(self.t, w, 12.5 * s, HEAD) * lh(12.5 * s) + .06
    def draw(self, cv, x, y, w, s):
        cv.text(x, y, w, self.height(w, s), [[(self.t, True)]], pt=12.5 * s, font=HEAD, name="Heading")


class Note(Block):
    def __init__(self, el): self.r = runs_of(el); self.t = "".join(t for t, _ in self.r)
    def height(self, w, s): return lines(self.t, w, 8.6 * s) * lh(8.6 * s) + .06
    def draw(self, cv, x, y, w, s): cv.text(x, y, w, self.height(w, s), [self.r], pt=8.6 * s, color="374151", name="Note")


class Rule(Block):
    """Rule card: id tag, confidence + test badges, statement, formula box, reading line."""
    def __init__(self, el):
        self.id = clean((el.xpath(".//b[@class='id']") or [None])[0].text_content()) if el.xpath(".//b[@class='id']") else ""
        self.badges = [(clean(b.text_content()), b.get("class")) for b in el.xpath("./span[contains(@class,'pass')]")]
        f = el.xpath("./span[@class='f']"); self.formula = clean(f[0].text_content()) if f else ""
        r = el.xpath(".//div[@class='econ']"); self.reading = runs_of(r[0]) if r else []
        st = LH.fromstring(LH.tostring(el))
        for bad in st.xpath("./span|.//div[@class='econ']|.//b[@class='id']"): bad.drop_tree()
        self.stmt = clean(st.text_content())
        if not self.reading and not self.formula and not self.badges:   # SCAN/TREES/ATLAS/NET cards: id + rich text only
            self.rich = runs_of(st)
        else:
            self.rich = None

    def _parts(self, w, s):
        iw = w - .2
        txt = self.stmt if self.rich is None else "".join(t for t, _ in self.rich)
        stmt_h = lines(txt, iw, 10 * s) * lh(10 * s) + .02
        f_h = (lines(self.formula, iw - .12, 8.6 * s, MONO) * lh(8.6 * s) + .08) if self.formula else 0
        r_txt = "".join(t for t, _ in self.reading)
        r_h = lines(r_txt, iw, 9 * s) * lh(9 * s) if self.reading else 0
        return iw, stmt_h, f_h, r_h

    def height(self, w, s):
        iw, a, b, c = self._parts(w, s)
        return .09 + .22 * s + .04 + a + (.05 + b if b else 0) + (.04 + c if c else 0) + .1 + .1

    def draw(self, cv, x, y, w, s):
        iw, sh, fh, rh = self._parts(w, s); h = self.height(w, s) - .1
        cv.rect(x, y, w, h, shadow=True, lw=2, name=f"Rule card {self.id}")
        bx = x + w - .1
        for t, cls in reversed(self.badges):   # badges right-aligned on the first line
            bw = .13 + len(t) * .062 * s; bx -= bw + .04
            lv = next((k for k in LV if f"lv-{k}" in (cls or "")), None)
            fill, fg = LV[lv] if lv else (BLUE, WHITE)
            b = cv.rect(bx, y + .09, bw, .19 * s, fill=fill, line=INK, lw=.75, name=f"Badge {t}")
            tf = b.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0
            p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; r = p.add_run(); r.text = t
            r.font.size = Pt(6.6 * s); r.font.name = MONO; r.font.bold = True; r.font.color.rgb = rgb(fg)
            tf.vertical_anchor = MSO_ANCHOR.MIDDLE
        if self.id:   # the dashboard's yellow id tag
            t = cv.rect(x + .1, y + .09, .14 + len(self.id) * .085 * s, .2 * s, fill=YELLOW if self.rich is None else INK, line=INK, lw=1, name=f"Rule id {self.id}")
            tf = t.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
            pp = tf.paragraphs[0]; pp.alignment = PP_ALIGN.CENTER; r = pp.add_run(); r.text = self.id
            r.font.size = Pt(8.5 * s); r.font.name = MONO; r.font.bold = True; r.font.color.rgb = rgb(INK if self.rich is None else YELLOW)
        cy = y + .09 + .22 * s + .04
        para = self.rich if self.rich is not None else [(self.stmt, False)]
        cv.text(x + .1, cy, iw, sh, [para], pt=10 * s, name=f"Rule {self.id} statement")
        cy += sh + .05
        if self.formula:
            box = cv.rect(x + .1, cy, iw, fh, fill=PAPER, line=INK, lw=1, dash=True, name=f"Rule {self.id} formula")
            tf = box.text_frame; tf.word_wrap = True
            tf.margin_left = tf.margin_right = Inches(.06); tf.margin_top = tf.margin_bottom = Inches(.03)
            p = tf.paragraphs[0]; p.alignment = PP_ALIGN.LEFT; r = p.add_run(); r.text = self.formula
            r.font.size = Pt(8.6 * s); r.font.name = MONO; r.font.color.rgb = rgb(INK)
            cy += fh + .04
        if self.reading:
            cv.text(x + .1, cy, iw, rh, [self.reading], pt=9 * s, name=f"Rule {self.id} reading")


class Table(Block):
    def __init__(self, el):
        self.rows = []
        for tr in el.xpath(".//tr"):
            cells = []
            for td in tr.xpath("./th|./td"):
                badges = td.xpath(".//span[contains(@class,'lv-')]")
                lv = next((k for k in LV if badges and f"lv-{k}" in badges[0].get("class", "")), None)
                cells.append(dict(runs=runs_of(td) or [("", False)], head=td.tag == "th", lv=lv,
                                  multi=len(badges) > 1 or (len(badges) == 1 and clean(badges[0].text_content()).upper() not in LEVEL_NAMES), ids=[(clean(b.text_content()), next((k for k in LV if f"lv-{k}" in b.get("class", "")), None)) for b in badges]))
            if cells: self.rows.append(cells)
        n = max(len(r) for r in self.rows)
        self.rows = [r + [dict(runs=[("", False)], head=False, lv=None, multi=False, ids=[])] * (n - len(r)) for r in self.rows]
        self.ncol = n

    def _txt(self, c): return "".join(t for t, _ in c["runs"])

    def widths(self, w, s=1.0):
        mins, wt = [], []
        for j in range(self.ncol):
            col = [self._txt(r[j]) for r in self.rows]
            body = [t for r, t in zip(self.rows, col) if not r[j]["head"]] or [""]
            word = max(len(x) for t in body for x in (t.split(" ") or [""]))
            hword = max((len(x) for x in col[0].split(" ")), default=0) if self.rows[0][j]["head"] else 0
            lvcol = any(r[j]["lv"] and not r[j]["multi"] for r in self.rows)
            mins.append(max(word * 8.5 * s * CW[MONO if lvcol else BODY] / 72, hword * 7 * s * CW[MONO] / 72) + .13)
            wt.append(max(3, min(46, max(len(t) for t in body))))
        extra = w - sum(mins)
        if extra <= 0: return [w * m / sum(mins) for m in mins]
        tot = sum(wt); return [m + extra * x / tot for m, x in zip(mins, wt)]

    def _rows_h(self, w, s):
        ws = self.widths(w, s); out = []
        for r in self.rows:
            hmax = 0
            for c, cw in zip(r, ws):
                pt = (7 if c["head"] else 8.5) * s
                txt = self._txt(c) if not c["multi"] else " ".join(t for t, _ in c["ids"])
                hmax = max(hmax, lines(txt, max(.2, cw - .12), pt, MONO if (c["head"] or c["multi"] or c["lv"]) else BODY) * lh(pt, 1.2))
            out.append(hmax + .08)
        return ws, out

    def height(self, w, s): return sum(self._rows_h(w, s)[1]) + .1

    def draw(self, cv, x, y, w, s):
        ws, hs = self._rows_h(w, s)
        gs = cv.s.shapes.add_table(len(self.rows), self.ncol, Inches(x), Inches(y), Inches(w), Inches(sum(hs)))
        gs.name = "Table"; t = gs.table
        tblPr = t._tbl.tblPr; tblPr.set("firstRow", "0"); tblPr.set("bandRow", "0")
        style = tblPr.find("{http://schemas.openxmlformats.org/drawingml/2006/main}tableStyleId")
        if style is not None: style.text = "{5940675A-B579-460E-94D1-54222C63F5DA}"   # 'No Style, Table Grid'
        for j, cw in enumerate(ws): t.columns[j].width = Inches(cw)
        for i, (r, rh) in enumerate(zip(self.rows, hs)):
            t.rows[i].height = Inches(rh)
            for j, c in enumerate(r):
                cell = t.cell(i, j); cell.margin_left = cell.margin_right = Inches(.05); cell.margin_top = cell.margin_bottom = Inches(.02)
                cell.vertical_anchor = MSO_ANCHOR.MIDDLE
                fill, fg = (INK, WHITE) if c["head"] else (WHITE, INK)
                if c["lv"] and not c["multi"]: fill, fg = LV[c["lv"]]
                cell.fill.solid(); cell.fill.fore_color.rgb = rgb(fill)
                tf = cell.text_frame; tf.word_wrap = True; p = tf.paragraphs[0]
                if c["multi"]:   # coverage cell: one coloured id per badge
                    for k, (tid, lv) in enumerate(c["ids"]):
                        rr = p.add_run(); rr.text = (" " if k else "") + tid
                        rr.font.size = Pt(8.5 * s); rr.font.name = MONO; rr.font.bold = True
                        rr.font.color.rgb = rgb({"validated": BLUE, "strongly": "1D5FA8", "supported": "9A7B00", "inconclusive": MUTED}.get(lv, INK))
                    continue
                for tx, b in c["runs"]:
                    rr = p.add_run(); rr.text = tx.upper() if c["head"] else tx
                    rr.font.size = Pt((7 if c["head"] else 8.5) * s); rr.font.name = MONO if (c["head"] or c["lv"]) else BODY
                    rr.font.bold = b or c["head"] or bool(c["lv"]); rr.font.color.rgb = rgb(fg)


class Care(Block):
    def __init__(self, el):
        b = el.xpath("./b"); self.title = clean(b[0].text_content()).upper() if b else "READ WITH CARE"
        self.items = [runs_of(li) for li in el.xpath(".//li")]
        self.coral = "care" in (el.get("class") or "")

    def height(self, w, s):
        return .1 + lh(8 * s) + sum(lines("".join(t for t, _ in it), w - .35, 8.5 * s) * lh(8.5 * s, 1.25) for it in self.items) + .12

    def draw(self, cv, x, y, w, s):
        h = self.height(w, s); cv.rect(x, y, w, h, line=CORAL, lw=2, name="Read with care")
        cv.text(x + .1, y + .06, w - .2, lh(8 * s), [[(self.title, True)]], pt=8 * s, font=MONO, color=CORAL, name="Care title")
        cv.text(x + .1, y + .06 + lh(8 * s) + .02, w - .2, h - lh(8 * s) - .12, self.items, pt=8.5 * s, bullets=True, name="Care items")


class Concl(Block):
    def __init__(self, el):
        self.paras = [runs_of(p) for p in el.xpath("./p")] or [runs_of(el)]
        h = el.xpath(".//b"); self.title = "Conclusion"

    def height(self, w, s):
        return .14 + lh(12 * s) + sum(lines("".join(t for t, _ in p), w - .3, 9.4 * s) * lh(9.4 * s, 1.3) + .05 for p in self.paras) + .1

    def draw(self, cv, x, y, w, s):
        h = self.height(w, s); cv.rect(x, y, w, h, fill=INK, line=INK, lw=2, name="Conclusion")
        cv.text(x + .14, y + .08, w - .28, lh(12 * s), [[(self.title, True)]], pt=12 * s, font=HEAD, color=YELLOW, name="Conclusion title")
        body = [[(t, False) for t, _ in p if t.strip() and t.strip() != "Conclusion"] for p in self.paras]
        cv.text(x + .14, y + .1 + lh(12 * s), w - .28, h - lh(12 * s) - .15, body, pt=9.4 * s, color=PAPER, space_after=3, name="Conclusion text")


class Figure(Block):
    def __init__(self, el, short=False, span=False):
        src = el.xpath(".//img/@src")[0]; self.path = Path(unquote(urlparse(src).path.lstrip("/")))
        if not self.path.exists(): self.path = ROOT / "outputs" / "charts" / Path(src).name
        cap = el.xpath(".//figcaption"); self.cap = runs_of(cap[0]) if cap else []
        with Image.open(self.path) as im: self.aspect = im.width / im.height
        self.short, self.span = short, span

    def img_size(self, w, s):
        iw = (w - .16) * s; ih = iw / self.aspect
        if self.short and ih > 2.35 * s: ih = 2.35 * s; iw = ih * self.aspect
        return iw, ih

    def cap_h(self, w): return lines("".join(t for t, _ in self.cap), w - .2, 8.5) * lh(8.5) + .1 if self.cap else 0

    def height(self, w, s): return .08 + self.img_size(w, s)[1] + .06 + self.cap_h(w) + .1

    def draw(self, cv, x, y, w, s, h=None):
        iw, ih = self.img_size(w, s); h = h or self.height(w, s) - .1
        cv.rect(x, y, w, h, shadow=True, lw=2, name=f"Chart card {self.path.stem}")
        pic = cv.s.shapes.add_picture(str(self.path), Inches(x + (w - iw) / 2), Inches(y + .08), Inches(iw), Inches(ih))
        pic.name = f"Chart {self.path.stem}"
        if self.cap:
            cy = y + .08 + ih + .06
            ln = cv.s.shapes.add_connector(1, Inches(x + .08), Inches(cy - .03), Inches(x + w - .08), Inches(cy - .03))
            ln.line.color.rgb = rgb("D6D1C4"); ln.line.width = Pt(.75)
            cv.text(x + .1, cy, w - .2, self.cap_h(w), [self.cap], pt=8.5, name=f"Reading {self.path.stem}")


class Panel(Block):
    """A grid cell holding blocks instead of a chart (e.g. a table)."""
    def __init__(self, blocks): self.blocks = blocks
    def height(self, w, s): return .12 + sum(b.height(w - .2, s) + .06 for b in self.blocks) + .1
    def draw(self, cv, x, y, w, s, h=None):
        cv.rect(x, y, w, (h or self.height(w, s) - .1), shadow=True, lw=2, name="Panel")
        cy = y + .1
        for b in self.blocks:
            b.draw(cv, x + .1, cy, w - .2, s); cy += b.height(w - .2, s) + .06


def blocks_of(container):
    out = []
    for el in container:
        if not isinstance(el.tag, str): continue
        cls = el.get("class") or ""
        if el.tag == "h2": out.append(Heading(el))
        elif el.tag == "table": out.append(Table(el))
        elif el.tag == "p": out.append(Note(el))
        elif "rule" in cls.split(): out.append(Rule(el))
        elif "care" in cls.split(): out.append(Care(el))
        elif "concl" in cls.split(): out.append(Concl(el))
        elif el.tag == "div": out.extend(blocks_of(el))
    return out


def stack(cv, blocks, x, y, w, bottom, gap=.1, floor=.72, grow=1.0):
    """Draw blocks top-down; scale fonts uniformly so the stack ends above `bottom`."""
    fits = lambda s: y + sum(b.height(w, s) + gap for b in blocks) <= bottom
    s = 1.0
    if fits(s):
        while s < grow and fits(s + .02): s += .02
    else:
        while s > floor and not fits(s): s -= .02
    for b in blocks:
        b.draw(cv, x, y, w, s); y += b.height(w, s) + gap
    return s


def grid(cv, cells, x, y, w, bottom, gap=.2):
    """2-column chart grid; a span cell takes a full row. Images shrink uniformly to fit the height."""
    rows, cur = [], []
    for c in cells:
        if getattr(c, "span", False):
            if cur: rows.append(cur); cur = []
            rows.append([c])
        else:
            cur.append(c)
            if len(cur) == 2: rows.append(cur); cur = []
    if cur: rows.append(cur)
    cw = (w - gap) / 2
    def row_h(r, s): return max(c.height(w if len(r) == 1 and getattr(r[0], "span", False) else cw, s) for c in r)
    s = 1.0
    while s > .6 and y + sum(row_h(r, s) + gap - .1 for r in rows) > bottom: s -= .02
    for r in rows:
        h = row_h(r, s) - .1
        for i, c in enumerate(r):
            cwid = w if len(r) == 1 and getattr(c, "span", False) else cw
            c.draw(cv, x + i * (cw + gap), y, cwid, s, h=h)
        y += h + gap
    return s


# ------------------------------------------------------------------ page frame
def frame(cv, eyebrow, title, sub, n, total):
    sl = cv.s
    bg = sl.background.fill; bg.solid(); bg.fore_color.rgb = rgb(PAPER)
    ew = .3 + len(eyebrow) * .092
    e = cv.rect(MX, .36, ew, .3, fill=INK, line=None, name="Eyebrow")
    tf = e.text_frame; tf.margin_left = Inches(.12); tf.margin_top = tf.margin_bottom = 0; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    tf.paragraphs[0].alignment = PP_ALIGN.LEFT
    r = tf.paragraphs[0].add_run(); r.text = eyebrow.upper(); r.font.size = Pt(9.5); r.font.name = MONO; r.font.bold = True; r.font.color.rgb = rgb(YELLOW)
    cv.text(6.9, .33, 1.3, .34, [[("ORVANTA", True)]], pt=12, font=HEAD, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE, name="Brand")
    g = cv.rect(8.25, .38, 1.05, .26, fill=YELLOW, line=INK, lw=1.25, name="Brand tag")
    tf = g.text_frame; tf.margin_left = tf.margin_right = tf.margin_top = tf.margin_bottom = 0; tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER; r = p.add_run(); r.text = "GENOME"; r.font.size = Pt(11); r.font.name = HEAD; r.font.bold = True; r.font.color.rgb = rgb(INK)
    cv.text(PAGE_W - MX - 1.2, .33, 1.2, .34, [f"{n} / {total}"], pt=10, font=MONO, align=PP_ALIGN.RIGHT, anchor=MSO_ANCHOR.MIDDLE, name="Page number")
    ln = sl.shapes.add_connector(1, Inches(MX), Inches(.76), Inches(PAGE_W - MX), Inches(.76)); ln.line.color.rgb = rgb(INK); ln.line.width = Pt(3)
    tpt = 23 if len(title) < 95 else 20
    cv.text(MX, .86, PAGE_W - 2 * MX, .5, [[(title, True)]], pt=tpt, font=HEAD, name="Title")
    sub_h = lines("".join(t for t, _ in sub), PAGE_W - 2 * MX, 11) * lh(11)
    cv.text(MX, 1.36, PAGE_W - 2 * MX, sub_h, [sub], pt=11, name="Research question")
    return max(TOP, 1.36 + sub_h + .14)
    cv.text(MX, 8.66, 11, .22, ["UMDAC Datathon 2026 · Swift case · synthetic data, n = 10,000,000 · every figure generated from outputs/evidence"],
            pt=7.5, font=MONO, color="374151", name="Footer")
    cv.text(PAGE_W - MX - 2, 8.66, 2, .22, ["Team Nai Long"], pt=7.5, font=MONO, color="374151", align=PP_ALIGN.RIGHT, name="Footer team")


def kpis(cv, el, y):
    ks = el.xpath("./div"); n = len(ks); gap = .12; w = (PAGE_W - 2 * MX - gap * (n - 1)) / n
    for i, k in enumerate(ks):
        x = MX + i * (w + gap); b = clean(k.xpath("./b")[0].text_content()); s = clean(k.xpath("./span")[0].text_content())
        cv.rect(x, y, w, .82, shadow=True, lw=2, name=f"KPI {b}")
        cv.text(x + .11, y + .06, w - .2, .38, [[(b, True)]], pt=19, font=HEAD, name="KPI value")
        cv.text(x + .11, y + .44, w - .2, .36, [s.upper()], pt=7.2, font=MONO, name="KPI label")
    return y + .82 + .2


def journey(cv, el, y):
    ds = el.xpath("./div"); n = len(ds); w = (PAGE_W - 2 * MX) / n
    fills = [WHITE, "CFE3F7", "FBE3E1", BLUE, YELLOW]
    for i, d in enumerate(ds):
        x = MX + i * w; b = d.xpath("./b"); head = clean(b[0].text_content()) if b else ""
        rest = clean(d.text_content())[len(head):].strip()
        fg = WHITE if fills[i % 5] == BLUE else INK
        cv.rect(x, y, w, .66, fill=fills[i % 5], lw=2, name=f"Stage {head}")
        cv.text(x + .1, y + .05, w - .2, .6, [[(head, True)], rest], pt=9, color=fg, name="Stage text")
    return y + .66 + .22


def main():
    doc = LH.parse(str(HTML)).getroot()
    secs = doc.xpath("//section[contains(@class,'pg')]"); total = len(secs)
    prs = Presentation(); prs.slide_width, prs.slide_height = Inches(PAGE_W), Inches(PAGE_H)
    blank = prs.slide_layouts[6]
    for n, sec in enumerate(secs, 1):
        sl = prs.slides.add_slide(blank); cv = Canvas(sl)
        eyebrow = clean(sec.xpath(".//span[@class='eyebrow']")[0].text_content())
        title = clean(sec.xpath(".//h1")[0].text_content())
        sub = runs_of(sec.xpath(".//p[contains(@class,'sub')]")[0])
        y = frame(cv, eyebrow, title, sub, n, total)
        k = sec.xpath("./div[@class='kpis6']")
        if k: y = kpis(cv, k[0], y)
        j = sec.xpath("./div[@class='journey']")
        if j: y = journey(cv, j[0], y)
        tri = sec.xpath("./div[@class='tri']")
        if tri:
            cols = tri[0].xpath("./div"); gap = .25; w = (PAGE_W - 2 * MX - gap * (len(cols) - 1)) / len(cols)
            for i, c in enumerate(cols): stack(cv, blocks_of(c), MX + i * (w + gap), y, w, BOTTOM, grow=1.25)
        fp = sec.xpath("./div[contains(@class,'fp')]")
        if fp:
            lcs = fp[0].xpath("./div[@class='lc']"); cg = fp[0].xpath("./div[@class='cg']")
            if cg:   # feature page: left text column + 2x2 chart grid
                lw = 5.45; stack(cv, blocks_of(lcs[0]), MX, y, lw, BOTTOM, grow=1.12)
                cells = []
                for c in cg[0]:
                    if not isinstance(c.tag, str): continue
                    cls = c.get("class") or ""; st = c.get("style") or ""
                    if c.tag == "figure": cells.append(Figure(c, short="short" in cls, span="1/3" in st))
                    else:
                        bl = blocks_of(c)
                        if bl: cells.append(Panel(bl))
                grid(cv, cells, MX + lw + .25, y, PAGE_W - 2 * MX - lw - .25, BOTTOM)
            else:    # synthesis page: two text columns 1.25 : 1
                gap = .3; tw = PAGE_W - 2 * MX - gap; w1 = tw * 1.25 / 2.25
                stack(cv, blocks_of(lcs[0]), MX, y, w1, BOTTOM, grow=1.25)
                stack(cv, blocks_of(lcs[1]), MX + w1 + gap, y, tw - w1, BOTTOM, grow=1.25)
        sl.notes_slide.notes_text_frame.text = (f"ORVANTA dashboard page {n}. All numbers are read from outputs/evidence (validation.json, register, "
                                                "evidence ledger). Charts are the pipeline's PNGs; text and tables are editable.")
    prs.core_properties.title = "ORVANTA Genome — dashboard (editable)"; prs.core_properties.author = "Team Nai Long"
    prs.save(OUT); print("wrote", OUT, "| slides:", total)


if __name__ == "__main__":
    main()
