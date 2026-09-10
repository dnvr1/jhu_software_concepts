Name: Denver Clarke
JHED ID: dclar106
Module: 2 - Assignment: Web Scraping, EN.605.256
Due: Sunday, September 13, 2026 at 11:59 p.m. Eastern
Repository: git@github.com:dnvr1/jhu_software_concepts.git

Final result:
The Python collector saved 30,000 unique public GradCafe records in
applicant_data.json. Each row is backed by one of 1,500 saved HTML pages and a
page journal. The instructor-supplied local TinyLlama package then produced
llm_extend_applicant_data.json with the same 30,000 rows plus
llm-generated-program and llm-generated-university. No paid API was used.

Approach:
browser_collect.py attaches to a normal manually verified Chrome session.
Python checks robots.txt, follows source cursor links, waits between pages,
captures the displayed DOM, and stops on challenges, authentication, rejection,
or an unfamiliar layout. It never automates verification. scrape.py uses urllib,
BeautifulSoup, regex, and string operations for URL handling and parsing.
Storage is atomic, page journals support safe resume, and URL identity prevents
duplicates. Missing values are JSON null; raw program/listing text and source
URLs remain available for traceability.

Cleaning:
parallel_clean.py ran the supplied local model with two workers and six threads
per worker against a frozen source snapshot. It completed 600 restartable
batches and validated all 30,000 outputs in 8,896.5 seconds. Every source field
and row order is unchanged. Both required generated fields are populated on all
rows. Eight listings with no usable source program are conservatively labeled
Unknown in the generated program field instead of being invented.

Verification:
An independent HTML audit made 510,001 source-field comparisons with zero
mismatches, checked all 1,500 page hashes, and found no duplicates or unbacked
URLs. The software suite passes 89 tests, pip reports no broken requirements,
runtime Pylint is 10.00/10, and Sphinx builds with warnings treated as errors.
See README.md, FINAL_VALIDATION.md, SCORE_POLICY.md, and COMPLIANCE.md for full
commands, field definitions, hashes, safeguards, and limitations.

Remaining user-controlled submission steps:
Confirm grader access to the private repository, push the final verified commit,
zip the matching module_2 folder, and submit the archive plus SSH URL in Canvas.
Canvas submission has not been performed by Codex.
