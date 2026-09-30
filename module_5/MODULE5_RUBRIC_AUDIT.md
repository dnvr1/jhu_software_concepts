# Module 5 rubric audit

Reviewed September 30, 2026 against the supplied Module 5 assignment PDF.
This is an evidence checklist, not a prediction or guarantee of the instructor's grade.

| Rubric category | Points | Assessment and evidence |
| --- | ---: | --- |
| GitHub repository and submission | 5 | Required SSH remote is `git@github.com:dnvr1/jhu_software_concepts.git`. Organized `module_5/` and root `.github/workflows/ci.yml` are pushed. `tools/build_submission.py` and `tools/verify_submission.py` check the ZIP manifest and every file's bytes against Git. **Canvas upload is still a user action.** |
| Virtual environment and reproducible setup | 8 | pip/venv and uv editable installations were verified in separate environments. README gives both paths, PostgreSQL configuration and app launch instructions. Full tooling is verified on Python 3.12. Runtime requirements include Pylint and pydeps. |
| Pylint | 10 | All `src/` Python modules: 10.00/10, no emitted warnings/errors; see `lint_summary.txt`. CI enforces `--fail-under=10`. The project uses documented design thresholds and targeted suppressions for dynamic SQLAlchemy behavior; this is not a default-config score. |
| SQL injection defenses | 20 | `query_data.build_lookup_statement` uses `sql.SQL`, allowlisted `sql.Identifier` columns and placeholders; `lookup_applicants` executes separate parameters. Dynamic database names use `Identifier`. Ingested values and ORM filters are bound. Unit and live CI tests verify malicious values do not become SQL. Existing Flask analysis routes accept no SQL search filters; the safe lookup helper is tested independently, not presented as a web endpoint. |
| LIMIT and query safety | 5 | All application-authored SELECT analysis and metadata queries have bounded limits, including the inherited model validation utility. Tests inspect all 11 raw and all 11 ORM analysis statements. Lookup limits clamp to 1-100; invalid, negative, oversized and non-finite inputs are tested. DDL and INSERT are not SELECT queries and do not use PostgreSQL LIMIT syntax. |
| Database hardening | 10 | Environment-based credentials, tracked placeholder-only `.env.example`, and ignored `.env` verified. CI creates `gradcafe_app` with only needed SELECT/INSERT and sequence usage, no ownership or superuser privileges. `database_privileges.txt` records successful restricted app use and denied CREATE/ALTER/DROP/UPDATE/DELETE/TRUNCATE. **This evidence is from disposable CI, not the home database.** Local setup scripts are provided. PDF explains the grants. |
| Dependency graph | 8 | `dependency.svg` exists and is generated/validated by CI with pydeps + Graphviz. PDF has exactly seven dependency-summary sentences. |
| Packaging | 5 | `setup.py` supports the documented `pip install -e .` and uv editable workflows, verified locally and in CI. PDF explains import consistency and editable development. Standalone wheel deployment is not the documented installation method. |
| Snyk dependencies | 6 | `snyk-analysis.png`, text and JSON evidence record a successful local scan (52 dependencies, zero issues). Hosted Linux scan passed with 50 dependencies and zero issues. Different platforms resolve different dependency sets. |
| GitHub Actions | 13 | Four jobs: Pylint threshold 10, graph generation/presence, Snyk scan, and Pytest with 100% coverage. Workflow runs on every push/PR and supports manual execution. Least-privilege verification also fails the job on errors (`bash` pipefail). Passing run evidence is in `ci_success.jpg` and linked in README. |
| README, PDF and deliverables | 10 | README and the visually checked three-page `module_5_report.pdf` cover installation/run, environment variables, security, limits, grants, graph, packaging, CI and SAST extra credit. Required files are checked by the ZIP verifier. Existing Module 4 Read the Docs stays available; Module 5 Sphinx HTML builds with `-W`. |
| Optional Snyk Code | +5 | Executed with original CLI and SARIF output preserved. Initial 26 findings reduced to 25 after fixing HTML escaping; zero high, two medium and 23 low remain. `SNYK_CODE_REVIEW.md` and the PDF explain the fix and remaining trust boundaries. No findings suppressed; exit code 1 correctly records findings, not scan failure. Instructor determines credit. |

## Audit corrections

- Added the missing aggregate LIMIT in `tools/validate_models.py`.
- Separated dynamic database statement construction from execution.
- Added explicit bounds checks for every raw and ORM analysis statement.
- Handled non-finite limit inputs without raising an overflow error.
- Corrected installation guidance to the verified Python 3.12 tooling version.
- Refreshed test evidence and regenerated/reviewed the report and documentation.

Local audit rerun: 132 passed, three documented skips, 100% coverage over
1,166 statements; Pylint 10.00/10; Sphinx warning-as-error build succeeded.
Hosted runs also exercise the PostgreSQL integration test (133 passed, two skips).

## Remaining actions and scope

1. Review and upload the rebuilt `output/module_5_submission.zip` to Canvas.
2. For home-PC operation, apply the role setup with your administrator password
   and set the app credentials privately. No home database changes are claimed.
3. The Module 1 Projects website contains the Module 5 card and evidence links.
   Its source is pushed to GitHub and its local page is verified. No separate
   public web host was configured in this repository.

The assignment contains conflicting repository-visibility instructions; no
visibility change was made as part of this audit.
