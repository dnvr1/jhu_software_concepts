"""Sphinx configuration for the Module 2 public Python APIs."""

from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

project = "Module 2: GradCafe Web Scraping"
extensions = ["sphinx.ext.autodoc", "sphinx.ext.napoleon"]
napoleon_google_docstring = True
napoleon_numpy_docstring = False
html_theme = "alabaster"
exclude_patterns = ["_build"]
