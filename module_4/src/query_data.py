"""Answer the nine required analysis questions with raw PostgreSQL SQL."""

from __future__ import annotations

import sys
from typing import Any

import psycopg

from analysis_format import format_count, format_decimal, format_difference
from load_data import connect_database


QUESTION_1 = "How many entries are from applicants who applied for Fall 2026?"
SQL_QUESTION_1 = """
SELECT COUNT(*)
FROM applicants
WHERE LOWER(BTRIM(term)) = 'fall 2026'
"""

QUESTION_2 = (
    "Among entries that provide a nationality classification, what "
    "percentage are international students?"
)
SQL_QUESTION_2 = """
SELECT
    100.0 * COUNT(*) FILTER (
        WHERE LOWER(BTRIM(us_or_international)) = 'international'
    ) / NULLIF(
        COUNT(*) FILTER (
            WHERE NULLIF(BTRIM(us_or_international), '') IS NOT NULL
        ),
        0
    )
FROM applicants
"""

QUESTION_3 = (
    "What are the average GPA, GRE Quantitative, GRE Verbal, and GRE "
    "Analytical Writing scores among applicants who provide each metric?"
)
SQL_QUESTION_3 = """
SELECT
    AVG(gpa),
    AVG(gre),
    AVG(gre_v),
    AVG(gre_aw)
FROM applicants
"""

QUESTION_4 = (
    "What is the average GPA of American applicants who applied for "
    "Fall 2026?"
)
SQL_QUESTION_4 = """
SELECT AVG(gpa)
FROM applicants
WHERE LOWER(BTRIM(term)) = 'fall 2026'
  AND LOWER(BTRIM(us_or_international)) = 'american'
  AND gpa IS NOT NULL
"""

QUESTION_5 = "What percentage of Fall 2025 entries are acceptances?"
SQL_QUESTION_5 = """
SELECT
    100.0 * COUNT(*) FILTER (
        WHERE LOWER(BTRIM(status)) = 'accepted'
    ) / NULLIF(COUNT(*), 0)
FROM applicants
WHERE LOWER(BTRIM(term)) = 'fall 2025'
"""

QUESTION_6 = (
    "What is the average GPA of accepted applicants who applied for "
    "Fall 2026?"
)
SQL_QUESTION_6 = """
SELECT AVG(gpa)
FROM applicants
WHERE LOWER(BTRIM(term)) = 'fall 2026'
  AND LOWER(BTRIM(status)) = 'accepted'
  AND gpa IS NOT NULL
"""

QUESTION_7 = (
    "How many entries are from applicants who applied to Johns Hopkins "
    "University for a master's degree in Computer Science?"
)
SQL_QUESTION_7 = r"""
SELECT COUNT(*)
FROM applicants
WHERE (
        LOWER(program) LIKE '%johns hopkins university%'
        OR program ~* '\mJHU\M'
      )
  AND LOWER(program) LIKE '%computer science%'
  AND BTRIM(LOWER(degree)) IN (
        'master',
        'masters',
        'master''s',
        'ms',
        'm.s.',
        'msc',
        'm.sc.'
      )
"""

QUESTION_8 = (
    "How many Fall 2026 entries are acceptances from applicants applying "
    "for a PhD in Computer Science at Georgetown, MIT, Stanford, or "
    "Carnegie Mellon using the original program field?"
)
SQL_QUESTION_8 = r"""
SELECT COUNT(*)
FROM applicants
WHERE LOWER(BTRIM(term)) = 'fall 2026'
  AND LOWER(BTRIM(status)) = 'accepted'
  AND BTRIM(LOWER(degree)) IN (
        'phd',
        'ph.d.',
        'doctor of philosophy'
      )
  AND LOWER(program) LIKE '%computer science%'
  AND (
        LOWER(program) LIKE '%georgetown university%'
        OR LOWER(program) LIKE '%massachusetts institute of technology%'
        OR program ~* '\mMIT\M'
        OR LOWER(program) LIKE '%stanford university%'
        OR LOWER(program) LIKE '%carnegie mellon university%'
      )
"""

