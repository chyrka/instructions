#!/usr/bin/env python3
"""
Build OMNIVERSE_SETUP_AWS_G5.pptx in the visual style of the
"Omniverse Set-Up-demo.pptx" template (NVIDIA green bokeh section dividers,
white content slides with centered bold title, page number, NVIDIA mark and
green edge bar in the footer).

Content source: OMNIVERSE_SETUP_AWS_G5.md (same folder).

    pip install python-pptx Pillow
    python3 build_deck.py
"""
from __future__ import annotations

import re
import uuid
from pathlib import Path

from lxml import etree
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

HERE = Path(__file__).resolve().parent
ASSETS = HERE / "assets"
OUT = HERE / "OMNIVERSE_SETUP_AWS_G5.pptx"

SLIDE_W, SLIDE_H = Inches(13.333), Inches(7.5)

# Template geometry measured from the reference screenshots
CONTENT_L = Inches(0.75)
CONTENT_R = Inches(12.47)
CONTENT_W = CONTENT_R - CONTENT_L
BODY_T = Inches(1.30)
BODY_B = Inches(6.85)
TITLE_Y = Inches(0.36)

FONT = "Arial"
MONO = "Consolas"

NV_GREEN = RGBColor(0x76, 0xB9, 0x00)
NV_GREEN_DARK = RGBColor(0x4E, 0x7A, 0x00)
NV_GREEN_TINT = RGBColor(0xEE, 0xF7, 0xDC)
INK = RGBColor(0x1A, 0x1A, 0x1A)
INK_SOFT = RGBColor(0x3C, 0x3C, 0x3C)
GRAY = RGBColor(0x76, 0x76, 0x76)
GRAY_LINE = RGBColor(0xD9, 0xD9, 0xD9)
GRAY_BAND = RGBColor(0xF5, 0xF5, 0xF5)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
CODE_BG = RGBColor(0x1E, 0x1E, 0x1E)
CODE_FG = RGBColor(0xE6, 0xE6, 0xE6)
CODE_INLINE = RGBColor(0x2E, 0x6B, 0x1F)
AMBER_TINT = RGBColor(0xFF, 0xF4, 0xDB)
AMBER = RGBColor(0xE0, 0x9A, 0x00)


# --------------------------------------------------------------------------- #
# low-level helpers
# --------------------------------------------------------------------------- #
INLINE_RE = re.compile(r"(\*\*.+?\*\*|`[^`]+`)")


def add_runs(p, text: str, size: int, color=INK, bold=False, mono_color=CODE_INLINE):
    """Append runs to paragraph p, honouring **bold** and `code` markdown."""
    for tok in INLINE_RE.split(text):
        if not tok:
            continue
        r = p.add_run()
        f = r.font
        f.size = Pt(size)
        if tok.startswith("**") and tok.endswith("**"):
            inner = tok[2:-2]
            f.bold = True
            if inner.startswith("`") and inner.endswith("`"):
                r.text = inner[1:-1]
                f.name = MONO
                f.color.rgb = mono_color
            else:
                r.text = inner
                f.name = FONT
                f.color.rgb = color
        elif tok.startswith("`") and tok.endswith("`"):
            r.text = tok[1:-1]
            f.name = MONO
            f.bold = bold
            f.color.rgb = mono_color
        else:
            r.text = tok
            f.name = FONT
            f.bold = bold
            f.color.rgb = color
    return p


def set_bullet(p, kind: str = "bullet", level: int = 0, char: str = "•"):
    """Attach a real bullet / auto-number to a paragraph (python-pptx has no API).

    kind: "bullet" | "check" | "number" | "number@N" (auto-number starting at N)
    """
    start_at = None
    if kind.startswith("number@"):
        kind, start_at = "number", kind.split("@", 1)[1]
    pPr = p._p.get_or_add_pPr()
    indent = Inches(0.28)
    pPr.set("marL", str(int(indent * (level + 1))))
    pPr.set("indent", str(-int(indent)))
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum", "a:buFont", "a:buClr"):
        for el in pPr.findall(qn(tag)):
            pPr.remove(el)
    buClr = etree.SubElement(pPr, qn("a:buClr"))
    etree.SubElement(buClr, qn("a:srgbClr")).set("val", "76B900")
    buFont = etree.SubElement(pPr, qn("a:buFont"))
    buFont.set("typeface", FONT)
    if kind == "number":
        num = etree.SubElement(pPr, qn("a:buAutoNum"))
        num.set("type", "arabicPeriod")
        if start_at:
            num.set("startAt", start_at)
    elif kind == "check":
        etree.SubElement(pPr, qn("a:buChar")).set("char", "☐")
    else:
        etree.SubElement(pPr, qn("a:buChar")).set("char", char if level == 0 else "–")


def paragraph(tf, text: str, size=14, color=INK, bold=False, bullet=None, level=0,
              space_after=6, align=None, first=False, line_spacing=None):
    p = tf.paragraphs[0] if first else tf.add_paragraph()
    p.space_after = Pt(space_after)
    if line_spacing:
        p.line_spacing = line_spacing
    if align is not None:
        p.alignment = align
    add_runs(p, text, size, color=color, bold=bold)
    if bullet:
        set_bullet(p, bullet, level)
    return p


def textbox(slide, l, t, w, h, anchor=MSO_ANCHOR.TOP, margin=Inches(0.05)):
    tb = slide.shapes.add_textbox(l, t, w, h)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = margin
    tf.margin_top = tf.margin_bottom = margin
    return tb, tf


def no_line(shape):
    shape.line.fill.background()
    shape.shadow.inherit = False


def rect(slide, l, t, w, h, fill, rounded=False, radius=0.04):
    shp = slide.shapes.add_shape(
        MSO_SHAPE.ROUNDED_RECTANGLE if rounded else MSO_SHAPE.RECTANGLE, l, t, w, h)
    shp.fill.solid()
    shp.fill.fore_color.rgb = fill
    no_line(shp)
    if rounded:
        shp.adjustments[0] = radius
    return shp


