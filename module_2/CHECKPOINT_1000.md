# 1,000-record collection and reevaluation

Follow-up: the narrative gap below has been addressed with schema-3 extraction,
exact source evidence, and review flags. See SCORE_POLICY.md. The LLM output
has been refreshed to all 1,000 records with source fields preserved. This
document retains the original checkpoint findings for traceability.

Collection stopped successfully at exactly 1,000 records across 50 saved pages.
580 records were added to the earlier 420. All 1,000 applicant URLs are unique;
all are backed by saved HTML, and all saved HTML hashes match their manifests.
No restriction was reported during this bounded run. No collection beyond the
1,000-record target was started.

The independent audit compared 17,001 values directly with source table cells,
metadata badges, and comments: zero mismatches. This includes the narrow explicit
GRE declaration fallback. The checker does not invoke the production parser.
This verifies the compared fields, not the truth of applicant claims or full
semantic extraction of every narrative comment. 57 automated tests pass.

| Category | Populated entries |
| --- | --- |
| Program, university, date added, URL, status, term, origin, degree | 1,000 each |
| Comments | 492 |
| Acceptance date | 455 of 455 accepted |
| Rejection date | 470 of 470 rejected |
| GRE / GRE verbal / GRE writing | 62 / 64 / 61 |
| GPA | 622 |
| Raw program and listing text | 1,000 each |

## Findings requiring review before scaling

- Applicant 1019889 explicitly reports GRE 318 and CGPA 8.49 in narrative
  comments, with no score badges. Structured metrics remain null; the complete
  comment is preserved. The narrow existing declaration rule does not cover
  this format. A reviewed narrative-score extraction policy is needed.
- Applicant 1019720 has badge values GRE 165, verbal 164, writing 4, GPA 3.7,
  while the comment reports GRE 329/340 and GPA 5.49/6. These are different
  score representations/scales. Do not overwrite badges, infer conversions,
  or put component and total scores into one field without qualification.
- Scores found in narrative should preserve the exact excerpt, scale when
  given, and provenance; ambiguous historical/third-party claims should be
  flagged for review, not automatically substituted.

The data is faithful to the compared structured source, but the comment-only
score coverage issue prevents an unconditional recommendation to scale.
The original 420-record LLM output is intentionally unchanged and now trails
the 1,000-row source dataset. Refresh it after the score policy is settled.
The required final target remains 30,000, so collection is 3.33% complete.
