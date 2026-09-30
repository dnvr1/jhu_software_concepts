"""Keep source contracts documented using Google-style argument sections."""

import ast
import pathlib
import re

import pytest


@pytest.mark.integration
def test_source_docstrings_and_arguments():
    """Require docstrings and named argument entries without importing code."""
    source = pathlib.Path(__file__).resolve().parents[1] / "src"
    failures = []
    for path in sorted(source.glob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"))
        if not ast.get_docstring(tree):
            failures.append(f"{path.name}: missing module docstring")
        for node in ast.walk(tree):
            if not isinstance(
                node, (ast.ClassDef, ast.FunctionDef, ast.AsyncFunctionDef)
            ):
                continue
            location = f"{path.name}:{node.lineno} {node.name}"
            doc = ast.get_docstring(node) or ""
            if not doc:
                failures.append(f"{location}: missing docstring")
            if isinstance(node, ast.ClassDef):
                continue
            arguments = [
                *node.args.posonlyargs, *node.args.args, *node.args.kwonlyargs
            ]
            arguments += [
                arg for arg in (node.args.vararg, node.args.kwarg)
                if arg is not None
            ]
            section = re.search(
                r"(?:^|\n)Args:\n(.*?)(?=\n\w[^\n]*:\n|\Z)",
                doc, re.DOTALL,
            )
            entries = section.group(1) if section else ""
            for arg in arguments:
                if arg.arg in {"self", "cls"}:
                    continue
                pattern = (
                    rf"^\s+\*{{0,2}}{re.escape(arg.arg)}"
                    r"(?:\s*\([^\n]+\))?:"
                )
                if not re.search(pattern, entries, re.MULTILINE):
                    failures.append(f"{location}: undocumented {arg.arg}")
    assert not failures, "\n".join(failures)
