"""Build the Module 3 SQL analysis PDF from verified queries and results."""

from __future__ import annotations

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    Preformatted,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from query_data import (
    QUESTION_1,
    QUESTION_2,
    QUESTION_3,
    QUESTION_4,
    QUESTION_5,
    QUESTION_6,
    QUESTION_7,
    QUESTION_8,
    QUESTION_9,
    QUESTION_10,
    QUESTION_11,
    SQL_QUESTION_1,
    SQL_QUESTION_2,
    SQL_QUESTION_3,
    SQL_QUESTION_4,
    SQL_QUESTION_5,
    SQL_QUESTION_6,
    SQL_QUESTION_7,
    SQL_QUESTION_8,
    SQL_QUESTION_9,
    SQL_QUESTION_10,
    SQL_QUESTION_11,
)


OUTPUT = Path(__file__).with_name("query_results.pdf")

NAVY = colors.HexColor("#15304A")
BLUE = colors.HexColor("#2878B5")
PALE_BLUE = colors.HexColor("#EAF3F9")
LIGHT_GRAY = colors.HexColor("#F4F6F8")
MID_GRAY = colors.HexColor("#667481")
DARK = colors.HexColor("#1F2933")
WHITE = colors.white


ANALYSES = [
    {
        "number": 1,
        "question": QUESTION_1,
        "result": ["Fall 2026 applicant count: 29,586"],
        "sql": SQL_QUESTION_1,
        "explanation": (
            "The query normalizes capitalization and surrounding whitespace "
            "in the term field, retains only Fall 2026 entries, and counts "
            "the resulting rows."
        ),
    },
    {
        "number": 2,
        "question": QUESTION_2,
        "result": ["Percent international: 46.34%"],
        "sql": SQL_QUESTION_2,
        "explanation": (
            "The numerator counts rows classified as international. The "
            "denominator counts every nonblank nationality classification, "
            "including American and Other, while excluding NULL and blank "
            "values. NULLIF prevents division by zero."
        ),
    },
    {
        "number": 3,
        "question": QUESTION_3,
        "result": [
            "Average GPA: 3.80",
            "Average GRE Quantitative: 260.47",
            "Average GRE Verbal: 161.53",
            "Average GRE Analytical Writing: 8.34",
        ],
        "sql": SQL_QUESTION_3,
        "explanation": (
            "Each AVG operates on one column and automatically ignores NULL "
            "values in that column. A row can therefore contribute to one "
            "average even when its other metrics are missing. The unusually "
            "high GRE results reflect the stored self-reported values; the "
            "assignment does not specify an additional score-range filter."
        ),
    },
    {
        "number": 4,
        "question": QUESTION_4,
        "result": ["Average GPA, American Fall 2026 applicants: 3.79"],
        "sql": SQL_QUESTION_4,
        "explanation": (
            "The query simultaneously requires Fall 2026, an American "
            "classification, and a supplied GPA. AVG then calculates the "
            "mean only for rows that satisfy all three conditions."
        ),
    },
    {
        "number": 5,
        "question": QUESTION_5,
        "result": ["Fall 2025 acceptance percentage: 47.92%"],
        "sql": SQL_QUESTION_5,
        "explanation": (
            "The WHERE clause establishes all Fall 2025 entries as the "
            "denominator. A filtered count selects accepted rows for the "
            "numerator, and NULLIF protects an empty term group."
        ),
    },
    {
        "number": 6,
        "question": QUESTION_6,
        "result": ["Average GPA, accepted Fall 2026 applicants: 3.79"],
        "sql": SQL_QUESTION_6,
        "explanation": (
            "The query filters for Fall 2026 acceptances with a non-NULL GPA "
            "and averages the GPA values in that subset."
        ),
    },
    {
        "number": 7,
        "question": QUESTION_7,
        "result": ["JHU Computer Science master's applicant count: 8"],
        "sql": SQL_QUESTION_7,
        "explanation": (
            "This query uses only the original program and degree fields. It "
            "recognizes the full Johns Hopkins University name or the JHU "
            "abbreviation, requires Computer Science in the combined program "
            "text, and accepts common master's degree labels."
        ),
    },
    {
        "number": 8,
        "question": QUESTION_8,
        "result": ["Original-field count: 28"],
        "sql": SQL_QUESTION_8,
        "explanation": (
            "The query applies every required restriction at once: Fall "
            "2026, accepted status, a PhD label, Computer Science in the "
            "original program field, and one of the four listed universities."
        ),
    },
    {
        "number": 9,
        "question": QUESTION_9,
        "result": [
            "Original-field count: 28",
            "LLM-field count: 28",
            "Difference: +0",
        ],
        "sql": SQL_QUESTION_9,
        "explanation": (
            "This query retains the original term, degree, and status fields "
            "but replaces the original combined program matching with the "
            "LLM-generated program and university fields. Both methods match "
            "the same 28 URLs because the original names in this subset were "
            "already recognizable and the standardized fields preserved them."
        ),
    },
    {
        "number": 10,
        "question": QUESTION_10,
        "result": [
            "American: 15,449 entries, 38.53% accepted (5,952 acceptances)",
            (
                "International: 13,499 entries, 34.59% accepted "
                "(4,669 acceptances)"
            ),
        ],
        "sql": SQL_QUESTION_10,
        "explanation": (
            "The query filters to Fall 2026 American and international "
            "entries, groups them by classification, and divides each group's "
            "accepted count by its total count. These are dataset percentages, "
            "not estimates of population admission rates."
        ),
    },
    {
        "number": 11,
        "question": QUESTION_11,
        "result": [
            "1. Stanford University: 718 entries, 19.08% accepted",
            (
                "2. University of California, Berkeley: 615 entries, "
                "25.20% accepted"
            ),
            "3. Yale University: 573 entries, 14.14% accepted",
            "4. Princeton University: 556 entries, 20.86% accepted",
            (
                "5. University of Washington: 547 entries, "
                "27.97% accepted"
            ),
        ],
        "sql": SQL_QUESTION_11,
        "explanation": (
            "The query filters to Fall 2026 and usable standardized university "
            "names, groups entries case-insensitively by university, and ranks "
            "the groups by entry count. Each acceptance percentage uses that "
            "university's displayed entry count as its denominator."
        ),
    },
]


