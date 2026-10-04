"""Render the completed Markdown checklist as the single Gradescope PDF."""

from __future__ import annotations

import re
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "reports" / "module_6_submission.md"
OUTPUT = ROOT / "reports" / "module_6_submission.pdf"


def inline(text: str) -> str:
    replacements = {"—": "-", "→": " to ", "€": "EUR ", "–": "-", "’": "'"}
    for old, new in replacements.items():
        text = text.replace(old, new)
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`(.+?)`", r"<font name='Courier'>\1</font>", text)
    text = re.sub(r"\[(.+?)\]\((.+?)\)", r"<link href='\2'>\1</link>", text)
    return text


def page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Helvetica", 8)
    canvas.drawString(0.65 * inch, 0.4 * inch, "DSO 576 - Spotify Financial Data Cleaning")
    canvas.drawRightString(7.85 * inch, 0.4 * inch, f"Page {doc.page}")
    canvas.restoreState()


def build() -> None:
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name="TitleCentered", parent=styles["Title"], alignment=TA_CENTER, spaceAfter=14))
    styles.add(ParagraphStyle(name="Small", parent=styles["BodyText"], fontSize=8, leading=10))
    styles["BodyText"].leading = 13
    styles["BodyText"].spaceAfter = 7
    styles["Heading2"].spaceBefore = 12
    styles["Heading3"].spaceBefore = 9
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        rightMargin=0.6 * inch,
        leftMargin=0.6 * inch,
        topMargin=0.55 * inch,
        bottomMargin=0.6 * inch,
        title="DSO 576 Module 6 - Spotify Financial Data Cleaning",
        author="[YOUR NAME]",
    )

    lines = SOURCE.read_text(encoding="utf-8").splitlines()
    story = []
    i = 0
    first_heading = True
    while i < len(lines):
        line = lines[i].strip()
        if not line:
            i += 1
            continue
        if line.startswith("|"):
            block = []
            while i < len(lines) and lines[i].strip().startswith("|"):
                cells = [c.strip() for c in lines[i].strip().strip("|").split("|")]
                block.append(cells)
                i += 1
            if len(block) > 1 and all(set(c.replace(":", "").replace("-", "")) == set() for c in block[1]):
                block.pop(1)
            data = [[Paragraph(inline(c), styles["Small"]) for c in row] for row in block]
            widths = [doc.width / len(data[0])] * len(data[0])
            table = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
            table.setStyle(
                TableStyle(
                    [
                        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#D9EAD3")),
                        ("GRID", (0, 0), (-1, -1), 0.35, colors.grey),
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 4),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
                    ]
                )
            )
            story.extend([table, Spacer(1, 8)])
            continue
        if line.startswith("# "):
            if not first_heading:
                story.append(PageBreak())
            story.append(Paragraph(inline(line[2:]), styles["TitleCentered"]))
            first_heading = False
        elif line.startswith("## "):
            story.append(Paragraph(inline(line[3:]), styles["Heading2"]))
        elif line.startswith("### "):
            story.append(Paragraph(inline(line[4:]), styles["Heading3"]))
        elif line.startswith("- "):
            story.append(Paragraph(inline(line[2:]), styles["BodyText"], bulletText="-"))
        else:
            story.append(Paragraph(inline(line.rstrip("  ")), styles["BodyText"]))
        i += 1

    doc.build(story, onFirstPage=page_number, onLaterPages=page_number)
    print(f"Wrote {OUTPUT}")


if __name__ == "__main__":
    build()