QUESTION_9 = (
    "Repeat Question 8 using the LLM-generated program and university "
    "fields, and compare the counts."
)
SQL_QUESTION_9 = r"""
SELECT COUNT(*)
FROM applicants
WHERE LOWER(BTRIM(term)) = 'fall 2026'
  AND LOWER(BTRIM(status)) = 'accepted'
  AND BTRIM(LOWER(degree)) IN (
        'phd',
        'ph.d.',
        'doctor of philosophy'
      )
  AND LOWER(llm_generated_program) LIKE '%computer science%'
  AND (
        LOWER(llm_generated_university) LIKE '%georgetown university%'
        OR LOWER(llm_generated_university)
            LIKE '%massachusetts institute of technology%'
        OR llm_generated_university ~* '\mMIT\M'
        OR LOWER(llm_generated_university) LIKE '%stanford university%'
        OR LOWER(llm_generated_university)
            LIKE '%carnegie mellon university%'
      )
"""

QUESTION_10 = (
    "For Fall 2026, what are the applicant counts and acceptance "
    "percentages for American and international entries?"
)
SQL_QUESTION_10 = """
SELECT
    INITCAP(LOWER(BTRIM(us_or_international))) AS classification,
    COUNT(*) AS applicant_count,
    100.0 * COUNT(*) FILTER (
        WHERE LOWER(BTRIM(status)) = 'accepted'
    ) / NULLIF(COUNT(*), 0) AS acceptance_percentage
FROM applicants
WHERE LOWER(BTRIM(term)) = 'fall 2026'
  AND LOWER(BTRIM(us_or_international)) IN (
        'american',
        'international'
      )
GROUP BY LOWER(BTRIM(us_or_international))
ORDER BY CASE LOWER(BTRIM(us_or_international))
    WHEN 'american' THEN 1
    ELSE 2
END
"""

QUESTION_11 = (
    "Which five LLM-standardized universities have the most Fall 2026 "
    "entries, and what percentage of each university's entries are "
    "acceptances?"
)
SQL_QUESTION_11 = """
SELECT
    MIN(BTRIM(llm_generated_university)) AS university,
    COUNT(*) AS applicant_count,
    100.0 * COUNT(*) FILTER (
        WHERE LOWER(BTRIM(status)) = 'accepted'
    ) / NULLIF(COUNT(*), 0) AS acceptance_percentage
FROM applicants
WHERE LOWER(BTRIM(term)) = 'fall 2026'
  AND NULLIF(BTRIM(llm_generated_university), '') IS NOT NULL
GROUP BY LOWER(BTRIM(llm_generated_university))
ORDER BY applicant_count DESC, university ASC
LIMIT 5
"""


def fetch_one(
    cursor: psycopg.Cursor, query: str
) -> tuple[Any, ...]:
    """Execute one analysis query and require exactly one result row."""
    cursor.execute(query)
    row = cursor.fetchone()
    if row is None:
        raise RuntimeError("An analysis query returned no result row")
    return row


def fetch_all(
    cursor: psycopg.Cursor, query: str
) -> list[tuple[Any, ...]]:
    """Execute one analysis query and return all result rows."""
    cursor.execute(query)
    return cursor.fetchall()


