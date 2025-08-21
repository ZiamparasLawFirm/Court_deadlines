
from __future__ import annotations
from typing import List
from datetime import datetime
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
import os

from .calculators import DeadlineItem

GREEK_FONT_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "DejaVuSans.ttf")

def _ensure_font() -> str:
    if os.path.exists(GREEK_FONT_PATH):
        if "DejaVuSans" not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont("DejaVuSans", GREEK_FONT_PATH))
        return "DejaVuSans"
    return "Helvetica"

def make_pdf(path: str, title: str, meta: dict, rows: List[DeadlineItem]) -> None:
    font = _ensure_font()
    c = canvas.Canvas(path, pagesize=A4)
    width, height = A4
    margin = 18 * mm
    x = margin
    y = height - margin

    c.setFont(font, 14)
    c.drawString(x, y, title); y -= 8 * mm

    c.setFont(font, 10)
    c.drawString(x, y, f"Πελάτης: {meta.get('client','-')}"); y -= 5 * mm
    c.drawString(x, y, f"Αντίδικος: {meta.get('opponent','-')}"); y -= 5 * mm
    c.drawString(x, y, f"Δικαστήριο: {meta.get('court','-')}"); y -= 8 * mm

    headers = ["#", "Ενέργεια", "Νομική βάση", "Ημερομηνία", "Ημέρα", "Σημείωση"]
    col_widths = [10*mm, 70*mm, 35*mm, 25*mm, 25*mm, 40*mm]

    c.setFont(font, 9)
    c.rect(x, y-6*mm, sum(col_widths), 6*mm, stroke=1, fill=0)
    cx = x + 2
    for i, h in enumerate(headers):
        c.drawString(cx, y-4*mm, h)
        cx += col_widths[i]
    y -= 6*mm

    for it in rows:
        if y < margin + 20*mm:
            c.showPage()
            y = height - margin
            c.setFont(font, 9)
            c.rect(x, y-6*mm, sum(col_widths), 6*mm, stroke=1, fill=0)
            cx = x + 2
            for i, h in enumerate(headers):
                c.drawString(cx, y-4*mm, h)
                cx += col_widths[i]
            y -= 6*mm

        c.rect(x, y-10*mm, sum(col_widths), 10*mm, stroke=1, fill=0)
        cx = x + 2
        vals = [str(it.step), it.action, it.legal_basis, it.deadline.strftime("%d-%m-%Y"), it.weekday, it.note or ""]
        for i, v in enumerate(vals):
            c.drawString(cx, y-7*mm, v[:60])
            cx += col_widths[i]
        y -= 10*mm

    c.setFont(font, 8)
    c.drawString(x, margin, f"Generated: {datetime.now():%Y-%m-%d %H:%M}")
    if font == "Helvetica":
        c.drawString(x, margin+10, "⚠ Προσθέστε assets/DejaVuSans.ttf για σωστή εμφάνιση ελληνικών.")
    c.save()