def outer_shadow(shape, blur=Pt(6), dist=Pt(3), alpha=35):
    spPr = shape._element.spPr
    for el in spPr.findall(qn("a:effectLst")):
        spPr.remove(el)
    eff = etree.SubElement(spPr, qn("a:effectLst"))
    sh = etree.SubElement(eff, qn("a:outerShdw"))
    sh.set("blurRad", str(int(blur)))
    sh.set("dist", str(int(dist)))
    sh.set("dir", "5400000")
    sh.set("algn", "t")
    sh.set("rotWithShape", "0")
    clr = etree.SubElement(sh, qn("a:srgbClr"))
    clr.set("val", "000000")
    etree.SubElement(clr, qn("a:alpha")).set("val", str(alpha * 1000))


def cell_border(cell, side: str, color="D9D9D9", width=Pt(0.75)):
    tcPr = cell._tc.get_or_add_tcPr()
    tag = {"L": "a:lnL", "R": "a:lnR", "T": "a:lnT", "B": "a:lnB"}[side]
    for el in tcPr.findall(qn(tag)):
        tcPr.remove(el)
    ln = etree.SubElement(tcPr, qn(tag))
    ln.set("w", str(int(width)))
    ln.set("cap", "flat")
    ln.set("cmpd", "sng")
    ln.set("algn", "ctr")
    sf = etree.SubElement(ln, qn("a:solidFill"))
    etree.SubElement(sf, qn("a:srgbClr")).set("val", color)
    etree.SubElement(ln, qn("a:prstDash")).set("val", "solid")


def cell_no_border(cell, sides="LRTB"):
    tcPr = cell._tc.get_or_add_tcPr()
    for s in sides:
        tag = {"L": "a:lnL", "R": "a:lnR", "T": "a:lnT", "B": "a:lnB"}[s]
        for el in tcPr.findall(qn(tag)):
            tcPr.remove(el)
        ln = etree.SubElement(tcPr, qn(tag))
        ln.set("w", "0")
        etree.SubElement(ln, qn("a:noFill"))


