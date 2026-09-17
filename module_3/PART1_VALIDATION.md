# Part 1 Validation

Validated on September 15, 2026 against PostgreSQL 17 on Windows.

## Initial load

```text
Source records: 30,000
Usable unique records: 30,000
Duplicate source URLs skipped: 0
Rows before load: 0
Rows inserted: 30,000
Rows after load: 30,000
Unique URLs after load: 30,000
Schema and primary-key verification: passed
```

## Repeated load

```text
Source records: 30,000
Usable unique records: 30,000
Duplicate source URLs skipped: 0
Rows before load: 30,000
Rows inserted: 0
Rows after load: 30,000
Unique URLs after load: 30,000
Schema and primary-key verification: passed
```

The repeated run confirms that the unique URL constraint and
`ON CONFLICT (url) DO NOTHING` prevent unnecessary duplicate records. The
loader's live schema check also confirmed the required columns, data types,
identity column, `p_id` primary key, and unique stored URLs.

## Automated checks

```text
tests/test_load_data.py: 4 passed
Python compilation: passed
Git whitespace validation: passed
Credential pattern scan: no matches
```
