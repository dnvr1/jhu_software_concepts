"""Capture live raw-SQL and ORM output as submission screenshots."""

from __future__ import annotations

from contextlib import redirect_stdout
from io import StringIO
import getpass
import os
from pathlib import Path
import shutil
import textwrap

from PIL import Image, ImageDraw, ImageFont

import models
import orm_queries
import query_data
from load_data import connect_database


ROOT = Path(__file__).parent
SCREENSHOTS = ROOT / "screenshots"
PLAYWRIGHT_SCREENSHOT = (
    ROOT / "output" / "playwright" / "flask_update_finished.png"
)


def capture(function, *args) -> str:
    """Return printed output while preserving its exact formatted values."""
    buffer = StringIO()
    with redirect_stdout(buffer):
        function(*args)
    return buffer.getvalue().strip()


def font(size: int, bold: bool = False):
    """Load the Windows console font, with a portable fallback."""
    filename = "consolab.ttf" if bold else "consola.ttf"
    path = Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / filename
    if path.exists():
        return ImageFont.truetype(str(path), size)
    return ImageFont.load_default()


def render_console(text: str, destination: Path, title: str) -> None:
    """Render a readable terminal transcript from live program output."""
    width = 1500
    padding = 42
    title_height = 54
    body_font = font(17)
    title_font = font(17, bold=True)
    line_height = 25
    wrapped_lines: list[str] = []
    for line in text.splitlines():
        wrapped_lines.extend(textwrap.wrap(line, width=112) or [""])
    height = title_height + padding * 2 + line_height * len(wrapped_lines)
    image = Image.new("RGB", (width, height), "#0c1117")
    drawing = ImageDraw.Draw(image)
    drawing.rectangle((0, 0, width, title_height), fill="#202832")
    drawing.ellipse((18, 19, 32, 33), fill="#ff5f57")
    drawing.ellipse((40, 19, 54, 33), fill="#febc2e")
    drawing.ellipse((62, 19, 76, 33), fill="#28c840")
    drawing.text((96, 15), title, font=title_font, fill="#e6edf3")
    y = title_height + padding
    for line in wrapped_lines:
        color = "#7ee787" if line.startswith("Module 3") else "#e6edf3"
        drawing.text((padding, y), line, font=body_font, fill=color)
        y += line_height
    destination.parent.mkdir(parents=True, exist_ok=True)
    image.save(destination, optimize=True)


def main() -> int:
    """Prompt once, run both live analyses, and save three required images."""
    password = os.getenv("PGPASSWORD")
    if password is None:
        password = getpass.getpass(
            f"Password for PostgreSQL user {os.getenv('PGUSER', 'postgres')}: "
        )

    previous_password = os.environ.get("PGPASSWORD")
    os.environ["PGPASSWORD"] = password
    try:
        with connect_database() as connection:
            raw_results = query_data.run_analysis(connection)
        raw_text = capture(query_data.print_analysis, raw_results)

        _, session_factory = models.configure_database(password)
        with session_factory() as session:
            orm_results = orm_queries.run_analysis(session)
        orm_text = capture(orm_queries.print_analysis, orm_results)
    finally:
        if previous_password is None:
            os.environ.pop("PGPASSWORD", None)
        else:
            os.environ["PGPASSWORD"] = previous_password

    raw_transcript = (
        "C:\\...\\module_3> python query_data.py\n\n" + raw_text
    )
    orm_transcript = (
        "C:\\...\\module_3> python orm_queries.py\n\n" + orm_text
    )
    render_console(
        raw_transcript,
        SCREENSHOTS / "raw_sql_output.png",
        "Module 3 - Raw PostgreSQL SQL",
    )
    render_console(
        orm_transcript,
        SCREENSHOTS / "sqlalchemy_orm_output.png",
        "Module 3 - SQLAlchemy ORM",
    )
    if not PLAYWRIGHT_SCREENSHOT.exists():
        raise FileNotFoundError(
            "Run the Flask browser validation before capturing evidence"
        )
    shutil.copy2(PLAYWRIGHT_SCREENSHOT, SCREENSHOTS / "flask_webpage.png")

    print(raw_text)
    print("\n" + "=" * 72 + "\n")
    print(orm_text)
    print(f"\nSaved submission screenshots in {SCREENSHOTS}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
