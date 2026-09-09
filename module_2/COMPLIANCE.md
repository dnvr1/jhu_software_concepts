# Module 2 compliance checkpoint

This is a development checkpoint, not a completed submission.

Latest: 1,000 source entries and 1,000 matching local LLM outputs. Narrative
score handling is documented in SCORE_POLICY.md; 70 tests pass. Earlier counts
below describe prior checkpoints. Collection has not resumed beyond 1,000.

## Verified

- Tested interpreter: Python 3.12.6, Windows x64.
- Root requirements.txt includes the complete pinned environment.
- 51 automated tests pass; dependency check reports no broken requirements.
- Refreshed 420-row source and local LLM outputs preserve every source field.
- Incremental code and data commits were pushed: 4d4bc30 and fca0659.
- GitHub repository dnvr1/jhu_software_concepts is private.
- Python parser uses urllib, BeautifulSoup, regex, and string methods.
- 420 unique source records are preserved with raw HTML and per-page journals.
- A separate 40-record source audit performed 760 field comparisons and
  40 raw-text checks without table/badge mismatches or missing/duplicate rows.
- One explicit comment declaration supplied missing GRE verbal and writing
  scores. The parser now records 159 and 4, with provenance; quantitative 165
  is separate from the site's generic GRE field. No total is invented.
- Original program text, outcomes, dates, comments, and unusual score values
  are retained. Missing values are JSON null.
- Actual instructor-supplied local LLM runs add two standardized fields without
  replacing original fields. No paid API or secret credentials are required.
- Robots evidence and its transcription/provenance are included.

## Gates before collecting more

1. Public access has been verified for two pages after normal account logout;
   see PUBLIC_ACCESS.md. Continue only while pages remain public and permitted.
2. Run the standalone Python collector successfully against permitted public
   pages on a small batch. Browser capture plus Python parsing is not proof
   of standalone end-to-end collection.
3. Audit that batch against source HTML and verify safe resume. Never mix
   old-parser journals with newly parsed rows or retry a recorded access block.

## Gates before submission

- Reach at least 30,000 genuine entries, then refresh and audit the LLM output.
- Submit by Sunday, September 13, 2026 at 11:59 p.m. Eastern (user-confirmed
  Sunday midnight, using the PDF's 11:59 p.m. submission target).
- Confirm grader repository access.
- Push incremental verified changes; submit the matching archive and SSH URL
  only when the assignment is complete and submission is authorized.

No Cloudflare solver, proxy rotation, login automation, or fabricated records
are included. A blocked source is a stop condition, not a reason to switch
transports. Source authenticity means faithful extraction, not a guarantee
that applicant-submitted claims are true.
