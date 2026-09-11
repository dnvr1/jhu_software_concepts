# Module 2: Web Scraping

Student: Denver Clarke (`dclar106`)

Course: EN.605.256, Modern Software Concepts in Python

Due: September 13, 2026 at 11:59 p.m. Eastern

Repository: `git@github.com:dnvr1/jhu_software_concepts.git`

## Result

This project collected **30,000 unique public GradCafe entries** and produced
**30,000 matching local TinyLlama outputs**. An independent audit compared
510,001 source values against 1,500 saved HTML pages with zero mismatches. Every
source field and row order is preserved in the extended output. All 89 tests
pass. See `FINAL_VALIDATION.md` for hashes and detailed counts.

Primary deliverables:

- `applicant_data.json`: scraped and conservatively parsed source data.
- `llm_extend_applicant_data.json`: the same records plus standardized program
  and university fields from the instructor-supplied local model.

## Setup

Python 3.10 or newer is required; the verified environment used Python 3.12.6
on Windows x64.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On macOS or Linux, replace `.venv\Scripts\python.exe` with
`.venv/bin/python`. The pinned requirements include BeautifulSoup, the local
LLM runtime, pytest, Pylint, and Sphinx. No paid API or secret key is required.

## Collection approach

`scrape.py` uses urllib for URL validation, robots policy handling, and permitted
requests. BeautifulSoup, regex, and string methods parse the applicant table.
`browser_collect.py` attaches to a dedicated Chrome or Edge session when normal
browser rendering is required.

The browser workflow deliberately retains the assignment's manual step:

1. Python opens or attaches to a dedicated browser profile at `robots.txt`.
2. The user completes any ordinary browser verification manually and remains
   signed out.
3. Python validates the visible policy, follows genuine cursor links, saves the
   displayed DOM, and parses the public listings.
4. Collection stops on login evidence, a challenge, HTTP rejection, rate
   limiting, stale pagination, or an unfamiliar layout.

There is no CAPTCHA solver, login automation, proxy rotation, restriction
bypass, private-data collection, or fabricated-record path. Requests are
sequential and paced. `screenshot.jpg`, `raw/robots_check.json`, and
`ACCESS_EVENTS.md` record robots and access evidence.

Run a small isolated test first:

```powershell
.\.venv\Scripts\python.exe browser_collect.py --browser chrome --target 40 --output tmp\smoke.json --raw-dir tmp\smoke-raw
.\.venv\Scripts\python.exe audit_data.py --file tmp\smoke.json --raw-dir tmp\smoke-raw
```

After reviewing the sample, collect or safely resume the primary dataset:

```powershell
.\.venv\Scripts\python.exe browser_collect.py --browser chrome --target 30000
```

The collector commits each page to `raw/` before updating the aggregate JSON.
Its checkpoint resumes after interruption, rejects mixed parser schemas, and
deduplicates by stable applicant URL. Do not run two collectors against the
same output directory. Direct urllib collection is also available when public
requests are permitted:

```powershell
.\.venv\Scripts\python.exe scrape.py --target 30000 --delay 6
```

## Data fields

Each source object contains:

| Fields | Meaning |
| --- | --- |
| `program`, `program_name`, `university` | Combined model input and separate displayed names. |
| `comments`, `date_added`, `url` | Public comment, listing date, and stable result URL. |
| `status`, `decision_date` | Displayed admission outcome and date. |
| `acceptance_date`, `rejection_date` | Outcome-specific dates when applicable. |
| `term`, `citizenship`, `degree` | Start term, origin label, and Masters/PhD/other displayed degree. |
| `gpa`, `gre`, `gre_v`, `gre_aw`, `gre_quantitative` | Explicitly labeled numeric metrics. |
| `score_provenance`, `comment_score_mentions`, `score_context` | Evidence for structured and narrative scores. |
| `raw_program`, `raw_text`, `source_url` | Original visible text and supporting page URL. |

Missing values use JSON `null`. Markup and display whitespace are normalized,
but missing years, scores, outcomes, institutions, and degree meanings are not
guessed. Comments never overwrite labeled badges. Narrative score extraction is
conservative and documented in `SCORE_POLICY.md`. The saved HTML provides full
traceability.

## Local LLM cleaning

`clean.py` invokes the supplied `llm_hosting/app.py`, preserves every input
field, and accepts only `llm-generated-program` and
`llm-generated-university`. Batches are cached and identity-checked before the
final JSON is published.

Single-process command:

```powershell
.\.venv\Scripts\python.exe clean.py --file applicant_data.json --output llm_extend_applicant_data.json --llm-dir llm_hosting --batch-size 100
```

The completed production run used the benchmarked two-worker configuration on
an immutable local snapshot:

```powershell
.\.venv\Scripts\python.exe parallel_clean.py --file tmp\final_30000_input_20260909.json --workers 2 --threads 6 --work-dir tmp\parallel-clean-final-30000 --output llm_extend_applicant_data.json
```

The model processed and validated all records in 8,896.5 seconds. Eight source
listings lacked a usable program name, so their generated program is `Unknown`
instead of an invented value. Model safeguards and canonical-list changes are
documented in `llm_hosting/LOCAL_CHANGES.md`; performance measurements are in
`BENCHMARK.md`.

## Verification

```powershell
.\.venv\Scripts\python.exe audit_data.py --file applicant_data.json --raw-dir raw
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m pip check
.\.venv\Scripts\python.exe -m pylint audit_data.py storage.py scrape.py browser_collect.py clean.py parallel_clean.py
.\.venv\Scripts\python.exe -m sphinx -W --keep-going -b html docs docs\_build\html
```

Final results: 30,000 records, 30,000 unique URLs, zero source mismatches, 89
passing tests, no broken dependencies, runtime Pylint 10.00/10, and a clean
warning-as-error Sphinx build.

## Limitations and submission

The parser supports the inspected layout and stops if it changes. The public
feed can change between runs. Displayed dates without years remain without
years, abbreviations stay conservative, and unusual or false applicant claims
remain source data without being endorsed.

Before submitting, confirm the private repository invitation for `Dibakar58`
has been accepted, push the final commit, and upload the matching `module_2` ZIP
plus repository SSH URL to Canvas. Exclude `.venv`, `tmp`, caches, dedicated
browser profiles, model weights, and generated documentation builds. Canvas
submission remains the student's responsibility.
