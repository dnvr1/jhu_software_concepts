"""Build the required two-paragraph reflection as a polished PDF."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


OUTPUT = Path(__file__).with_name("limitations.pdf")

NAVY = colors.HexColor("#15304A")
BLUE = colors.HexColor("#2878B5")
PALE_BLUE = colors.HexColor("#EAF3F9")
DARK = colors.HexColor("#1F2933")
MUTED = colors.HexColor("#65737E")
LINE = colors.HexColor("#D6E0E6")
WHITE = colors.white


PARAGRAPH_ONE = (
    "The 30,006 records in this database are a self-selected collection, not "
    "a random sample of graduate applicants. People decide for themselves "
    "whether to use GradCafe, which schools and programs to report, and "
    "whether an acceptance, rejection, waitlist, or unusually surprising "
    "result is worth posting. Applicants who never visit the site, prefer not "
    "to share an outcome, or come from communities where GradCafe is less "
    "commonly used are absent. Missing nationality and status values further "
    "change the denominator for a calculation. For example, the database "
    "shows a 38.53% acceptance percentage for 15,449 American Fall 2026 "
    "entries and 34.59% for 13,499 international entries. Those percentages "
    "accurately summarize the classified entries stored here, but they do not "
    "establish the acceptance rates of either applicant population. The "
    "difference could reflect which applicants post, the programs they apply "
    "to, or which outcomes they choose to disclose. The university submission "
    "rankings have the same limitation: high counts can indicate greater use "
    "of this website rather than greater application volume in the real world."
)

PARAGRAPH_TWO = (
    "Anonymous self-reporting also limits reliability because no admissions "
    "office verifies the scores, labels, dates, or outcomes. In the current "
    "analysis, the stored values produce an average GRE Quantitative score of "
    "260.47 and an average Analytical Writing score of 8.34. These results are "
    "warning signs that some entries may use incompatible score scales, place "
    "a combined score in a component field, or contain typing and parsing "
    "errors. Missingness compounds the problem: SQL averages each metric over "
    "only the rows that supply that metric, so GPA, Quantitative, Verbal, and "
    "Writing averages have different underlying groups even when they appear "
    "together in one result. Cleaning and LLM-generated program or university "
    "names can make text more consistent, but they cannot confirm that a score "
    "or admission decision is true. The reported averages are therefore "
    "mathematically correct for the non-NULL values in this database while "
    "remaining weak estimates of the broader applicant population. A careful "
    "analysis should report denominators, inspect score ranges, test how results "
    "change after questionable values are excluded, and describe these figures "
    "as patterns in GradCafe submissions rather than population statistics."
)


def page_decoration(canvas, document) -> None:
    """Draw a restrained footer and page number."""
    canvas.saveState()
    canvas.setStrokeColor(LINE)
    canvas.line(0.72 * inch, 0.58 * inch, 7.78 * inch, 0.58 * inch)
    canvas.setFillColor(MUTED)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(0.72 * inch, 0.38 * inch, "Denver Clarke | EN.605.256")
    canvas.drawRightString(
        7.78 * inch,
        0.38 * inch,
        f"Module 3 | Page {document.page}",
    )
    canvas.restoreState()


def build_pdf(output: Path = OUTPUT) -> Path:
    """Create the reflection PDF and return its path."""
    output.parent.mkdir(parents=True, exist_ok=True)
    document = SimpleDocTemplate(
        str(output),
        pagesize=letter,
        leftMargin=0.72 * inch,
        rightMargin=0.72 * inch,
        topMargin=0.68 * inch,
        bottomMargin=0.78 * inch,
        title="Data Limitations Reflection",
        author="Denver Clarke",
        subject="Module 3 analysis of anonymous self-reported data",
    )
    base = getSampleStyleSheet()
    kicker = ParagraphStyle(
        "Kicker",
        parent=base["Normal"],
        textColor=BLUE,
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        spaceAfter=8,
        uppercase=True,
    )
    title = ParagraphStyle(
        "Title",
        parent=base["Title"],
        textColor=NAVY,
        fontName="Helvetica-Bold",
        fontSize=27,
        leading=31,
        alignment=0,
        spaceAfter=8,
    )
    subtitle = ParagraphStyle(
        "Subtitle",
        parent=base["Normal"],
        textColor=MUTED,
        fontSize=10,
        leading=15,
        spaceAfter=18,
    )
    heading = ParagraphStyle(
        "Heading",
        parent=base["Heading2"],
        textColor=NAVY,
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        spaceBefore=12,
        spaceAfter=6,
    )
    body = ParagraphStyle(
        "Body",
        parent=base["BodyText"],
        textColor=DARK,
        fontName="Helvetica",
        fontSize=9.6,
        leading=14.2,
        spaceAfter=4,
    )
    stat_label = ParagraphStyle(
        "StatLabel",
        parent=base["Normal"],
        textColor=MUTED,
        fontName="Helvetica-Bold",
        fontSize=7.2,
        leading=9,
    )
    stat_value = ParagraphStyle(
        "StatValue",
        parent=base["Normal"],
        textColor=NAVY,
        fontName="Helvetica-Bold",
        fontSize=15,
        leading=18,
    )

    statistics = Table(
        [
            [
                Paragraph("AMERICAN ACCEPTED", stat_label),
                Paragraph("INTERNATIONAL ACCEPTED", stat_label),
                Paragraph("GRE QUANTITATIVE MEAN", stat_label),
            ],
            [
                Paragraph("38.53%", stat_value),
                Paragraph("34.59%", stat_value),
                Paragraph("260.47", stat_value),
            ],
        ],
        colWidths=[2.30 * inch, 2.30 * inch, 2.30 * inch],
    )
    statistics.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE_BLUE),
                ("BOX", (0, 0), (-1, -1), 0.75, BLUE),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, LINE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, 0), 9),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 2),
                ("TOPPADDING", (0, 1), (-1, 1), 2),
                ("BOTTOMPADDING", (0, 1), (-1, 1), 9),
            ]
        )
    )

    story = [
        Paragraph("MODULE 3 | WRITTEN REFLECTION", kicker),
        Paragraph("Limits of self-reported applicant data", title),
        Paragraph(
            "What the database mathematically contains is narrower than what "
            "it can support as a conclusion about graduate applicants.",
            subtitle,
        ),
        statistics,
        Spacer(1, 0.08 * inch),
        Paragraph("Selection and representation", heading),
        Paragraph(PARAGRAPH_ONE, body),
        Paragraph("Missingness and reliability", heading),
        Paragraph(PARAGRAPH_TWO, body),
    ]
    document.build(
        story,
        onFirstPage=page_decoration,
        onLaterPages=page_decoration,
    )
    return output


if __name__ == "__main__":
    print(f"Created {build_pdf()}")
