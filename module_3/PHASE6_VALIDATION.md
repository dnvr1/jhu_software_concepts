# Phase 6: SQLAlchemy ORM Query Validation

Validated on September 15, 2026 against the same 30,000-row PostgreSQL
`applicants` table used by `load_data.py` and `query_data.py`.

| Analysis | Raw SQL | SQLAlchemy ORM | Match |
| --- | ---: | ---: | :---: |
| Question 1 - Fall 2026 count | 29,585 | 29,585 | Yes |
| Question 4 - American Fall 2026 average GPA | 3.79 | 3.79 | Yes |
| Question 5 - Fall 2025 acceptance percentage | 47.92% | 47.92% | Yes |
| Question 8 - Original-field count | 28 | 28 | Yes |
| Question 9 - LLM-field count | 28 | 28 | Yes |
| Question 9 - Difference | +0 | +0 | Yes |
| Question 10 - American entries | 15,448 | 15,448 | Yes |
| Question 10 - American acceptance percentage | 38.53% | 38.53% | Yes |
| Question 10 - International entries | 13,499 | 13,499 | Yes |
| Question 10 - International acceptance percentage | 34.59% | 34.59% | Yes |

The implementation constructs every operation with `select()`, mapped
`Applicant` attributes, SQLAlchemy aggregate functions, filters, grouping, and
ordering. It executes the statements through an ORM `Session`. An AST-based
test rejects psycopg imports, `text()` calls, and cursor calls in
`orm_queries.py`.
