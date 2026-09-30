"""Build a report PDF and a browser view of captured Snyk output."""

from html import escape
from pathlib import Path
import re

from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

ROOT = Path(__file__).resolve().parents[1]
evidence_dir = ROOT / "tmp" / "evidence"
evidence_dir.mkdir(parents=True, exist_ok=True)
scan_output = (ROOT / "snyk-analysis.txt").read_text(encoding="utf-8")
scan_output = re.sub(r"\x1b\[[0-9;]*m", "", scan_output)
html = (
    '<!doctype html><html><head><meta charset="utf-8">'
    '<title>Module 5 - Snyk scan evidence</title>'
    '<style>body{margin:32px;color:#172033;background:#fff;'
    'font:16px Arial}pre{font:13px/1.5 Consolas,monospace;'
    'white-space:pre-wrap;overflow-wrap:anywhere;padding:24px;'
    'background:#f3f5f8;border:1px solid #ccd3df}'
    'p{color:#46536a}</style></head><body>'
    '<h1>Module 5 - Snyk dependency scan</h1>'
    '<p>Saved CLI output, displayed verbatim from snyk-analysis.txt.</p>'
    '<pre>' + escape(scan_output) + '</pre></body></html>'
)
(evidence_dir / "snyk.html").write_text(html, encoding="utf-8")

styles = getSampleStyleSheet()
styles["BodyText"].fontSize = 10
styles["BodyText"].leading = 14
styles["BodyText"].spaceAfter = 8
styles["Heading1"].textColor = colors.HexColor("#173e67")
source = (ROOT / "MODULE5_REPORT.md").read_text(encoding="utf-8")
story = []
for block in source.split("\n\n"):
    block = block.strip()
    if not block:
        continue
    style = styles["BodyText"]
    if block.startswith("# "):
        block = "Module 5: Software Assurance and Secure SQL"
        style = styles["Title"]
    elif block.startswith("## "):
        block = block[3:]
        style = styles["Heading2"]
    text = escape(" ".join(block.splitlines()))
    text = re.sub(r"`([^`]+)`", r'<font name="Courier">\1</font>', text)
    story.append(Paragraph(text, style))
    story.append(Spacer(1, 4))

def footer(canvas, doc):
    canvas.setFont("Helvetica", 8)
    canvas.setFillColor(colors.HexColor("#56647a"))
    canvas.drawString(0.65 * inch, 0.4 * inch,
                      "Denver Clarke | EN.605.256 | Module 5")
    canvas.drawRightString(7.85 * inch, 0.4 * inch, str(doc.page))

SimpleDocTemplate(
    str(ROOT / "module_5_report.pdf"),
    rightMargin=0.65 * inch, leftMargin=0.65 * inch,
    topMargin=0.6 * inch, bottomMargin=0.65 * inch,
    title="Module 5 Software Assurance and Secure SQL",
    author="Denver Clarke",
    allowSplitting=0,
).build(story, onFirstPage=footer, onLaterPages=footer)
print("Built module_5_report.pdf and tmp/evidence/snyk.html")