def run_analysis(connection: psycopg.Connection) -> dict[str, object]:
    """Execute Questions 1-11 using handwritten SQL only."""
    connection.read_only = True
    with connection.cursor() as cursor:
        question_1 = fetch_one(cursor, SQL_QUESTION_1)[0]
        question_2 = fetch_one(cursor, SQL_QUESTION_2)[0]
        question_3 = fetch_one(cursor, SQL_QUESTION_3)
        question_4 = fetch_one(cursor, SQL_QUESTION_4)[0]
        question_5 = fetch_one(cursor, SQL_QUESTION_5)[0]
        question_6 = fetch_one(cursor, SQL_QUESTION_6)[0]
        question_7 = fetch_one(cursor, SQL_QUESTION_7)[0]
        question_8 = fetch_one(cursor, SQL_QUESTION_8)[0]
        question_9 = fetch_one(cursor, SQL_QUESTION_9)[0]
        question_10 = fetch_all(cursor, SQL_QUESTION_10)
        question_11 = fetch_all(cursor, SQL_QUESTION_11)

    return {
        "question_1": question_1,
        "question_2": question_2,
        "question_3": question_3,
        "question_4": question_4,
        "question_5": question_5,
        "question_6": question_6,
        "question_7": question_7,
        "question_8": question_8,
        "question_9": question_9,
        "question_10": question_10,
        "question_11": question_11,
    }


def print_question(number: int, question: str) -> None:
    """Print a consistent heading for console and screenshot output."""
    print(f"\nQuestion {number}")
    print(question)


def print_analysis(results: dict[str, object]) -> None:
    """Print every result using the assignment's required formatting."""
    print("Module 3 Raw SQL Analysis")

    print_question(1, QUESTION_1)
    print(
        "Fall 2026 applicant count: "
        f"{format_count(results['question_1'])}"
    )

    print_question(2, QUESTION_2)
    print(
        "Percent international: "
        f"{format_decimal(results['question_2'], '%')}"
    )

    print_question(3, QUESTION_3)
    gpa, gre, gre_v, gre_aw = results["question_3"]
    print(f"Average GPA: {format_decimal(gpa)}")
    print(f"Average GRE Quantitative: {format_decimal(gre)}")
    print(f"Average GRE Verbal: {format_decimal(gre_v)}")
    print(
        "Average GRE Analytical Writing: "
        f"{format_decimal(gre_aw)}"
    )

    print_question(4, QUESTION_4)
    print(
        "Average GPA, American Fall 2026 applicants: "
        f"{format_decimal(results['question_4'])}"
    )

    print_question(5, QUESTION_5)
    print(
        "Fall 2025 acceptance percentage: "
        f"{format_decimal(results['question_5'], '%')}"
    )

    print_question(6, QUESTION_6)
    print(
        "Average GPA, accepted Fall 2026 applicants: "
        f"{format_decimal(results['question_6'])}"
    )

    print_question(7, QUESTION_7)
    print(
        "JHU Computer Science master's applicant count: "
        f"{format_count(results['question_7'])}"
    )

    print_question(8, QUESTION_8)
    print(
        "Original-field count: "
        f"{format_count(results['question_8'])}"
    )

    print_question(9, QUESTION_9)
    original_count = int(results["question_8"])
    llm_count = int(results["question_9"])
    print(f"Original-field count: {format_count(original_count)}")
    print(f"LLM-field count: {format_count(llm_count)}")
    print(f"Difference: {format_difference(llm_count - original_count)}")

    print_question(10, QUESTION_10)
    for classification, applicant_count, percentage in results[
        "question_10"
    ]:
        print(
            f"{classification}: {format_count(applicant_count)} entries, "
            f"{format_decimal(percentage, '%')} accepted"
        )

    print_question(11, QUESTION_11)
    for position, row in enumerate(results["question_11"], start=1):
        university, applicant_count, percentage = row
        print(
            f"{position}. {university}: "
            f"{format_count(applicant_count)} entries, "
            f"{format_decimal(percentage, '%')} accepted"
        )


def main() -> int:
    """Connect, execute the required SQL, and print formatted results."""
    try:
        with connect_database() as connection:
            results = run_analysis(connection)
        print_analysis(results)
    except (RuntimeError, ValueError, psycopg.Error) as error:
        print(f"Query analysis failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":  # pragma: no cover - module execution bootstrap
    raise SystemExit(main())