def build_styles() -> dict[str, ParagraphStyle]:
    """Create the report's compact visual hierarchy."""
    base = getSampleStyleSheet()
    return {
        "cover_label": ParagraphStyle(
            "CoverLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=BLUE,
            spaceAfter=14,
            alignment=TA_CENTER,
        ),
        "cover_title": ParagraphStyle(
            "CoverTitle",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=30,
            leading=35,
            textColor=NAVY,
            alignment=TA_CENTER,
            spaceAfter=12,
        ),
        "cover_subtitle": ParagraphStyle(
            "CoverSubtitle",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=13,
            leading=18,
            textColor=MID_GRAY,
            alignment=TA_CENTER,
            spaceAfter=30,
        ),
        "eyebrow": ParagraphStyle(
            "Eyebrow",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=11,
            textColor=BLUE,
            spaceAfter=7,
        ),
        "question": ParagraphStyle(
            "Question",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=17,
            leading=22,
            textColor=NAVY,
            spaceAfter=16,
        ),
        "section": ParagraphStyle(
            "Section",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=13,
            textColor=NAVY,
            spaceBefore=12,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9.5,
            leading=14,
            textColor=DARK,
            spaceAfter=8,
        ),
        "result": ParagraphStyle(
            "Result",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=10,
            leading=15,
            textColor=NAVY,
            leftIndent=2,
        ),
        "code": ParagraphStyle(
            "Code",
            parent=base["Code"],
            fontName="Courier",
            fontSize=7.2,
            leading=9.1,
            textColor=DARK,
            backColor=LIGHT_GRAY,
            borderColor=colors.HexColor("#D8DEE4"),
            borderWidth=0.5,
            borderPadding=8,
            spaceAfter=7,
        ),
        "meta_label": ParagraphStyle(
            "MetaLabel",
            parent=base["Normal"],
            fontName="Helvetica-Bold",
            fontSize=9,
            leading=12,
            textColor=MID_GRAY,
        ),
        "meta_value": ParagraphStyle(
            "MetaValue",
            parent=base["Normal"],
            fontName="Helvetica",
            fontSize=9,
            leading=12,
            textColor=DARK,
        ),
    }


def draw_first_page(canvas, document) -> None:
    """Draw a quiet footer on the cover page."""
    canvas.saveState()
    canvas.setFillColor(MID_GRAY)
    canvas.setFont("Helvetica", 8)
    canvas.drawCentredString(
        letter[0] / 2,
        0.36 * inch,
        "Module 3 - Database Queries",
    )
    canvas.restoreState()


