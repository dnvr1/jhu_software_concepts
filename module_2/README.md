# Module 2: Web Scraping

Final verified result: **30,000 unique public source entries** and **30,000
matching local TinyLlama outputs**. Every source row is backed by saved HTML,
all 30,000 applicant URLs are unique, and an independent audit made 510,001
source-field comparisons with zero mismatches. The LLM output preserves every
source field and source order while adding the two required generated fields.
The test suite passes 89 tests. See `FINAL_VALIDATION.md` for hashes, counts,
field coverage, and the exact validation scope.

This Python project collects public GradCafe admission listings, preserves source
HTML and applicant text, and runs the instructor's local LLM standardization
step. No applicant records or model results are fabricated. Historical bounded
tests and checkpoints remain documented for traceability.

Student name: **Denver Clarke**. JHED ID: **dclar106**.
Course: EN.605.256, Modern Software Concepts in Python.
Assignment: Module 2 - Assignment: Web Scraping.
Due date: Sunday, September 13, 2026. The user confirmed Sunday at midnight;
the submission target is 11:59 p.m. Eastern that Sunday, consistent with the
assignment PDF. Repository SSH URL:
`git@github.com:dnvr1/jhu_software_concepts.git`.

## Setup

Use Python 3.12.6 on Windows x64 to reproduce the pinned environment (meeting
the assignment's Python 3.10+ requirement). From `module_2`:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On macOS/Linux use `.venv/bin/python` in place of the Windows interpreter path.
The scraper uses Python's standard `urllib` library and BeautifulSoup. Selenium
is not used. The capture receiver uses the standard library; the standalone
browser collector also uses websocket-client. Root `requirements.txt` includes
`requirements-lock.txt`, covering the local LLM runtime and documentation tools
as well as scraping. This uses the project's official CPU wheel index for
`llama-cpp-python`, avoiding a local C++ build. See the
[upstream installation instructions](https://github.com/abetlen/llama-cpp-python).

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-lock.txt
```

## Approach and robots evidence

The public `https://www.thegradcafe.com/robots.txt` was inspected in an ordinary
browser. `screenshot.jpg` records the policy. The wildcard policy allows `/`;
separate policies disallow named bots. The scraper identifies itself as
`JHU-Module2-EducationalScraper/1.0`, parses the applicable policy with
`urllib.robotparser`, and checks each requested URL, including redirects and
pagination links. A saved policy is not permission to bypass an access challenge.

The existing `browser_captures/robots.txt` is a transcription of the directives
visible in the verified browser, not a claimed byte-for-byte download. The
screenshot is the visual evidence. When importing it, the scraper archives that
policy and saves its hash, check time, method, and user agent in
`raw/robots_check.json`. A fresh live run requests robots.txt first. An unreadable
or denying policy stops collection before result requests.

During this implementation, GradCafe presented a Cloudflare verification screen.
After the user completed normal browser verification, the results became visible
and their actual DOM was captured from the same browser session. This follows the
instructor's September 7 hybrid-capture note. No challenge solver, alternate proxy,
login automation, or browser security override is included.

Access limitation: the later Codex-browser session redirected to sign-in, and
the user signed in before the 40-record audit capture. Those 40 records match
earlier public captures, but this does not establish an independently runnable,
unauthenticated collection workflow. That sample remains separate under `tmp/`.
Do not collect more data through authenticated sessions or treat account login
as an assignment-approved workaround. A subsequent normal logout check verified
that both tested admissions pages load while signed out; see PUBLIC_ACCESS.md.
This resolves the public-access question for those pages, not the remaining
standalone Python live test or future pages.

`urllib.parse` constructs and validates URLs. The current site uses **cursor-based
Next links**; the scraper follows the exact source link instead of guessing page
numbers. A filename such as `page-000002.html` means the second saved capture,
not an invented `?page=2` URL. Its `.meta.json` sidecar preserves the actual URL.

BeautifulSoup groups each main table row with its following metadata/comment
rows. It extracts school, program, displayed degree, date added, outcome,
displayed decision date, term, applicant type, and labeled scores. Only comment
elements contribute comments; a duplicated mobile decision badge is not a
comment. Ads and navigation are excluded. Unrecognized pages stop collection.

## Collect and resume

The reproducible normal-browser workflow is a Python script. First run a small
batch into a separate directory, then compare all fields with its saved HTML
before increasing the target:

```powershell
.\.venv\Scripts\python.exe browser_collect.py --browser edge --target 40 --output tmp/python_smoke/applicant_data.json --raw-dir tmp/python_smoke/raw
```

The script opens a visible normal Edge browser using a dedicated local profile.
Chrome is also supported with `--browser chrome`. Complete normal verification
yourself on robots.txt without signing into an account, then press Enter.
Python checks the policy before navigating to results, captures a JPEG, follows real
cursor links, and saves actual DOM pages and applicant records. No challenge
handling is automated. Login/account UI, a challenge, or a rejected document
stops the script. A saved stop prevents subsequent automatic retries.

For an existing dedicated session, use `--attach --port PORT`; the script refuses
to launch over an occupied debugging port. It accepts the site's observed
trailing-slash redirect but requires the exact cursor and a changed first
applicant before accepting the next page, preventing stale SPA captures. The
local debugging port is bound to loopback and the dedicated profile is ignored
by Git. The browser stays open for the user after the script exits.

After the small-batch source audit passes, increase `--target` on that same
output/raw directory to resume. The completed production command used the
default output/raw paths:

```powershell
.\.venv\Scripts\python.exe browser_collect.py --browser edge --target 30000
```

The 30,000-record run completed. Do not run both collection modes against the
same output/checkpoint concurrently.

When direct public requests are permitted and no previous request has been
blocked, the standalone collector is:

```powershell
.\.venv\Scripts\python.exe scrape.py --target 30000 --delay 6
```

It makes sequential requests with a six-second minimum interval by default,
increased to honor robots crawl-delay/request-rate. HTTP rejection, rate limiting,
verification pages, repeated pages, or changed layouts stop the run. A recorded
live stop persists in the checkpoint so restarting does not repeatedly retry a
blocked site. Do not run a second transport to get around such a block.

For the instructor-approved capture workflow, manually open a normal Chrome or
Edge browser and complete normal verification yourself. Once the public results
are visible, save the displayed DOM to the local capture helper:

```powershell
.\.venv\Scripts\python.exe capture_receiver.py
```

Open the localhost address printed by the helper. Use a browser helper capable
of reading the displayed DOM (the connected browser was used here) to fill the
form with the source URL and current HTML. The receiver only saves local files;
it does not request GradCafe, advance pages, or interact with verification. Move
to the real Next link in that same verified browser with reasonable pauses, and
close unused tabs. Stop if a challenge or restriction reappears. The initial
manual setup remains necessary on a new computer/session.

Parse all available saved pages and safely append new applicant URLs:

```powershell
.\.venv\Scripts\python.exe scrape.py --html-dir browser_captures --robots-file browser_captures/robots.txt --target 30000
```

Exit code 0 means the requested count was reached, 2 means a valid partial
collection was saved, and 1 means collection stopped on an error/restriction.
Repeat the import after more actual pages are captured. Completed pages are
skipped and applicant URLs are deduplicated. Never delete progress to resume.

Every accepted page has a preserved HTML file, SHA-256 hash, source URL,
capture/import time, next URL, and per-page JSON journal under `raw/`. The journal
is committed before the aggregate and checkpoint. Restart replays journals to
recover an interrupted write or rebuild a missing aggregate without requesting
pages again. The submitted `applicant_data.json` is an atomic JSON array.

## Data and local LLM cleaning

Each object uses these consistent fields:

| Fields | Meaning |
| --- | --- |
| `program`, `program_name`, `university` | `program` combines the displayed program and school for the instructor's expected model input; the other fields retain each source component. |
| `comments`, `date_added`, `url` | Public listing comment, displayed addition date, stable applicant-entry URL. |
| `status`, `decision_date`, `acceptance_date`, `rejection_date` | Outcome and only the dates actually displayed. |
| `term`, `citizenship`, `degree` | Displayed start semester/year, origin label, and degree. |
| `gre`, `gre_v`, `gre_aw`, `gpa` | Labeled numeric metrics; absent values are JSON `null`. |
| `gre_quantitative`, `score_provenance` | Explicit quantitative score and per-metric source labels, introduced in the audited 40-record batch. |
| `raw_program`, `raw_text`, `source_url` | Original visible program-cell text including degree, listing text, and source page URL. Full HTML is also archived. |

Basic cleaning decodes entities, removes markup, normalizes display whitespace,
and converts numeric score strings. Original raw fields are retained. All absent
values use `null`; no outcome, missing year, score, or institution is guessed.
An exact whole-comment declaration of GRE quantitative/verbal/writing scores
can fill missing metrics, with provenance; it never overrides a badge. Schema 3
also preserves labeled narrative mentions and fills only unique unambiguous
missing scores. See SCORE_POLICY.md for scale and ambiguity handling.
Quantitative is separate from the generic `gre` field, and a
total score is never inferred. All 30,000 records were independently checked
against the saved source pages with consistent score provenance. The final local
LLM run preserves every source field. See COMPLIANCE.md and FINAL_VALIDATION.md
for audit scope.
The scraper refuses old or mixed journal schemas rather than silently combining
them with new records; replay saved HTML into a separate directory to migrate.

The actual instructor Canvas file **19121115** (`llm_hosting-1-1.zip`) is extracted
under `module_2/llm_hosting`. The user provided the package after its initial
download was blocked. Its supplied TinyLlama 1.1B Chat Q4_K_M GGUF model was
downloaded publicly from Hugging Face and executed on the local CPU with eight
threads. Model weights are cached in `llm_hosting/models` and excluded from Git;
a fresh machine downloads them on the first run. No paid API or secret
credentials are required.

```powershell
.\.venv\Scripts\python.exe -m pip install --only-binary=llama-cpp-python --extra-index-url https://abetlen.github.io/llama-cpp-python/whl/cpu -r llm_hosting/requirements.txt
```

Run the checked adapter for a simple single-process execution:

```powershell
.\.venv\Scripts\python.exe clean.py --file applicant_data.json --output llm_extend_applicant_data.json --llm-dir llm_hosting --batch-size 100
```

If the package uses a separate Python environment, pass its interpreter with
`--python`. The adapter runs the supplied `app.py --file` in small local batches.
The supplied app emits JSONL with `--stdout`; the adapter accepts JSONL or a
JSON array and writes the final required JSON array. It requires the fields
`llm-generated-program` and `llm-generated-university`. It preserves the input
objects and accepts only those added model fields, checking record count,
original program text, and identity. Successful batches are cached in
`.llm_cache` using input, model configuration, and package/canonical-file hashes;
restart reuses them. Changing canonical lists or model configuration invalidates
the cache. The final extended
JSON is replaced only when every batch succeeds. The cache is not submission
data and is ignored by Git.

The completed optimized run used two workers with six CPU threads each against
an immutable source snapshot:

```powershell
.\.venv\Scripts\python.exe parallel_clean.py --file tmp\final_30000_input_20260909.json --workers 2 --threads 6 --work-dir tmp\parallel-clean-final-30000 --output llm_extend_applicant_data.json
```

It validated and merged all 30,000 records in 8,896.5 seconds. The snapshot is
an ignored local safety copy; `applicant_data.json` is its verified submitted
equivalent.

Changes to the supplied package are documented in `llm_hosting/LOCAL_CHANGES.md`.
Deprecated Hugging Face download arguments were removed. The adapter invokes
Python in UTF-8 mode so Windows stdout cannot corrupt source accents. Reviewed
model errors included `Artificial Intellegenence`, `Dhaaka`, and `Jewiš Studies`.
A source-supported postprocessor now prefers exact canonical source matches and
accepts a changed canonical model suggestion only for a close spelling variant
(similarity at least 0.90). Unrecognized names retain the source text. The model
is still invoked for each record; the guard limits unsupported changes.

Four observed names were added to the provided canonical lists: Artificial
Intelligence, Jewish Studies, University of Dhaka, and Friedrich-Schiller
Universität Jena. Original program/university fields remain untouched. This
conservative guard can leave unfamiliar abbreviations unexpanded; that is an
explicit limit requiring reviewed canonical/alias updates, not guessed data.

## Verification, documentation, and limitations

For measured local processing optimization, see BENCHMARK.md. The fastest tested
configuration was two independent model workers with six threads each. Run
`parallel_clean.py --workers 2 --threads 6 --work-dir tmp/parallel-clean --output llm_extend_applicant_data.json`
on a frozen source file. Workers have separate caches; the parent validates and
merges in source order. This does not increase website request concurrency.

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements-dev.txt
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m sphinx -W --keep-going -b html docs docs/_build/html
.\.venv\Scripts\python.exe -c "from scrape import load_data; d=load_data(); print('Records:', len(d), 'Unique URLs:', len({r['url'] for r in d})); assert len(d) >= 30000"
```

The final assertion passes for the submitted 30,000-record dataset.
Tests use explicitly synthetic fixtures in temporary directories; they never
write synthetic records into the deliverable. They cover parsing, null values,
mobile badges, cursor links, comment/score separation, robots rejection, block
stopping, deduplication, crash recovery, and LLM identity/cache behavior. Code
uses four-space indentation, descriptive names, Google-style public API
docstrings, and a 79-character formatter configuration. Sphinx uses Napoleon to
render those docstrings. No grade or perfect style score is claimed.

Known limits: CAPTCHA interaction remains manual; the
HTML parser supports the observed layout and deliberately stops when that
layout changes. A newly changing live results feed can shift between captures;
cursor links and URL deduplication reduce repeated entries but cannot freeze
the source site. `Sep 08` decision dates retain their missing year. `MFA` remains
`MFA` instead of being guessed as another degree. University acronyms and program
abbreviations are preserved for the actual model/canonical-list stage. Raw
scores are not silently clamped to expected ranges, and comments mentioning a
different GPA do not overwrite the labeled score. Public submissions may contain
spam, false claims, unusual scores, or jokes. Such source entries are retained
without asserting their truth or rewriting their contents.

Before submitting, confirm the repository is shared with the grader, push the
final verified commit before the deadline, and submit the matching zipped
`module_2` folder plus SSH URL through Canvas. Meaningful code and data
checkpoints were pushed throughout development. Canvas submission has not been
performed.

Repository metadata was checked through GitHub: `dnvr1/jhu_software_concepts`
is private. Grader access remains unverified. The current suite passes 89 tests,
the completed source collection contains 30,000 unique records, and the extended
file contains 30,000 matching locally cleaned records.
