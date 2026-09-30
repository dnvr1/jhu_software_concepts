# Python style and documentation

Module 5 uses the [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
as its style reference, particularly section 3.8 on comments and docstrings.
Pylint is the checking tool, not the name of the guide.

## Documentation conventions

- Start modules, classes, functions, and methods with meaningful docstrings.
- Use Google-style `Args:`, `Returns:`, `Yields:`, `Raises:`, and `Attributes:`
  sections as applicable. Do not add empty sections or a `Returns: None` section.
- Explain input constraints, output shape, mutation, transaction ownership,
  concurrency, and observable failure modes where callers need that information.
- Use type annotations when available; otherwise include types in the `Args:`
  entries. Simple no-argument expression builders may use a concise docstring.
- Write implementation comments about *why* an operation is necessary, especially
  at trust boundaries. Avoid narrating obvious assignments or every line.
- Keep credentials and personal data out of comments, examples, and logs.

The security helpers explain identifier allowlisting versus value binding,
bounded query results, and the distinction between result limits and aggregate
work. Loader comments describe commit/rollback behavior. Scraper documentation
explains policy stops and durable recovery; background-job comments explain why
the worker releases the lock acquired by the request thread.

## Automated checks

`pyproject.toml` selects Google-style parsing in Pylint's `docparams` extension
and requires parameter documentation. Sphinx Napoleon explicitly renders Google
docstrings. The source documentation test checks every source module/class/
function for a docstring and every function argument for an `Args:` entry.

```powershell
.\.venv\Scripts\python.exe -m pylint src --fail-under=10
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m sphinx -W --keep-going -b html docs docs/_build/html
```

## Project-specific choices

This is a Google-guided project, not a claim that every recommendation is
mechanically enforced. Lines are limited to 79 characters (within Google's
80-character limit). Existing direct symbol imports and test-patching seams
are retained rather than changing application APIs during a documentation edit;
Google generally prefers module imports. Existing imperative docstring summaries
remain consistent within modules; the guide permits descriptive or imperative
style. SQLAlchemy's dynamic API needs narrowly documented lint exceptions.
Design thresholds and the 1,200-line parser-module limit are explicit in
`pyproject.toml`; the latter accommodates detailed recovery documentation.
Third-party instructor code in `llm_hosting/` is not restyled.

A 10/10 Pylint score verifies the configured checks, not full Google-guide
compliance or the semantic accuracy of every comment. Review and tests remain
necessary. Historical Snyk/CI screenshots retain their original run identity;
documentation-only changes do not make those historical scans new scans.