def draw_later_pages(canvas, document) -> None:
    """Draw consistent headers and page numbers."""
    canvas.saveState()
    width, height = letter
    canvas.setFillColor(NAVY)
    canvas.rect(0, height - 0.42 * inch, width, 0.42 * inch, fill=1, stroke=0)
    canvas.setFillColor(WHITE)
    canvas.setFont("Helvetica-Bold", 8)
    canvas.drawString(
        0.65 * inch,
        height - 0.27 * inch,
        "EN.605.256  |  Module 3 SQL Analysis",
    )
    canvas.setFillColor(MID_GRAY)
    canvas.setFont("Helvetica", 8)
    canvas.drawRightString(
        width - 0.65 * inch,
        0.34 * inch,
        f"Denver Clarke  |  Page {document.page}",
    )
    canvas.setStrokeColor(colors.HexColor("#D8DEE4"))
    canvas.line(
        0.65 * inch,
        0.48 * inch,
        width - 0.65 * inch,
        0.48 * inch,
    )
    canvas.restoreState()


def result_box(lines: list[str], styles: dict[str, ParagraphStyle]) -> Table:
    """Create a shaded result block with a blue accent edge."""
    paragraphs = [Paragraph(line, styles["result"]) for line in lines]
    content = Table(
        [[paragraph] for paragraph in paragraphs],
        colWidths=[6.23 * inch],
    )
    content.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), PALE_BLUE),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, 0), 8),
                ("BOTTOMPADDING", (0, -1), (-1, -1), 8),
                ("TOPPADDING", (0, 1), (-1, -1), 2),
                ("BOTTOMPADDING", (0, 0), (-1, -2), 2),
            ]
        )
    )
    box = Table([["", content]], colWidths=[0.08 * inch, 6.23 * inch])
    box.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (0, 0), BLUE),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    return box


def build_pdf() -> None:
    """Render the verified analysis as a letter-sized PDF."""
    styles = build_styles()
    document = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=letter,
        rightMargin=0.65 * inch,
        leftMargin=0.65 * inch,
        topMargin=0.66 * inch,
        bottomMargin=0.62 * inch,
        title="Module 3 SQL Query Results",
        author="Denver Clarke",
        subject="PostgreSQL analysis of GradCafe applicant entries",
    )

    story = [
        Spacer(1, 1.15 * inch),
        Paragraph("EN.605.256  |  MODERN SOFTWARE CONCEPTS", styles["cover_label"]),
        Paragraph("Database Query Results", styles["cover_title"]),
        Paragraph(
            "Raw PostgreSQL analysis of 30,006 GradCafe entries",
            styles["cover_subtitle"],
        ),
    ]

    metadata = Table(
        [
            [
                Paragraph("STUDENT", styles["meta_label"]),
                Paragraph("Denver Clarke (dclar106)", styles["meta_value"]),
            ],
            [
                Paragraph("DATABASE", styles["meta_label"]),
                Paragraph("PostgreSQL 17 / gradcafe", styles["meta_value"]),
            ],
            [
                Paragraph("SNAPSHOT", styles["meta_label"]),
                Paragraph("30,006 unique applicant URLs", styles["meta_value"]),
            ],
            [
                Paragraph("VALIDATED", styles["meta_label"]),
                Paragraph("September 17, 2026", styles["meta_value"]),
            ],
        ],
        colWidths=[1.25 * inch, 4.5 * inch],
        hAlign="CENTER",
    )
    metadata.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), LIGHT_GRAY),
                ("BOX", (0, 0), (-1, -1), 0.5, colors.HexColor("#D8DEE4")),
                ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#E3E7EA")),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )
    story.extend(
        [
            metadata,
            Spacer(1, 0.35 * inch),
            Paragraph(
                "This report presents the nine required questions and two "
                "original questions. Each section states the verified result, "
                "shows the executable SQL, and explains how the query answers "
                "the question. Counts use whole numbers; percentages and "
                "averages use two decimal places.",
                styles["body"],
            ),
            PageBreak(),
        ]
    )

    for index, analysis in enumerate(ANALYSES):
        story.extend(
            [
                Paragraph(
                    f"QUESTION {analysis['number']} OF 11",
                    styles["eyebrow"],
                ),
                Paragraph(analysis["question"], styles["question"]),
                result_box(analysis["result"], styles),
                Paragraph("SQL query", styles["section"]),
                Preformatted(analysis["sql"].strip(), styles["code"]),
                Paragraph("How the query answers the question", styles["section"]),
                Paragraph(analysis["explanation"], styles["body"]),
            ]
        )
        if index < len(ANALYSES) - 1:
            story.append(PageBreak())

    document.build(
        story,
        onFirstPage=draw_first_page,
        onLaterPages=draw_later_pages,
    )
    print(f"Created {OUTPUT}")


if __name__ == "__main__":
    build_pdf()
