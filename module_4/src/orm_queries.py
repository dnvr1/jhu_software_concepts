"""Repeat selected analyses with SQLAlchemy 2.x ORM expressions."""

from __future__ import annotations

import getpass
import os
import sys
from typing import Any

from sqlalchemy import Select, case, func, or_, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from analysis_format import format_count, format_decimal, format_difference
import models


MASTER_DEGREES = (
    "master",
    "masters",
    "master's",
    "ms",
    "m.s.",
    "msc",
    "m.sc.",
)
PHD_DEGREES = ("phd", "ph.d.", "doctor of philosophy")


def normalized(column):
    """Return a case-insensitive, whitespace-normalized SQL expression."""
    return func.lower(func.btrim(column))


def acceptance_percentage():
    """Return a conditional aggregate for accepted-row percentages."""
    accepted_count = func.count(models.Applicant.p_id).filter(
        normalized(models.Applicant.status) == "accepted"
    )
    total_count = func.count(models.Applicant.p_id)
    return 100.0 * accepted_count / func.nullif(total_count, 0)


def question_1_statement() -> Select:
    """Build the Fall 2026 applicant-count ORM statement."""
    return select(func.count(models.Applicant.p_id)).where(
        normalized(models.Applicant.term) == "fall 2026"
    )


def question_2_statement() -> Select:
    """Build the international-classification percentage statement."""
    nationality = models.Applicant.us_or_international
    international_count = func.count(models.Applicant.p_id).filter(
        normalized(nationality) == "international"
    )
    classified_count = func.count(models.Applicant.p_id).filter(
        func.nullif(func.btrim(nationality), "").is_not(None)
    )
    return select(
        100.0 * international_count / func.nullif(classified_count, 0)
    )


def question_3_statement() -> Select:
    """Build the four independent score-average expressions."""
    return select(
        func.avg(models.Applicant.gpa),
        func.avg(models.Applicant.gre),
        func.avg(models.Applicant.gre_v),
        func.avg(models.Applicant.gre_aw),
    )


def question_4_statement() -> Select:
    """Build the American Fall 2026 average-GPA ORM statement."""
    return select(func.avg(models.Applicant.gpa)).where(
        normalized(models.Applicant.term) == "fall 2026",
        normalized(models.Applicant.us_or_international) == "american",
        models.Applicant.gpa.is_not(None),
    )


def question_5_statement() -> Select:
    """Build the Fall 2025 acceptance-percentage ORM statement."""
    return select(acceptance_percentage()).where(
        normalized(models.Applicant.term) == "fall 2025"
    )


def question_6_statement() -> Select:
    """Build the accepted Fall 2026 average-GPA ORM statement."""
    return select(func.avg(models.Applicant.gpa)).where(
        normalized(models.Applicant.term) == "fall 2026",
        normalized(models.Applicant.status) == "accepted",
        models.Applicant.gpa.is_not(None),
    )


def question_7_statement() -> Select:
    """Build the original-field JHU master's count statement."""
    program = models.Applicant.program
    return select(func.count(models.Applicant.p_id)).where(
        or_(
            func.lower(program).like("%johns hopkins university%"),
            program.regexp_match(r"\mJHU\M", flags="i"),
        ),
        func.lower(program).like("%computer science%"),
        normalized(models.Applicant.degree).in_(MASTER_DEGREES),
    )


def original_university_filter():
    """Match the four universities in the original combined program field."""
    program = models.Applicant.program
    lowered_program = func.lower(program)
    return or_(
        lowered_program.like("%georgetown university%"),
        lowered_program.like("%massachusetts institute of technology%"),
        program.regexp_match(r"\mMIT\M", flags="i"),
        lowered_program.like("%stanford university%"),
        lowered_program.like("%carnegie mellon university%"),
    )


def generated_university_filter():
    """Match the four universities in the LLM-generated university field."""
    university = models.Applicant.llm_generated_university
    lowered_university = func.lower(university)
    return or_(
        lowered_university.like("%georgetown university%"),
        lowered_university.like(
            "%massachusetts institute of technology%"
        ),
        university.regexp_match(r"\mMIT\M", flags="i"),
        lowered_university.like("%stanford university%"),
        lowered_university.like("%carnegie mellon university%"),
    )


def question_8_statement() -> Select:
    """Build Question 8 using the original combined program field."""
    return select(func.count(models.Applicant.p_id)).where(
        normalized(models.Applicant.term) == "fall 2026",
        normalized(models.Applicant.status) == "accepted",
        normalized(models.Applicant.degree).in_(PHD_DEGREES),
        func.lower(models.Applicant.program).like("%computer science%"),
        original_university_filter(),
    )


def question_9_statement() -> Select:
    """Build Question 9 using the LLM-generated fields."""
    return select(func.count(models.Applicant.p_id)).where(
        normalized(models.Applicant.term) == "fall 2026",
        normalized(models.Applicant.status) == "accepted",
        normalized(models.Applicant.degree).in_(PHD_DEGREES),
        func.lower(models.Applicant.llm_generated_program).like(
            "%computer science%"
        ),
        generated_university_filter(),
    )


