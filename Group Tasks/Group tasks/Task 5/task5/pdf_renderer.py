from pathlib import Path
from html import escape
import re
import textwrap
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, letter, landscape
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from .schemas import ReportStyle

FONT_DIR = Path(__file__).parent / "fonts"


def fonts(family):
    base = {"sans": "DejaVuSans", "serif": "DejaVuSerif", "mono": "DejaVuSansMono"}[family]
    for name in [base, base + "-Bold"]:
        if name not in pdfmetrics.getRegisteredFontNames():
            pdfmetrics.registerFont(TTFont(name, str(FONT_DIR / (name + ".ttf"))))
    return base, base + "-Bold"


def safe_text(value):
    text = str(value or "")
    text = "".join(c for c in text if ord(c) >= 32 or c in "\n\t")
    if re.search(r"[\u0600-\u06ff]", text):
        import arabic_reshaper
        from bidi.algorithm import get_display
        text = get_display(arabic_reshaper.reshape(text))
    return escape(text).replace("\n", "<br/>")


def render_pdf(path: Path, title: str, question: str, result: dict, style: ReportStyle):
    normal, bold = fonts(style.font)
    page = A4 if style.page_size == "A4" else letter
    if style.orientation == "landscape":
        page = landscape(page)
    body = ParagraphStyle("body", fontName=normal, fontSize=style.body_size,
                          leading=style.body_size * style.line_height, spaceAfter=style.spacing,
                          splitLongWords=True, wordWrap="CJK")
    heading = ParagraphStyle("head", parent=body, fontName=bold if style.emphasis == "bold" else normal,
                             fontSize=style.heading_size, leading=style.heading_size * 1.2,
                             textColor=colors.HexColor(style.color), keepWithNext=True)
    sub = ParagraphStyle("sub", parent=heading, fontSize=style.body_size + 2, leading=style.body_size + 6)
    story = [Paragraph(safe_text(title), heading), Paragraph(safe_text("Question: " + question), body)]
    def section(label, text):
        if text:
            story.append(Paragraph(label, sub))
            # Split paragraphs before bidi conversion to keep Arabic blocks readable.
            for block in str(text).split("\n\n"):
                # Bound paragraph size so keepWithNext headings cannot push an
                # entire multi-page paragraph onto a mostly empty next page.
                for piece in textwrap.wrap(block, width=1000, replace_whitespace=False,
                                           drop_whitespace=False, break_on_hyphens=False) or [""]:
                    paragraph_style = body
                    if re.search(r"[\u0600-\u06ff]", piece):
                        paragraph_style = ParagraphStyle("arabic", parent=body, fontName=fonts("sans")[0], alignment=2)
                    story.append(Paragraph(safe_text(piece), paragraph_style))
    section("Answer", result.get("answer"))
    section("Analysis", result.get("analysis"))
    results = result.get("results") or {}
    for label in ["calculation", "stats", "comparison"]:
        if results.get(label):
            import json
            section(label.title(), json.dumps(results[label], ensure_ascii=False, indent=2))
    rows = results.get("table") or []
    if rows:
        story.append(Paragraph("Results", sub))
        # Two-column field/value form handles arbitrarily wide source records.
        table_data = [[Paragraph("Field", sub), Paragraph("Value", sub)]]
        for i, row in enumerate(rows[:200], 1):
            for key, value in row.items():
                table_data.append([Paragraph(safe_text(f"{i}. {key}"), body), Paragraph(safe_text(value), body)])
        usable = page[0] - 2 * style.margin
        table = LongTable(table_data, colWidths=[usable * .30, usable * .70], repeatRows=1, splitInRow=1)
        table.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), .4, colors.lightgrey),
                                   ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#EAF0F5")),
                                   ("VALIGN", (0, 0), (-1, -1), "TOP"),
                                   ("LEFTPADDING", (0, 0), (-1, -1), 7),
                                   ("RIGHTPADDING", (0, 0), (-1, -1), 7)]))
        story.append(table)
        if len(rows) > 200:
            story.append(Paragraph("Only the first 200 source rows are included in this report.", body))
    if result.get("sources"):
        story.append(Paragraph("Sources", sub))
        for s in result["sources"]:
            story.append(Paragraph(safe_text(f'{s.get("document", "source")}, p. {s.get("page", 1)}'), body))
    section("Limitations", "\n".join(str(w) for w in result.get("warnings", [])))
    if not result.get("enough_evidence", False):
        section("Evidence status", "Available evidence was not confirmed sufficient. Verify conclusions against source documents.")
    def footer(canvas, doc):
        canvas.setFont(normal, 8)
        canvas.setFillColor(colors.grey)
        canvas.drawString(style.margin, 18, "Document Intelligence | Generated application output")
        canvas.drawRightString(page[0] - style.margin, 18, str(doc.page))
    path.parent.mkdir(parents=True, exist_ok=True)
    SimpleDocTemplate(str(path), pagesize=page, leftMargin=style.margin, rightMargin=style.margin,
                      topMargin=style.margin, bottomMargin=style.margin,
                      title=title, author="Document Intelligence").build(story, onFirstPage=footer, onLaterPages=footer)
