# Narrative score policy (schema 3)

Structured website badges take precedence. Labeled numbers in comments are
retained in comment_score_mentions, with the exact label, value, stated scale
or null, original excerpt and character offsets. All original comments remain
unchanged. No GPA conversion, GRE sum, score clamping, or missing scale is guessed.

A unique labeled mention can fill an empty scalar field only when no ambiguous
context is detected. Its score_provenance is comment_labeled_narrative and
score_context supplies the label, scale and excerpt. CGPA remains labeled CGPA
in that context even when represented in the assignment's GPA field. Generic
GRE remains generic: never assume every gre value is a total or a component.

Historical degrees, third-party statements, requirements, targets, negations,
multiple competing mentions and inconsistent scales are not auto-filled.
Review flags preserve candidates for inspection. This conservative heuristic
can over-flag legitimate applicant scores and cannot understand every narrative.
It is not an assertion of exhaustive free-text extraction.

## 1,000-record replay results

Only three previously empty scalar values changed:

| Applicant | Field | Value | Source wording |
| --- | --- | --- | --- |
| 1020343 | gpa | 1.2 | GPA of 1.2 |
| 1019889 | gpa | 8.49 | CGPA of 8.49 |
| 1019889 | gre | 318 | GRE score of 318 |

Both GPA scales above remain null because a denominator was not explicitly
attached to those values. The complete original comments provide context.
No previously populated score or non-score source field was changed.

Five mentions remain review-only:

- 1020122: GPA 3.75 in a comment mentioning a master's degree.
- 1019890: Portuguese GPA 15.4/20 following a bachelor's description.
- 1019534: CGPA 8.58 and GRE 310 in a comment saying GRE was not submitted.
- 1019472: GPA 3.9/4 explicitly attached to M.S. studies.

The mentions remain numeric structured evidence even when the main metric
remains null. Repeated values can be found without re-scraping the website.
For 1019720, badge GPA 3.7 and GRE 165 remain untouched; alternative comment
values GPA 5.49/6 and GRE 329/340 are retained separately.

Before semester-long analysis, select compatible scales and score types.
Do not average all GPA or GRE values indiscriminately, infer that null scale
means 4.0/340, or treat source submissions as verified claims.

70 automated tests pass. The replay audit reports 17,001 comparisons without
mismatches, with narrative scalar fills additionally checked against exact
source excerpts. All 1,000 records remain unique and backed by source HTML.

Use replay_saved.py to migrate preserved HTML into a fresh directory. The
scraper rejects old schemas, and replay retains any previously recorded access
stop. Never delete a blocked checkpoint to restart requests.