def question_10_statement() -> Select:
    """Build the original nationality comparison with ORM grouping."""
    nationality = normalized(models.Applicant.us_or_international)
    display_name = func.initcap(nationality).label("classification")
    applicant_count = func.count(models.Applicant.p_id).label(
        "applicant_count"
    )
    percentage = acceptance_percentage().label("acceptance_percentage")
    display_order = case((nationality == "american", 1), else_=2)

    return (
        select(display_name, applicant_count, percentage)
        .where(
            normalized(models.Applicant.term) == "fall 2026",
            nationality.in_(("american", "international")),
        )
        .group_by(nationality)
        .order_by(display_order)
    )


def question_11_statement() -> Select:
    """Build the top-five Fall 2026 university analysis."""
    university = models.Applicant.llm_generated_university
    normalized_university = normalized(university)
    display_name = func.min(func.btrim(university)).label("university")
    applicant_count = func.count(models.Applicant.p_id).label(
        "applicant_count"
    )
    percentage = acceptance_percentage().label("acceptance_percentage")

    return (
        select(display_name, applicant_count, percentage)
        .where(
            normalized(models.Applicant.term) == "fall 2026",
            func.nullif(func.btrim(university), "").is_not(None),
        )
        .group_by(normalized_university)
        .order_by(applicant_count.desc(), display_name.asc())
        .limit(5)
    )


def build_statements() -> dict[str, Select]:
    """Return every required SQLAlchemy statement for inspection and tests."""
    return {
        "question_1": question_1_statement(),
        "question_4": question_4_statement(),
        "question_5": question_5_statement(),
        "question_8": question_8_statement(),
        "question_9": question_9_statement(),
        "question_10": question_10_statement(),
    }


def build_complete_statements() -> dict[str, Select]:
    """Return all 11 analysis statements used by the Flask page."""
    statements = build_statements()
    statements.update(
        {
            "question_2": question_2_statement(),
            "question_3": question_3_statement(),
            "question_6": question_6_statement(),
            "question_7": question_7_statement(),
            "question_11": question_11_statement(),
        }
    )
    return statements


def run_analysis(session: Session) -> dict[str, Any]:
    """Execute selected analyses through an ORM Session."""
    statements = build_statements()
    return {
        "question_1": session.scalar(statements["question_1"]),
        "question_4": session.scalar(statements["question_4"]),
        "question_5": session.scalar(statements["question_5"]),
        "question_8": session.scalar(statements["question_8"]),
        "question_9": session.scalar(statements["question_9"]),
        "question_10": session.execute(
            statements["question_10"]
        ).all(),
    }


def run_complete_analysis(session: Session) -> dict[str, Any]:
    """Execute all 11 ORM analyses for the dynamic Flask page."""
    results = run_analysis(session)
    statements = build_complete_statements()
    results.update(
        {
            "question_2": session.scalar(statements["question_2"]),
            "question_3": session.execute(
                statements["question_3"]
            ).one(),
            "question_6": session.scalar(statements["question_6"]),
            "question_7": session.scalar(statements["question_7"]),
            "question_11": session.execute(
                statements["question_11"]
            ).all(),
            "total_rows": session.scalar(
                select(func.count(models.Applicant.p_id))
            ),
        }
    )
    return results


def runtime_password() -> str | None:
    """Use configured credentials or securely request the password."""
    if os.getenv("DATABASE_URL"):
        return None
    password = os.getenv("PGPASSWORD")
    if password is not None:
        return password
    return getpass.getpass(
        f"Password for PostgreSQL user {os.getenv('PGUSER', 'postgres')}: "
    )


def print_analysis(results: dict[str, Any]) -> None:
    """Print ORM results with the same formatting as the raw-SQL output."""
    print("Module 3 SQLAlchemy ORM Analysis")

    print("\nQuestion 1")
    print(
        "Fall 2026 applicant count: "
        f"{format_count(results['question_1'])}"
    )

    print("\nQuestion 4")
    print(
        "Average GPA, American Fall 2026 applicants: "
        f"{format_decimal(results['question_4'])}"
    )

    print("\nQuestion 5")
    print(
        "Fall 2025 acceptance percentage: "
        f"{format_decimal(results['question_5'], '%')}"
    )

    print("\nQuestion 8")
    print(
        "Original-field count: "
        f"{format_count(results['question_8'])}"
    )

    print("\nQuestion 9")
    original_count = int(results["question_8"])
    llm_count = int(results["question_9"])
    print(f"Original-field count: {format_count(original_count)}")
    print(f"LLM-field count: {format_count(llm_count)}")
    print(f"Difference: {format_difference(llm_count - original_count)}")

    print("\nQuestion 10 - Original Question")
    for classification, applicant_count, percentage in results[
        "question_10"
    ]:
        print(
            f"{classification}: {format_count(applicant_count)} entries, "
            f"{format_decimal(percentage, '%')} accepted"
        )


def main() -> int:
    """Configure credentials, run ORM statements, and print the results."""
    try:
        _, session_factory = models.configure_database(runtime_password())
        with session_factory() as session:
            results = run_analysis(session)
        print_analysis(results)
    except (RuntimeError, ValueError, SQLAlchemyError) as error:
        print(f"ORM analysis failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - module execution bootstrap
    raise SystemExit(main())
