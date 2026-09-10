# Final validation

Validated September 9-10, 2026 on the frozen production source snapshot.

## Deliverables

- `applicant_data.json`: 30,000 records and 30,000 unique applicant URLs.
- `llm_extend_applicant_data.json`: 30,000 records in identical source order.
- Saved evidence: 1,500 source HTML pages plus matching page journals.
- Frozen source SHA-256:
  `2a8379981058fb1a0b359b3d03883ff83fd5fdf32c6c4dee64bd0d535f8343fa`.
- Extended output SHA-256:
  `256acd32d60c1ec8fdc4935bbea45562c9fefbbd385aac97c2fa7dc4247a6f36`.

The frozen snapshot and current `applicant_data.json` were byte-equivalent at
cleaning time. The snapshot remains ignored local recovery material, not a
third submission dataset.

## Independent source audit

`audit_data.py` independently read the saved HTML rather than calling the
production parser. It checked 510,001 extracted values, all 30,000 URLs, all
1,500 page hashes, and source-to-page membership. There were zero mismatches,
unbacked URLs, duplicate URLs, or whitespace normalization defects.

Outcome counts are 11,193 accepted, 14,079 rejected, 2,707 waitlisted, and
2,021 interview entries. Eight source listings omit a usable program name;
their value is retained as `null` rather than guessed. Other missing fields are
also represented consistently as JSON `null`.

## Local model audit

The instructor-supplied TinyLlama package ran locally using two workers and six
threads per worker. It processed 600 restartable batches and validated 30,000
records in 8,896.5 seconds. Independent comparison found:

- zero source-field changes;
- zero identity or order changes;
- zero missing generated fields;
- zero generated HTML tags or encoded HTML entities; and
- eight `Unknown` generated programs corresponding to the eight absent source
  program names; no generated university is unknown.

The two generated fields supplement rather than replace the original values.
Their standardization is model output guarded by source-supported canonical
matching; source authenticity does not imply that applicant-submitted claims
are true.

## Software verification

- 89 automated tests pass.
- `pip check` reports no broken requirements.
- Pylint reports 10.00/10 on the runtime modules.
- Sphinx documentation builds with warnings treated as errors.

Canvas submission and grader repository access are user-controlled final steps
and are not asserted here.
