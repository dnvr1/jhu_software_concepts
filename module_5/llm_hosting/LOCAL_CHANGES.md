# Local compatibility and accuracy changes

The files in this directory came from the instructor's `llm_hosting-1-1.zip`
(Canvas file 19121115). The supplied Flask service, local TinyLlama model,
few-shot prompt, and canonical lists remain the basis of the solution.

Changes made for this assignment:

- Removed obsolete `force_filename` and `local_dir_use_symlinks` parameters from
  `hf_hub_download`, compatible with the installed Hugging Face Hub 1.30.0.
- Added a postprocessor that checks model suggestions against the separate
  source `program_name` and `university`. Exact canonical source matches win;
  another canonical name must have at least 0.90 spelling similarity to be
  accepted. Unlisted names stay as the source provided them. Legacy inputs
  containing only the combined `program` retain the supplied behavior.
- Added Artificial Intelligence and Jewish Studies to `canon_programs.txt`;
  added University of Dhaka and Friedrich-Schiller Universität Jena to
  `canon_universities.txt`. These are names observed in the real captured batch.
- The surrounding `clean.py` adapter calls `app.py --file ... --stdout`, reads
  its actual JSONL output, and creates the required final JSON array. It launches
  Python with `-X utf8` to preserve accented source text on Windows, validates
  record identity, and accepts only the two additional standardized fields.

The initial actual-model review exposed misspellings such as `Artificial
Intellegenence`, `University of Dhaaka`, and `Jewiš Studies`. The source guard
prevents these inventions. It deliberately leaves unfamiliar abbreviations
unchanged until a reviewed alias/canonical entry can support the expansion.
The original input fields are never overwritten by model suggestions.

Verified runtime: Windows, Python 3.12.6, llama-cpp-python 0.2.90 official CPU
wheel, TinyLlama 1.1B Chat Q4_K_M, N_THREADS=8, CPU only. The 420-record model run
completed; all original fields were compared and preserved, with both added
standardization fields present for every record. This is a partial dataset;
the assignment still requires at least 30,000 actual applicant records.