# --------------------------------------------------------------------------- #
# deck-level building blocks
# --------------------------------------------------------------------------- #
class Deck:
    def __init__(self):
        self.prs = Presentation()
        self.prs.slide_width = SLIDE_W
        self.prs.slide_height = SLIDE_H
        self.blank = self.prs.slide_layouts[6]
        self.n = 0

    # ---- chrome ---------------------------------------------------------- #
    def _footer(self, slide):
        # page number (live field so numbering survives copy into the template)
        tb, tf = textbox(slide, Inches(11.85), Inches(7.02), Inches(0.5), Inches(0.3),
                         anchor=MSO_ANCHOR.MIDDLE, margin=0)
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.RIGHT
        fld = etree.SubElement(p._p, qn("a:fld"))
        fld.set("id", "{" + str(uuid.uuid4()).upper() + "}")
        fld.set("type", "slidenum")
        rPr = etree.SubElement(fld, qn("a:rPr"))
        rPr.set("lang", "en-US")
        rPr.set("sz", "900")
        sf = etree.SubElement(rPr, qn("a:solidFill"))
        etree.SubElement(sf, qn("a:srgbClr")).set("val", "767676")
        etree.SubElement(rPr, qn("a:latin")).set("typeface", FONT)
        etree.SubElement(fld, qn("a:t")).text = str(self.n)
        # NVIDIA mark
        slide.shapes.add_picture(str(ASSETS / "nvidia_footer_logo.png"),
                                 Inches(12.39), Inches(7.06), width=Inches(0.73))
        # green edge bar
        rect(slide, Inches(13.26), Inches(7.16), Inches(0.08), Inches(0.34), NV_GREEN)

    def _notes(self, slide, notes: str | None):
        if notes:
            slide.notes_slide.notes_text_frame.text = notes.strip()

    # ---- slide types ----------------------------------------------------- #
    def content(self, title: str, notes: str | None = None):
        self.n += 1
        s = self.prs.slides.add_slide(self.blank)
        tb, tf = textbox(s, CONTENT_L, TITLE_Y, CONTENT_W, Inches(0.55), anchor=MSO_ANCHOR.MIDDLE)
        p = tf.paragraphs[0]
        p.alignment = PP_ALIGN.CENTER
        r = p.add_run()
        r.text = title.upper()
        r.font.name = FONT
        r.font.size = Pt(20)
        r.font.bold = True
        r.font.color.rgb = RGBColor(0, 0, 0)
        self._footer(s)
        self._notes(s, notes)
        return s

    def divider(self, title: str, notes: str | None = None):
        self.n += 1
        s = self.prs.slides.add_slide(self.blank)
        s.shapes.add_picture(str(ASSETS / "section_bg.png"), 0, 0, SLIDE_W, SLIDE_H)
        tb, tf = textbox(s, Inches(0.55), Inches(6.35), Inches(9), Inches(0.7), anchor=MSO_ANCHOR.BOTTOM)
        p = tf.paragraphs[0]
        r = p.add_run()
        r.text = title.upper()
        r.font.name = FONT
        r.font.size = Pt(26)
        r.font.bold = True
        r.font.color.rgb = WHITE
        self._notes(s, notes)
        return s

    def cover(self, line1: str, line2: str, subtitle: str, notes: str | None = None):
        self.n += 1
        s = self.prs.slides.add_slide(self.blank)
        s.shapes.add_picture(str(ASSETS / "section_bg.png"), 0, 0, SLIDE_W, SLIDE_H)
        tb, tf = textbox(s, Inches(0.55), Inches(4.4), Inches(9), Inches(2.0), anchor=MSO_ANCHOR.BOTTOM)
        for i, line in enumerate((line1, line2)):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.space_after = Pt(0)
            p.line_spacing = 0.95
            r = p.add_run()
            r.text = line.upper()
            r.font.name = FONT
            r.font.size = Pt(48)
            r.font.bold = True
            r.font.color.rgb = WHITE
        rect(s, Inches(0.62), Inches(6.5), Inches(0.9), Inches(0.05), NV_GREEN)
        tb, tf = textbox(s, Inches(0.55), Inches(6.55), Inches(9), Inches(0.5), anchor=MSO_ANCHOR.TOP)
        p = tf.paragraphs[0]
        r = p.add_run()
        r.text = subtitle
        r.font.name = FONT
        r.font.size = Pt(16)
        r.font.color.rgb = WHITE
        self._notes(s, notes)
        return s

    # ---- body components -------------------------------------------------- #
    def bullets(self, slide, items, l=CONTENT_L, t=BODY_T, w=CONTENT_W, h=None, size=14,
                kind="bullet", space_after=8, anchor=MSO_ANCHOR.TOP):
        """items: list of str or (str, level) or (str, level, kind)."""
        h = h or (BODY_B - t)
        tb, tf = textbox(slide, l, t, w, h, anchor=anchor)
        for i, it in enumerate(items):
            if isinstance(it, str):
                text, level, k = it, 0, kind
            elif len(it) == 2:
                text, level = it
                k = kind
            else:
                text, level, k = it
            if k.startswith("number") and level > 0:
                k = "bullet"
            paragraph(tf, text, size=size if level == 0 else size - 1,
                      color=INK if level == 0 else INK_SOFT, bullet=k, level=level,
                      space_after=space_after if level == 0 else max(space_after - 4, 2),
                      first=(i == 0))
        return tb

    def heading(self, slide, text, l, t, w, size=15, color=NV_GREEN_DARK):
        tb, tf = textbox(slide, l, t, w, Inches(0.4), anchor=MSO_ANCHOR.MIDDLE)
        paragraph(tf, text, size=size, color=color, bold=True, first=True, space_after=0)
        return tb

    def text(self, slide, text, l, t, w, h, size=14, color=INK, align=None, anchor=MSO_ANCHOR.TOP):
        tb, tf = textbox(slide, l, t, w, h, anchor=anchor)
        paragraph(tf, text, size=size, color=color, first=True, align=align, space_after=0)
        return tb

    def code(self, slide, lines, l, t, w, h=None, size=12):
        if isinstance(lines, str):
            lines = lines.splitlines()
        h = h or Pt(size * 1.55 * len(lines) + 20)
        box = rect(slide, l, t, w, h, CODE_BG, rounded=True, radius=0.06)
        rect(slide, l, t, Inches(0.07), h, NV_GREEN, rounded=False)
        tb, tf = textbox(slide, l + Inches(0.15), t, w - Inches(0.25), h,
                         anchor=MSO_ANCHOR.MIDDLE, margin=Inches(0.08))
        for i, line in enumerate(lines):
            p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            p.space_after = Pt(2)
            r = p.add_run()
            r.text = line
            r.font.name = MONO
            r.font.size = Pt(size)
            r.font.color.rgb = CODE_FG if not line.lstrip().startswith(("#", "REM", "::")) else GRAY
        return box, h

    def callout(self, slide, text, l, t, w, h=None, size=13, tone="green", label=None):
        fill, bar = (NV_GREEN_TINT, NV_GREEN) if tone == "green" else (AMBER_TINT, AMBER)
        h = h or Inches(0.75)
        rect(slide, l, t, w, h, fill)
        rect(slide, l, t, Inches(0.07), h, bar)
        tb, tf = textbox(slide, l + Inches(0.15), t, w - Inches(0.25), h,
                         anchor=MSO_ANCHOR.MIDDLE, margin=Inches(0.08))
        if label:
            paragraph(tf, label, size=size - 1, color=NV_GREEN_DARK if tone == "green" else AMBER,
                      bold=True, first=True, space_after=2)
            paragraph(tf, text, size=size, color=INK, space_after=0)
        else:
            paragraph(tf, text, size=size, color=INK, first=True, space_after=0)
        return h

    def table(self, slide, header, rows, l, t, w, col_widths=None, size=11, row_h=Inches(0.36),
              header_h=Inches(0.38), highlight_rows=(), links_col=None):
        nrows, ncols = len(rows) + 1, len(header)
        gshape = slide.shapes.add_table(nrows, ncols, l, t, w, header_h + row_h * len(rows))
        tbl = gshape.table
        # kill built-in style banding so our fills rule
        tbl.first_row = False
        tbl.horz_banding = False
        tblPr = tbl._tbl.tblPr
        for el in tblPr.findall(qn("a:tableStyleId")):
            tblPr.remove(el)
        if col_widths:
            total = sum(col_widths)
            for i, cw in enumerate(col_widths):
                tbl.columns[i].width = int(w * cw / total)
        tbl.rows[0].height = header_h
        for i in range(1, nrows):
            tbl.rows[i].height = row_h

        def style_cell(cell, text, bold=False, fill=None, color=INK, url=None, hdr=False):
            cell.margin_left = cell.margin_right = Inches(0.08)
            cell.margin_top = cell.margin_bottom = Inches(0.03)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            tf = cell.text_frame
            tf.word_wrap = True
            p = tf.paragraphs[0]
            p.space_after = Pt(0)
            if url:
                r = p.add_run()
                r.text = text
                r.font.name = FONT
                r.font.size = Pt(size)
                r.font.color.rgb = NV_GREEN_DARK
                r.hyperlink.address = url
            else:
                add_runs(p, text, size, color=color, bold=bold,
                         mono_color=WHITE if hdr else CODE_INLINE)
            cell.fill.solid()
            cell.fill.fore_color.rgb = fill or WHITE
            cell_no_border(cell, "LR")
            cell_border(cell, "B", "D9D9D9")
            cell_border(cell, "T", "D9D9D9" if not hdr else "2B2B2B")

        for c, htxt in enumerate(header):
            style_cell(tbl.cell(0, c), htxt, bold=True, fill=RGBColor(0x2B, 0x2B, 0x2B), color=WHITE, hdr=True)
        for r, row in enumerate(rows, start=1):
            band = GRAY_BAND if r % 2 == 0 else WHITE
            if (r - 1) in highlight_rows:
                band = NV_GREEN_TINT
            for c, val in enumerate(row):
                url = val if (links_col is not None and c == links_col and val.startswith("http")) else None
                style_cell(tbl.cell(r, c), val, fill=band, url=url)
        return gshape

    def picture_framed(self, slide, path, l, t, w=None, h=None):
        pic = slide.shapes.add_picture(str(path), l, t, w, h)
        outer_shadow(pic)
        return pic

    def save(self):
        self.prs.save(OUT)
        return OUT


