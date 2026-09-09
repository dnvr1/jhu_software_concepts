Name: Denver Clarke
JHED ID: dclar106
Module: 2 - Assignment: Web Scraping, EN.605.256.
Due date: Sunday at 11:59 p.m. in the provided PDF; confirm dated Canvas deadline.
Repository: git@github.com:dnvr1/jhu_software_concepts.git

Approach:
scrape.py uses urllib for URL construction, validation, robots.txt checking, and
permitted requests. BeautifulSoup groups admission table rows and extracts the
public applicant fields. For the currently verified browser workflow,
capture_receiver.py saves the displayed HTML and its original URL locally;
scrape.py imports these saved pages. Cursor Next links are taken from the source.
Requests are throttled and collection stops on rejection or verification.
Per-page HTML and JSON journals preserve evidence and allow safe resume after
interruption. Applicant URLs deduplicate records. applicant_data.json is written
atomically, with consistent null values for unavailable data.

clean.py performs conservative text cleaning and adapts the actual instructor
llm_hosting/app.py local model, preserving all source fields while adding
llm-generated-program and llm-generated-university. Model batches are cached for
resume, and their record identities are checked before accepting model output.
No paid API, secret key, or fabricated source/model data is used.

Known unfinished requirements:
The genuine collection contains 420 rows, below the 30,000 target. The actual
instructor package is included and a TinyLlama CPU run standardized all 420
records. Every original field was verified unchanged in the extended JSON.
Manual verification is needed when the site challenges
the browser. The parser supports the actual inspected table layout and stops on
unknown layouts. Displayed dates without years remain without years, and source
abbreviations can remain unexpanded by the conservative model guard. Source
spam/false claims remain source data, without asserting their truth.

The standalone browser_collect.py launches or attaches to a normal dedicated
Chrome/Edge session. After the user manually verifies the site, Python checks
robots.txt before navigating to results, follows cursor links, and saves/resumes
data. Test with --target 40 in a separate output/raw directory and audit all
fields before increasing the target. No challenge or restriction is bypassed.
The browser starts on robots.txt, not the results page. Do not sign in. Login
and authenticated-account markers stop capture; recorded stops prevent retries.
Old or mixed record schemas are rejected before recovery writes.

All 420 primary records were replayed from saved HTML after the GRE audit fix,
and the local LLM was rerun. Every refreshed source field is preserved in its
extended counterpart. The previous snapshot is backed up locally under tmp/.

The audited 40-record sample used Codex browser capture and Python parsing;
it was not a successful standalone Python collection run. That browser required
sign-in, so no larger collection is authorized until unauthenticated public
access is established. No authenticated data beyond that separate sample is to
be collected. GitHub metadata confirms the repository is private; Module 2
publication and grader access remain pending.

Model changes and four observed canonical additions are documented in
llm_hosting/LOCAL_CHANGES.md. requirements-lock.txt reconstructs the verified
Python 3.12.6 Windows environment, including the official llama.cpp CPU wheel.
Root requirements.txt includes that lock file, so one installation covers the
scraper, local model runtime, tests, and documentation tools.

README.md contains complete installation/run/resume commands, robots evidence
and provenance, field definitions, validation commands, edge cases, and final
submission steps. docs/ contains buildable Sphinx API documentation. Tests use
synthetic examples only within temporary test directories.
