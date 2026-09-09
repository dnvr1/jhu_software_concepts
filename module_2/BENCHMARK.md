# Local LLM benchmark

Measured on the Core Ultra 9 285K (24 logical CPUs), using the first 100 saved
applicants, the supplied TinyLlama CPU model, and two equal 50-record batches.
Configurations ran sequentially with separate fresh result caches. Times include
child-process startup, model loading, inference, validation, and merging.
Model weights were already downloaded. This is one trial per configuration,
not a statistically conclusive estimate or a full-dataset runtime promise.

| Workers | Threads per worker | Seconds | Records/minute |
| --- | --- | --- | --- |
| 1 | 8 | 49.568 | 121.04 |
| 1 | 12 | 45.053 | 133.18 |
| 2 | 6 | 34.539 | 173.72 |

Two six-thread workers were fastest: about 30% less elapsed time than the
eight-thread baseline. Use this as the initial configuration and remeasure if
collection or other heavy work competes for resources. All three produced
identical standardized name pairs and preserved every source field and order.
These checks establish preservation and cross-configuration agreement, not the
semantic correctness of every model-generated name.

## Run on saved data

```powershell
.\.venv\Scripts\python.exe parallel_clean.py --file applicant_data.json --workers 2 --threads 6 --work-dir tmp/parallel-clean --output llm_extend_applicant_data.json
```

Each batch has its own input, output, and cache. Parent-only aggregation preserves
input order and publishes the final output only after all batches pass. A worker
failure leaves the prior final output untouched; validated batch caches can be
reused on restart. Do not run two coordinators against the same work directory
or output. Use a frozen input snapshot while collecting; never have concurrent
writers updating the same final JSON. Website collection remains sequential and
throttled. This benchmark made no GradCafe requests and did not modify either
primary dataset.

Reproduce with `python parallel_clean.py --benchmark` in the project environment.
Fresh timestamp-independent temporary directories prevent accidental result-cache
hits. Detailed local artifacts are in tmp/llm-bench-yeepafjp for this trial.

The project test suite passes 56 tests, including order preservation, isolated
batch output, CPU-thread limits, and failure-before-publication behavior.
