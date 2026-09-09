# Module 2 compliance checkpoint

This is a development checkpoint, not a completed submission.

## Verified

- Tested interpreter: Python 3.12.6, Windows x64.
- Root requirements.txt includes the complete pinned environment.
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

1. Establish that the source results are accessible without account login.
   The later Codex browser redirected to sign-in; its sample is kept separate
   under ignored tmp/. Matching older public captures does not prove the
   authenticated workflow meets the assignment's public-only restriction.
2. Run the standalone Python collector successfully against permitted public
   pages on a small batch. Browser capture plus Python parsing is not proof
   of standalone end-to-end collection.
3. Audit that batch against source HTML and verify safe resume. Never mix
   old-parser journals with newly parsed rows or retry a recorded access block.

## Gates before submission

- Reach at least 30,000 genuine entries, then refresh and audit the LLM output.
- Confirm the exact Canvas due date and grader repository access.
- Push incremental verified changes; submit the matching archive and SSH URL
  only when the assignment is complete and submission is authorized.

No Cloudflare solver, proxy rotation, login automation, or fabricated records
are included. A blocked source is a stop condition, not a reason to switch
transports. Source authenticity means faithful extraction, not a guarantee
that applicant-submitted claims are true.
