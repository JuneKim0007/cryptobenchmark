# apps/benchmark-runner/stages

One stage per run kind, called by `apps/benchmark-runner/pipeline.py`.

```
__init__.py : package of the run driver's stages still in the runner: benchmark, harness, and their steps
benchmark.py : the plain run's benchmark: device passes and sessions or host processes, warm-up, dry pass; whether it timed anything, for the analysis
harness.py : --harness run: scope generation, the harness's device check, interop verdicts into checked/
measuring.py : what a run's device sessions share: the Measuring context, the thermal gate's start, session and pass arguments, timed hooks, ConvertKt, per-process files
```
