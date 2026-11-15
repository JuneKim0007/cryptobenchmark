# apps/benchmark-runner/stages

One stage per run kind, called by `apps/benchmark-runner/pipeline.py`.

```
__init__.py : package of the run driver's stages still in the runner: benchmark, check, harness, interop, and their steps
benchmark.py : the plain run's benchmark: device passes and sessions or host processes, warm-up, dry pass; whether it timed anything, for the analysis
check.py : --check run: every planned case once through the real harness (host CheckKt, device EndToEndCheck under the dry run), check.yaml, its summary and failures
harness.py : --harness run: scope generation, the harness's device check, interop verdicts into checked/
interop.py : --interop run: the plan's pairs on the host or device, published beside a finished run or as a new device folder
interop_oracle.py : oracle steps of a --interop run: plan staging, host InteropKt, device InteropCheck, summary
known_answers.py : --check's known-answers.yaml: the guide's vectors filled per provider, global.yaml's selection.knownVectors
measuring.py : what a run's device sessions share: the Measuring context, the thermal gate's start, session and pass arguments, timed hooks, ConvertKt, per-process files
```
