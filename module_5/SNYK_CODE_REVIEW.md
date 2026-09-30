# Snyk Code extra-credit review

Snyk Code was enabled with the account owner's approval on September 30, 2026.
Executed from `module_5/`: `snyk code test --json-file-output=snyk-code-results.json`.
The capture helper is `tools/capture_snyk_code.py`. Snyk analyzed the Module 5
source, including inherited optional CLI utilities, rather than only `src/`.

## Results and remediation

| Scan | High | Medium | Low | Total |
| --- | ---: | ---: | ---: | ---: |
| Initial | 0 | 3 | 23 | 26 |
| After HTML escaping | 0 | 2 | 23 | 25 |

Both scans completed with findings (CLI exit code 1). This is not an
authentication failure or a claim of zero issues. No findings were suppressed
or ignored. Original CLI output and SARIF JSON are preserved in
`snyk-code-initial.txt` / `.json` and `snyk-code-analysis.txt` /
`snyk-code-results.json`.

The medium XSS finding in `tools/capture_receiver.py` traced a local capture
filename into an HTML response. The success message now HTML-escapes the
filename, and the form also escapes its token attribute. A focused rendering
check verified escaping of quotes and HTML delimiters. The second Snyk scan
no longer reports this finding.

## Remaining findings and trust boundaries

- **Two medium command-execution findings:** `src/clean.py` invokes an
  operator-selected Python interpreter and local model package;
  `tools/browser_collect.py` launches an operator-selected browser executable.
  Both pass argument lists and use the default `shell=False`; shell
  metacharacters are not intentionally interpreted. However, an untrusted
  executable/package choice or compromised environment can still execute
  arbitrary code. These capabilities are intentional local CLI features and
  are not driven by Flask request parameters. Run only trusted executables,
  model packages and environment settings. These findings remain open, not
  categorically dismissed as false positives.
- **22 low path-traversal findings:** local scraper, cleaner, model and
  evidence utilities accept operator-selected input/output paths. These are
  not web-request paths, but they can read/write files with the operator's
  permissions. Do not run untrusted command lines or elevate these tools.
  A future multi-user service would need a fixed workspace allowlist and
  symlink-aware path containment before accepting remote filenames.
- **One low hardcoded-credential finding:** the test role name
  `gradcafe_app` in `tools/verify_least_privilege.py` is fixed so grants and
  verification refer to the same role. It is a public identifier, not a
  password. Its password is generated with `secrets.token_urlsafe(32)` per
  disposable CI run, retained in process memory and not printed. No secret
  value was hardcoded or removed as part of this finding's review.

The required Snyk dependency scan is separate and reported zero dependency
issues. SAST findings are documented here without suggesting that passing
dependency scans proves source-code security. Extra-credit grading remains
the instructor's decision.
