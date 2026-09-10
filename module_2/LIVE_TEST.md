# Live Python collection checkpoint

Historical checkpoint: the production collector subsequently completed 30,000
records. See README.md and FINAL_VALIDATION.md for the final result.

The normal Edge browser connection works without the Edge extension. Robots
policy was checked by Python before results collection. No account login,
challenge solver, or proxy was used.

The first live attempt exposed a transient DOM timing error. The snapshot now
handles a missing document root, and navigation waits for a results table, not
just document completion. A regression test covers the loading transition.
The local code-error stop was reviewed before recovery; no remote block was
cleared. The existing loaded page was captured using the Python collector's
classes, followed by its actual Next URL: 40 unique records.

The production browser_collect.py CLI then resumed the same checkpoint with
target 60, collected only page 3, and exited successfully. All 60 records are
unique. Required/supporting fields match the previously saved source dataset;
raw_text and source_url were excluded from equality because whole-document
capture and trailing-slash URLs differ from the earlier table-only captures.
Raw HTML and exact source URLs are retained in the local test artifacts.

52 tests pass. The live test is under ignored tmp/python_smoke; the primary
dataset remains 420 records. The 30,000-record requirement is not complete.
