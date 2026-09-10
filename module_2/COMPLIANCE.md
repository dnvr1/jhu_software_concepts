# Module 2 compliance report

## Completed assignment requirements

- Python collected 30,000 genuine public GradCafe entries with 30,000 unique
  applicant URLs.
- The requested program, university, comment, added date, URL, status, decision
  dates, term, citizenship/origin, GRE values, degree, GPA, and GRE writing
  fields use a consistent schema and JSON `null` for unavailable values.
- Raw program/listing text, source URLs, 1,500 HTML pages, hashes, and page
  journals preserve traceability.
- `applicant_data.json` and `llm_extend_applicant_data.json` are valid JSON
  arrays containing 30,000 records each.
- The instructor's local TinyLlama package added the required standardized
  program and university fields without changing any source field or row order.
- urllib, BeautifulSoup, regex, and string operations perform URL management and
  parsing. Browser rendering is limited to the normal manually verified public
  session; challenge interaction is never automated.
- Robots evidence is included in `screenshot.jpg`, with policy provenance and
  access history documented in README.md and ACCESS_EVENTS.md.
- Installation, execution, resume, validation, edge cases, and limitations are
  documented. Sphinx API documentation builds with warnings as errors.
- 89 automated tests pass; dependency checking passes; runtime Pylint is
  10.00/10.

## Data verification

The independent auditor does not call the production parser. It checked 510,001
values against the saved HTML, all page hashes, all URL identities, and the
source page supporting each record. It found zero mismatches, duplicates,
unbacked URLs, or normalization defects. `FINAL_VALIDATION.md` records exact
hashes, counts, outcome distribution, and model-preservation checks.

The data faithfully represents public applicant-submitted listings. That does
not guarantee that each applicant claim is true. Unusual values, jokes, spam,
missing years, and source abbreviations remain source data rather than being
silently rewritten.

## Ethical and access safeguards

The collector reads public pages only, honors the applicable robots policy,
paces requests sequentially, and stops on authentication, rate limiting,
verification, rejection, stale pagination, or an unknown layout. There is no
Cloudflare solver, login automation, proxy rotation, restriction bypass, PII
enrichment, or fabricated record path. The required manual verification step is
preserved.

## User-controlled steps before submission

- Confirm the private GitHub repository is shared with the grader.
- Push the final verified data/documentation commit before the deadline.
- Submit the matching `module_2` archive and SSH repository URL through Canvas.

Canvas submission and grader access are not asserted because they require the
student's account and final confirmation.