# --------------------------------------------------------------------------- #
# the deck
# --------------------------------------------------------------------------- #
def build():
    d = Deck()
    HALF = Inches(5.7)
    GUTTER = CONTENT_W - 2 * HALF
    COL2_L = CONTENT_L + HALF + GUTTER

    # 1 -- Title --------------------------------------------------------------
    d.cover("Omniverse", "Set Up", "AWS G5  ·  NVIDIA A10G  ·  Omniverse Kit", notes="""
Hello everyone.
In this session we walk through how NVIDIA Omniverse is set up in the cloud. This is a demonstration — you do not need to install or configure anything.
By the end you will understand how GPU quota, the G5 instance, drivers, CUDA, and Kit fit together.""")

    # 2 -- Agenda -------------------------------------------------------------
    s = d.content("Agenda", notes="""
GPU quota cannot be created by Terraform, CloudFormation, or Bicep. It is a manual portal request per region.
Instances for this cohort are already prepared. We focus on the environment, the install path, and how components work together.""")
    d.bullets(s, [
        "Requesting GPU quota",
        "Launch virtual machine (Azure vs AWS G5)",
        "NVIDIA GPU driver",
        "CUDA Toolkit",
        "Omniverse Kit",
    ], l=Inches(3.6), t=Inches(1.8), w=Inches(7), size=22, kind="number", space_after=18)

    # 3 -- Requesting quota increase (AWS) --------------------------------------
    s = d.content("Requesting quota increase", notes="""
Quota is regional. Approving G5 in us-east-1 does nothing for us-west-2.
G5 is not available in every AZ (example: historically weak in us-west-1). Pick a Region that has G5 capacity before you file the ticket.""")
    d.text(s, "GPU quota is a **mandatory** step. Without it, **Launch instance** fails with a vCPU limit error.",
           CONTENT_L, BODY_T, CONTENT_W, Inches(0.4), size=14)
    d.heading(s, "AWS (target for this engagement)", CONTENT_L, Inches(1.75), HALF)
    d.table(s, ["Item", "Value"], [
        ["Family", "**G5** — NVIDIA **A10G** Tensor Core (24 GB VRAM)"],
        ["Quota name", "**Running On-Demand G and VT instances**"],
        ["Unit", "**vCPUs per Region** (not “number of VMs”)"],
        ["Default", "Often **0** on a new account"],
        ["Where", "AWS Console → **Service Quotas** → **Amazon EC2**"],
        ["Filter", "`On-Demand` + `G and VT`"],
        ["Do not use", "Spot quota (`All G and VT Spot Instance Requests`) — will not launch On-Demand G5"],
    ], CONTENT_L, Inches(2.15), HALF, col_widths=[1.1, 3.4], size=11, row_h=Inches(0.5))
    d.heading(s, "Recommended request (demo / workstation)", COL2_L, Inches(1.75), HALF)
    d.table(s, ["Use case", "Instance", "vCPUs", "Why"], [
        ["Kit smoke test", "`g5.2xlarge`", "**8** (+ buffer)", "Minimum comfortable Windows + Kit"],
        ["RTX workstation (preferred)", "`g5.4xlarge`", "**16**", "Closest AWS match to Azure `Standard_NV18ads_A10_v5`"],
        ["Heavy USD / multi-viewport", "`g5.8xlarge`", "**32**", "More host RAM and EBS / network"],
    ], COL2_L, Inches(2.15), HALF, col_widths=[1.6, 1.1, 0.9, 2.2], size=10.5, row_h=Inches(0.6),
        highlight_rows=(1,))
    d.callout(s, "Always request **current usage + planned G5 vCPUs + 10–30 % buffer**, in the **same Region** where you will launch.",
              COL2_L, Inches(4.55), HALF, h=Inches(0.9), size=12)
    d.callout(s, "Quota is **regional**. Approving G5 in `us-east-1` does nothing for `us-west-2`. Pick a Region with G5 capacity before filing the ticket.",
              COL2_L, Inches(5.6), HALF, h=Inches(0.9), size=12, tone="amber")

    # 3b -- Azure parallel --------------------------------------------------------
    s = d.content("Requesting quota increase — Azure parallel", notes="""
Same concept on Azure: the NV A10 v5 family quota in the target region must cover 18 vCPUs for Standard_NV18ads_A10_v5.
This is the slide that mirrors the original Azure-based template; the AWS slide before it is the target for this engagement.""")
    d.heading(s, "Azure (template parallel)", CONTENT_L, BODY_T, HALF)
    d.table(s, ["Item", "Value"], [
        ["VM size", "`Standard_NV18ads_A10_v5`"],
        ["Need", "**18 vCPUs** in the NV A10 v5 family"],
        ["Where", "Azure Portal → **Quotas** → Compute"],
        ["Filter", "`nvadsa10v5` · Region e.g. **East US**"],
    ], CONTENT_L, Inches(1.75), HALF, col_widths=[1.1, 3.4], size=12, row_h=Inches(0.5))
    d.heading(s, "Same rule, both clouds", COL2_L, BODY_T, HALF)
    d.bullets(s, [
        "Quota is a **manual portal request** — not Terraform, CloudFormation, or Bicep.",
        "Unit is **vCPUs per Region**, never “number of VMs”.",
        "Request in the **same Region** you will launch in; approval is not global.",
        "File the ticket **before** the workshop — approval can take hours to days.",
        "Do not confuse **On-Demand** quota with **Spot** quota.",
    ], l=COL2_L, t=Inches(1.75), w=HALF, size=13, space_after=8)

    # 4 -- Section: Launch virtual machine -----------------------------------------
    d.divider("Launch virtual machine")

    # 5 -- Launch Azure VM (context) ----------------------------------------------
    s = d.content("Launch Azure virtual machine", notes="""
This is the Azure context slide from the original template. Connect to the VM over RDP.""")
    d.text(s, "Connect to the virtual machine over **RDP**.", CONTENT_L, BODY_T, CONTENT_W, Inches(0.4), size=15)
    d.heading(s, "Typical training SKU from the template", CONTENT_L, Inches(1.9), HALF)
    d.bullets(s, [
        "Size: `Standard_NV18ads_A10_v5`",
        "GPU: NVIDIA **A10**",
        "OS: Windows 11 Pro / Enterprise image",
        "Access: RDP **3389** only from corporate CIDR",
    ], l=CONTENT_L, t=Inches(2.35), w=HALF, size=14, space_after=10)
    d.callout(s, "Two clouds, one GPU class: **NVIDIA Ampere A10 / A10G** for RTX. Everything after the VM launch (driver → CUDA → Kit) is identical on Azure and AWS.",
              COL2_L, Inches(2.35), HALF, h=Inches(1.3), size=13, label="Why it maps 1:1 to AWS G5")

    # 6 -- Azure vs AWS mapping --------------------------------------------------
    s = d.content("Launch Azure virtual machine — AWS mapping", notes="""
A10 vs A10G: same Ampere generation, 24 GB; A10G is the AWS data-center SKU. RTX in Omniverse is supported on both.""")
    d.table(s, ["Azure", "AWS G5 equivalent"], [
        ["`Standard_NV18ads_A10_v5` (18 vCPU, A10)", "**`g5.4xlarge`** (16 vCPU, 64 GiB, **1× A10G 24 GB**)"],
        ["Resource group + VNet + NSG", "VPC + subnet + **Security Group** (+ optional NACL)"],
        ["Public IP + NIC", "Elastic IP (only if required) + ENI"],
        ["NVIDIA GPU Driver **Extension**", "AWS **GRID / RTX vWS** driver (or NVIDIA install)"],
        ["Quota: NV family vCPUs", "Quota: **G and VT** On-Demand vCPUs"],
    ], CONTENT_L, BODY_T, CONTENT_W, col_widths=[1, 1], size=13, row_h=Inches(0.62), highlight_rows=(0,))
    d.callout(s, "**A10 vs A10G:** same Ampere generation, 24 GB VRAM. A10G is the AWS data-center SKU. RTX in Omniverse is supported on both.",
              CONTENT_L, Inches(5.35), CONTENT_W, h=Inches(0.8), size=13)

    # 7 -- Launch AWS instance (console screenshot) -------------------------------
    s = d.content("Launch AWS instance", notes="""
We select the G5 family because it provides NVIDIA GPUs with RTX support.
AWS provides Windows Server images by default. Windows 11 needs a custom import.
Security Groups apply at the instance (ENI). NACLs apply at the subnet — use SG as the primary control, NACL as a coarse extra layer.""")
    d.picture_framed(s, ASSETS / "aws_launch_instance.png", CONTENT_L, BODY_T, w=CONTENT_W)

    # 7b -- G5 family table --------------------------------------------------------
    s = d.content("Launch AWS instance — G5 family (NVIDIA A10G)", notes="""
Every G5 size carries the same A10G GPU with 24 GB. Sizes differ in vCPU, host RAM and local NVMe.
g5.4xlarge is the recommended workstation: closest to Standard_NV18ads_A10_v5 and comfortable for Windows + Kit + CUDA.""")
    d.table(s, ["Instance", "GPUs", "vCPU", "RAM", "Local NVMe", "When to use"], [
        ["`g5.xlarge`", "1", "4", "16 GiB", "250 GB", "Too tight for Windows + Kit — avoid"],
        ["**`g5.2xlarge`**", "1", "8", "32 GiB", "450 GB", "Demo / Kit launch"],
        ["**`g5.4xlarge`**", "1", "16", "64 GiB", "600 GB", "**Recommended workstation**"],
        ["`g5.8xlarge`", "1", "32", "128 GiB", "900 GB", "Large USD assemblies"],
        ["`g5.16xlarge`", "1", "64", "256 GiB", "1900 GB", "Single GPU, max host RAM"],
        ["`g5.12xlarge`", "4", "48", "192 GiB", "3800 GB", "Multi-GPU (not needed for first Kit)"],
        ["`g5.24xlarge`", "4", "96", "384 GiB", "3800 GB", "Farm / batch"],
        ["`g5.48xlarge`", "8", "192", "768 GiB", "7600 GB", "Max A10G density"],
    ], CONTENT_L, BODY_T, CONTENT_W, col_widths=[1.5, 0.7, 0.7, 1.0, 1.1, 3.6], size=12,
        row_h=Inches(0.5), highlight_rows=(2,))
    d.text(s, "All sizes: NVIDIA **A10G** Tensor Core, 24 GB GDDR6 per GPU, RTX / ray tracing capable.",
           CONTENT_L, Inches(6.05), CONTENT_W, Inches(0.4), size=12, color=GRAY, align=PP_ALIGN.CENTER)

    # 7c -- Launch checklist -------------------------------------------------------
    s = d.content("Launch AWS instance — EC2 console checklist", notes="""
Walk the console top to bottom: AMI, instance type, network, storage, IAM, key pair.
Windows 11 is not a stock G5 AMI — if the customer mandates Win11, plan a VHD import (BYOL) before the workshop.""")
    d.bullets(s, [
        "**AMI**",
        ("Default marketplace: **Windows Server 2022 / 2025**.", 1),
        ("**Windows 11** is not a stock G5 AMI — import a custom VHD / AMI (BYOL) if the customer mandates Win11.", 1),
        ("Linux / headless Kit or Isaac: **NVIDIA Omniverse GPU-Optimized AMI** (`g5.2xlarge`+).", 1),
        "**Instance type:** `g5.4xlarge` (preferred) or `g5.2xlarge`.",
        "**Subnet:** private preferred; jump host or VPN for RDP.",
    ], l=CONTENT_L, t=BODY_T, w=HALF, size=13, kind="number", space_after=8)
    d.bullets(s, [
        "**Storage:** gp3 root **≥ 256 GB** (Kit + CUDA + USD). Instance store is ephemeral — do not keep projects only there.",
        "**IAM:** SSM Session Manager role for console access without opening 3389 to the internet.",
        "**Key pair:** required for Windows password decrypt (unless SSM + AD).",
    ], l=COL2_L, t=BODY_T, w=HALF, size=13, kind="number@4", space_after=8)
    d.callout(s, "**Security Groups** apply at the instance (ENI). **NACLs** apply at the subnet. Use the SG as the primary control and the NACL as a coarse extra layer.",
              COL2_L, Inches(4.3), HALF, h=Inches(1.1), size=12, label="Network controls")

    # 8 -- Security Group ----------------------------------------------------------
    s = d.content("Launch AWS instance — Security Group", notes="""
Access is controlled by the Security Group: which ports, and who may connect.
Never open RDP to 0.0.0.0/0. Prefer VPN / Direct Connect and a private IP.""")
    d.table(s, ["Direction", "Port", "Source / Destination", "Purpose"], [
        ["Inbound", "TCP **3389**", "Corporate CIDR only", "RDP"],
        ["Inbound", "TCP **22**", "Bastion / VPN only", "Linux SSH (if used)"],
        ["Inbound", "TCP **443**", "VPC / VPN", "Nucleus / HTTPS if co-located"],
        ["Outbound", "HTTPS **443**", "`0.0.0.0/0`", "CUDA, NGC, GitHub, Windows Update"],
    ], CONTENT_L, BODY_T, CONTENT_W, col_widths=[1.2, 1.3, 2.4, 3.2], size=13, row_h=Inches(0.6))
    d.callout(s, "**Never open RDP to `0.0.0.0/0`.** Prefer **VPN / Direct Connect + private IP**, or SSM Session Manager port-forwarding, with an MFA-protected jump host.",
              CONTENT_L, Inches(4.65), CONTENT_W, h=Inches(0.9), size=13, tone="amber")

    # 8b -- Drivers on G5 -----------------------------------------------------------
    s = d.content("Launch AWS instance — drivers on G5", notes="""
Drivers: AWS PowerShell scripts for a quick GRID setup, or a manual NVIDIA install as shown later.
For Omniverse RTX on Windows use the GRID / RTX Virtual Workstation branch, not the Tesla compute-only driver.""")
    d.text(s, "Two valid paths:", CONTENT_L, BODY_T, CONTENT_W, Inches(0.4), size=15)
    d.heading(s, "1 · AWS GRID driver  (recommended for Windows RTX / Omniverse desktop)", CONTENT_L, Inches(1.8), HALF)
    d.bullets(s, [
        "Follow **Install NVIDIA drivers on Windows** for **G5** (AWS docs).",
        "AWS publishes PowerShell helpers that pull the GRID package from S3.",
        "Reboot after install, then verify with `nvidia-smi`.",
    ], l=CONTENT_L, t=Inches(2.25), w=HALF, size=13, space_after=8)
    d.code(s, [
        "# PowerShell (Administrator) - G5 GRID driver",
        "$Bucket    = \"ec2-windows-nvidia-drivers\"",
        "$KeyPrefix = \"latest\"",
        "$Objects = Get-S3Object -BucketName $Bucket `",
        "             -KeyPrefix $KeyPrefix -Region us-east-1",
        "foreach ($o in $Objects) {",
        "  Copy-S3Object -BucketName $Bucket -Key $o.Key `",
        "    -LocalFile \"$home\\Desktop\\NVIDIA\\$($o.Key)\" `",
        "    -Region us-east-1",
        "}",
        "# run the downloaded installer, then Restart-Computer",
    ], CONTENT_L, Inches(3.75), HALF, size=10)
    d.heading(s, "2 · Manual NVIDIA package inside the OS", COL2_L, Inches(1.8), HALF)
    d.bullets(s, [
        "Same idea as the Azure “optional local install” slide.",
        "Download the **RTX Virtual Workstation (vWS)** / GRID branch for A10G — not Game Ready.",
        "Requires an NVIDIA account for the download.",
        "Reboot, then `nvidia-smi` must list **NVIDIA A10G**.",
    ], l=COL2_L, t=Inches(2.25), w=HALF, size=13, space_after=8)
    d.callout(s, "Keep **one** known-good combination per golden image: **G5 GRID driver + CUDA 13.2 + Kit build**. Snapshot the AMI once all three work.",
              COL2_L, Inches(4.55), HALF, h=Inches(1.0), size=12)

    # 9 -- GPU driver path -----------------------------------------------------------
    s = d.content("Launch virtual machine with NVIDIA GPU driver", notes="""
Standard_NV18ads_A10_v5 is a generation-5 VM on NVIDIA A10, suitable for RTX rendering. G5 A10G is the AWS counterpart.""")
    d.table(s, ["Cloud", "Mechanism"], [
        ["Azure", "VM extension **NVIDIA GPU Driver** (`Microsoft.HpcCompute` / `NvidiaGpuDriverWindows`)"],
        ["AWS G5", "**GRID / RTX Virtual Workstation** driver for graphics + RTX"],
    ], CONTENT_L, BODY_T, CONTENT_W, col_widths=[1, 5], size=14, row_h=Inches(0.7))
    d.bullets(s, [
        "Azure SKU in the original deck: `Standard_NV18ads_A10_v5` — gen-5 **A10**, RTX-capable.",
        "AWS SKU for the same class of work: **`g5.4xlarge`** — **A10G**, 24 GB.",
    ], l=CONTENT_L, t=Inches(3.6), w=CONTENT_W, size=14, space_after=10)

    # 10 -- NVIDIA GPU driver -----------------------------------------------------------
    s = d.content("NVIDIA GPU driver", notes="This is the optional in-guest driver path.")
    d.bullets(s, [
        "Optional / parallel path: install the NVIDIA GPU driver **inside** the VM (not only via the Azure extension).",
        "On AWS: after the GRID install, **reboot**, then verify with `nvidia-smi`.",
        "Pick the **graphics** branch (GRID / RTX vWS). A Tesla compute-only driver will not give you an RTX viewport.",
    ], l=CONTENT_L, t=Inches(1.8), w=CONTENT_W, size=16, space_after=14)
    d.heading(s, "Expected nvidia-smi header on a g5.4xlarge", CONTENT_L, Inches(3.9), CONTENT_W, size=14)
    d.code(s, [
        "+-----------------------------------------------------------------------------------------+",
        "| NVIDIA-SMI 5xx.xx        Driver Version: 5xx.xx        CUDA Version: 13.2               |",
        "|-----------------------------------------+------------------------+----------------------+",
        "| GPU  Name                  Driver-Model | Bus-Id          Disp.A | Volatile Uncorr. ECC |",
        "|   0  NVIDIA A10G                  WDDM  | 00000000:00:1E.0    On |                    0 |",
        "+-----------------------------------------+------------------------+----------------------+",
    ], CONTENT_L, Inches(4.3), CONTENT_W, size=10)

    # 11 -- Install NVIDIA driver and verify -----------------------------------------------
    s = d.content("Install NVIDIA driver", notes="""
Use the NVIDIA / AWS GRID driver first, then confirm with nvidia-smi.
If nvidia-smi fails: wrong driver branch (Tesla compute-only vs GRID graphics), incomplete install, or no reboot.""")
    d.text(s, "Use the **NVIDIA / AWS GRID driver first**, then confirm with **`nvidia-smi`**.",
           CONTENT_L, BODY_T, CONTENT_W, Inches(0.4), size=14)
    d.heading(s, "Verify", CONTENT_L, Inches(1.8), HALF)
    d.bullets(s, [
        "RDP to the instance.",
        "Open **Command Prompt** or **PowerShell as Administrator**.",
        "Run:",
    ], l=CONTENT_L, t=Inches(2.2), w=HALF, size=13, kind="number", space_after=6)
    d.code(s, ['cd "C:\\Program Files\\NVIDIA Corporation\\NVSMI"', "nvidia-smi"], CONTENT_L, Inches(3.55), HALF)
    d.text(s, "If `NVSMI` is not on that path (newer driver layouts), it is already on `PATH`:",
           CONTENT_L, Inches(4.45), HALF, Inches(0.4), size=12, color=INK_SOFT)
    d.code(s, ["nvidia-smi"], CONTENT_L, Inches(4.9), HALF)
    d.heading(s, "Expected", COL2_L, Inches(1.8), HALF)
    d.bullets(s, [
        "GPU name: **NVIDIA A10G** (AWS) or **A10** (Azure)",
        "Driver version listed",
        "`GPU-Util` may be `N/A` or `0%` with no workload — that is normal",
    ], l=COL2_L, t=Inches(2.2), w=HALF, size=13, space_after=8)
    d.callout(s, "Wrong driver branch (Tesla compute-only vs GRID graphics), incomplete install, or **no reboot**.",
              COL2_L, Inches(4.2), HALF, h=Inches(1.0), size=12, tone="amber", label="If nvidia-smi fails")

    # 12 -- Section: CUDA ---------------------------------------------------------------------
    d.divider("Install CUDA Toolkit")

    # 13 -- Install CUDA Toolkit ------------------------------------------------------------------
    s = d.content("Install CUDA Toolkit", notes="""
Download is a manual browser action (NVIDIA login). Do not expect this step in IaC.""")
    d.text(s, "CUDA Toolkit is required for RTX rendering, physics, and GPU compute workloads.",
           CONTENT_L, BODY_T, CONTENT_W, Inches(0.4), size=14)
    d.callout(s, "**Prerequisite:** NVIDIA account — sign-in is required to download the package.",
              CONTENT_L, Inches(1.85), HALF, h=Inches(0.65), size=13)
    d.heading(s, "Download", CONTENT_L, Inches(2.7), HALF)
    d.bullets(s, [
        "Open the CUDA downloads page: **Windows · x86_64 · Windows 11 or Windows Server · exe (local)**.",
        "Download **CUDA Toolkit 13.2** (same pin as the demo template).",
        "Run the installer **as Administrator**. Reboot if requested.",
    ], l=CONTENT_L, t=Inches(3.1), w=HALF, size=13, kind="number", space_after=8)
    d.heading(s, "Reference", COL2_L, Inches(1.85), HALF)
    tb, tf = textbox(s, COL2_L, Inches(2.25), HALF, Inches(0.8))
    p = tf.paragraphs[0]
    r = p.add_run()
    r.text = "developer.nvidia.com/cuda-downloads  (Windows · x86_64 · exe local)"
    r.font.name = FONT
    r.font.size = Pt(12)
    r.font.color.rgb = NV_GREEN_DARK
    r.hyperlink.address = ("https://developer.nvidia.com/cuda-downloads?target_os=Windows"
                           "&target_arch=x86_64&target_version=11&target_type=exe_local")
    d.callout(s, "The download is a **manual browser action** behind an NVIDIA login. Do not expect this step to be automated in IaC — bake it into the golden AMI instead.",
              COL2_L, Inches(3.1), HALF, h=Inches(1.1), size=12, tone="amber", label="Ops note")

    # 14 -- CUDA on the instance -------------------------------------------------------------------
    s = d.content("Install CUDA Toolkit — verify", notes="""
After install, confirm the compiler and the driver still agree. Keep one known-good combo: G5 GRID driver + CUDA 13.2 + Kit build.""")
    d.text(s, "After install, confirm compiler and driver still agree:", CONTENT_L, BODY_T, CONTENT_W, Inches(0.4), size=15)
    d.code(s, ["nvidia-smi", "where nvcc", "nvcc --version"], CONTENT_L, Inches(1.85), HALF, size=14)
    d.bullets(s, [
        "`nvidia-smi` → driver version and the **CUDA version the driver supports**",
        "`where nvcc` → `C:\\Program Files\\NVIDIA GPU Computing Toolkit\\CUDA\\v13.2\\bin\\nvcc.exe`",
        "`nvcc --version` → **release 13.2**",
    ], l=COL2_L, t=Inches(1.85), w=HALF, size=13, space_after=8)
    d.callout(s, "Keep **one** known-good combo: **G5 GRID driver + CUDA 13.2 + Kit build**. Do not mix random Game Ready drivers on a cloud GPU.",
              CONTENT_L, Inches(4.3), CONTENT_W, h=Inches(0.9), size=13)

    # 15 -- Section: Omniverse Kit ------------------------------------------------------------------
    d.divider("Omniverse Kit")

    # 16 -- Launch Omniverse Kit --------------------------------------------------------------------
    s = d.content("Launch Omniverse Kit", notes="""
Clone the kit-app-template, create an application from the template, build, launch.
Requires Git for Windows and a working GPU driver (nvidia-smi OK) before first launch.""")
    d.heading(s, "1 · Clone NVIDIA Omniverse kit-app-template", CONTENT_L, BODY_T, CONTENT_W)
    d.code(s, ["git clone https://github.com/NVIDIA-Omniverse/kit-app-template.git", "cd kit-app-template"],
           CONTENT_L, Inches(1.7), CONTENT_W, size=12)
    third_gap = Inches(0.3)
    THIRD = (CONTENT_W - 2 * third_gap) / 3
    for i, (label, cmd) in enumerate([
        ("2 · Create a new application from template", ".\\repo.bat template new"),
        ("3 · Build", ".\\repo.bat build"),
        ("4 · Launch", ".\\repo.bat launch"),
    ]):
        x = CONTENT_L + i * (THIRD + third_gap)
        d.heading(s, label, x, Inches(2.95), THIRD, size=14)
        d.code(s, [cmd], x, Inches(3.35), THIRD, size=12)
    d.callout(s, "Requires **Git for Windows** and a working GPU driver (`nvidia-smi` OK) before first launch. First build downloads the Kit SDK from NGC — allow outbound 443.",
              CONTENT_L, Inches(4.75), CONTENT_W, h=Inches(0.9), size=13)

    # 17 -- Kit first-run wizard --------------------------------------------------------------------
    s = d.content("Launch Omniverse Kit — first-run wizard", notes="""
This is the first-run template wizard. Defaults are recommended for a first successful launch.""")
    d.text(s, "Complete the **initial setup** of the Kit application:", CONTENT_L, BODY_T, CONTENT_W, Inches(0.4), size=15)
    d.bullets(s, [
        "Accept **license and consent**.",
        "**Create Application**.",
        "Set:",
        ("application name", 1),
        ("`.kit` file name", 1),
        ("display name", 1),
        ("application version", 1),
        ("Leave remaining options at **defaults** for the first setup.", 0, "number@4"),
    ], l=CONTENT_L, t=Inches(1.9), w=HALF + Inches(1), size=14, kind="number", space_after=10)
    d.callout(s, "Defaults are recommended for a first successful launch. Customise the `.kit` file and extensions only after the UI has loaded once.",
              COL2_L + Inches(1), Inches(1.9), HALF - Inches(1), h=Inches(1.2), size=12, label="Recommendation")

    # 18 -- Kit running -----------------------------------------------------------------------------
    s = d.content("Launch Omniverse Kit — UI loaded", notes="""
From here we work with USD, extensions, RTX, or Nucleus. Nucleus is a separate service (often a CPU instance + persistent disk), not something to co-host on the GPU workstation unless this is a tiny lab.""")
    d.text(s, "UI load confirms:", CONTENT_L, BODY_T, CONTENT_W, Inches(0.4), size=15)
    d.bullets(s, [
        "the application was **created successfully**",
        "the **Kit runtime** is working",
        "the environment is ready for **USD scenes, extensions, and RTX**",
        "next step: connect to **Enterprise Nucleus** for collaboration",
    ], l=CONTENT_L, t=Inches(1.9), w=HALF + Inches(1), size=15, space_after=12)
    d.callout(s, "Nucleus is a **separate service** — typically a CPU instance with a persistent EBS volume and backups. Do not co-host it on the GPU workstation except for a tiny lab.",
              COL2_L + Inches(1), Inches(1.9), HALF - Inches(1), h=Inches(1.4), size=12, tone="amber", label="Nucleus placement")

    # 19 -- Section: References -----------------------------------------------------------------------
    d.divider("References")

    # 20 -- References ----------------------------------------------------------------------------------
    s = d.content("References")
    d.table(s, ["Topic", "Link"], [
        ["CUDA downloads (Win x64, local exe)", "https://developer.nvidia.com/cuda-downloads?target_os=Windows&target_arch=x86_64&target_version=11&target_type=exe_local"],
        ["Omniverse Kit (NGC)", "https://catalog.ngc.nvidia.com/orgs/nvidia/teams/omniverse/collections/kit"],
        ["Enterprise Nucleus Server", "https://catalog.ngc.nvidia.com/orgs/nvidia/teams/omniverse/collections/enterprise-nucleus/artifacts"],
        ["kit-app-template", "https://github.com/NVIDIA-Omniverse/kit-app-template"],
        ["EC2 G5 (A10G)", "https://aws.amazon.com/ec2/instance-types/g5/"],
        ["On-Demand G / VT quota", "https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-on-demand-instances.html"],
        ["NVIDIA drivers on Windows EC2", "https://docs.aws.amazon.com/AWSEC2/latest/WindowsGuide/install-nvidia-driver.html"],
        ["Azure N-series Windows drivers", "https://learn.microsoft.com/en-us/azure/virtual-machines/windows/n-series-driver-setup"],
    ], CONTENT_L, BODY_T, CONTENT_W, col_widths=[2.2, 6], size=11, row_h=Inches(0.5), links_col=1)

    # 21 -- Close -------------------------------------------------------------------------------------
    d.divider("Thank you")

    # A1 -- Ops appendix ------------------------------------------------------------------------------
    s = d.content("Appendix — running this in production", notes="""
Use this if the customer asks “how would we run this in production?”""")
    d.bullets(s, [
        "**Quota first**, then AMI, then instance. IaC cannot skip Service Quotas.",
        "**Pin** Region + AZ with G5 capacity; consider a **Capacity Reservation** for a workshop date.",
        "**Stop** G5 when idle — A10G On-Demand is expensive. Instance store is wiped on stop — keep USD on **EBS**.",
        "**Nucleus** on a non-GPU instance with backups; Kit clients on G5.",
        "**Do not** put RDP on a public IP without CIDR lock + MFA jump host.",
        "Snapshot / AMI the golden image **after** GRID + CUDA 13.2 + Kit build succeed.",
    ], l=CONTENT_L, t=Inches(1.6), w=CONTENT_W, size=15, space_after=14)

    # A2 -- First-run validation checklist --------------------------------------------------------------
    s = d.content("Appendix — first-run validation checklist", notes="""
Run through this list before handing the instance to a user. Every line maps to one slide earlier in the deck.""")
    d.bullets(s, [
        "`Running On-Demand G and VT instances` quota ≥ instance vCPUs in the target Region",
        "Instance is `g5.2xlarge` or `g5.4xlarge` and `running`",
        "SG: RDP only from corp / VPN",
        "GRID driver installed; reboot done",
    ], l=CONTENT_L, t=Inches(1.6), w=HALF, size=14, kind="check", space_after=14)
    d.bullets(s, [
        "`nvidia-smi` shows **A10G**",
        "CUDA Toolkit **13.2**; `nvcc --version`",
        "`kit-app-template` cloned; `.\\repo.bat build` / `launch` succeeds",
        "Kit UI loads; RTX viewport available",
    ], l=COL2_L, t=Inches(1.6), w=HALF, size=14, kind="check", space_after=14)

    out = d.save()
    print(f"wrote {out} ({d.n} slides)")


if __name__ == "__main__":
    build()
