# Module 3 Rubric Checklist

This file tracks completion against the 100-point grading rubric. An item is
marked complete only after its implementation and required evidence have been
verified.

## 1. GitHub Repository Setup and Submission - 5 points

- [x] `github.txt` contains the verified private repository SSH URL.
- [x] A dedicated, organized `module_3` folder exists in the repository.
- [x] The final GitHub commit and Canvas ZIP contain the same files.

## 2. PostgreSQL Database Setup and Data Loading - 18 points

- [x] `load_data.py` connects to PostgreSQL with psycopg 3.
- [x] `applicants` schema defines all required columns and an integer primary
  key.
- [x] PostgreSQL verification confirms that all 30,000 cleaned records loaded.
- [x] Optional missing values become SQL `NULL` values.
- [x] A unique URL constraint and `ON CONFLICT DO NOTHING` prevent duplicates.
- [x] A second real loader run confirms that zero additional rows are inserted.
- [x] Errors roll back the transaction and produce a concise failure message.
- [x] Credentials are read from the environment or a secure runtime prompt.
- [x] `.env`, virtual environments, and caches are ignored by Git.

## 3. Raw SQL Query Analysis - 22 points

- [x] `query_data.py` answers Questions 1-9 using executable SQL.
- [x] Filters and text matching satisfy each question exactly.
- [x] Percentages, denominators, NULL handling, averages, and formatting are
  verified.
- [x] Two meaningful original questions are answered.
- [x] `query_results.pdf` contains all 11 questions, results, SQL, and
  explanations.

## 4. SQLAlchemy ORM - 15 points

- [x] `models.py` maps `Applicant` to the existing table.
- [x] Modern Engine and Session configuration is implemented.
- [x] `orm_queries.py` repeats Questions 1, 4, 5, 8, 9, and one original
  question.
- [x] ORM queries contain no handwritten SQL or psycopg cursors.
- [x] Flask reads use the ORM.
- [x] README compares one raw SQL query with its ORM equivalent.

## 5. Flask Webpage Functionality - 20 points

- [x] Flask connects through SQLAlchemy.
- [x] All analysis results are queried dynamically and displayed.
- [x] The analysis page is organized, readable, and styled with CSS.
- [x] Pull Data is functional and explained.
- [x] Update Analysis refreshes results and reports an active scrape.
- [x] The application passes its runtime checks.

## 6. Scraping and Data Refresh Integration - 8 points

- [x] Module 2 scraping is reused safely.
- [x] Only new usable records are inserted.
- [x] Concurrent scraping processes are prevented.
- [x] User-facing status and error messages are clear.

## 7. Written Reflection: Data Limitations - 7 points

- [x] `limitations.pdf` contains two substantive paragraphs.
- [x] It discusses bias, missingness, reliability, and representativeness.
- [x] It connects the limitations to verified analysis results.
- [x] The writing and rendered PDF are proofread.

## 8. Documentation, Screenshots, and Requirements - 5 points

- [x] README covers database, SQL, ORM, scraper, and Flask setup and use.
- [x] `requirements.txt` contains all current runtime dependencies.
- [x] Screenshots show raw SQL output, ORM output, and the running webpage.

## Final Submission Checks

- [x] Required files are present and no secrets or generated environments are
  included.
- [x] Automated checks pass from a clean environment.
- [x] `module_3.zip` is created from the final committed folder.
- [x] The ZIP contents and final GitHub commit correspond.
