# apps/benchmark-runner/stages

One stage per run kind, called by `apps/benchmark-runner/pipeline.py`.

```
__init__.py : package of the run driver's stages: discover, benchmark, check, harness, interop, and their steps
benchmark.py : the plain run's benchmark: device passes and sessions or host processes, warm-up, dry pass, not_measured, analysis
capture_files.py : the capture, trial and requirements a discovery wrote, by path and paired by stamp; never the newest in a kept folder; the reuse that probed again
check.py : --check run: every planned case once through the real harness (host CheckKt, device EndToEndCheck under the dry run), check.yaml, its summary and failures
discover.py : discover and configure: probe or host discovery, ConfigureKt, effective.yaml summary, staged then published under the capture's device id
harness.py : --harness run: scope generation, the harness's device check, interop verdicts into checked/
interop.py : --interop run: the plan's pairs on the host or device, published beside a finished run or as a new device folder
interop_oracle.py : oracle steps of a --interop run: plan staging, host InteropKt, device InteropCheck, summary
known_answers.py : --check's known-answers.yaml: the guide's vectors filled per provider, global.yaml's selection.knownVectors
measuring.py : what a run's device sessions share: the Measuring context, the thermal gate's start, session and pass arguments, timed hooks, ConvertKt, per-process files
not_measured.py : planned timed cases the final benchmark.json lacks: one not_measured line each, recorded in the manifest
```
