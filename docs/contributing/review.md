# Review

Tools that back a review with numbers. They are installed outside the repo, so no project dependency is added:
- `T=~/capstone/tools/venv/bin`, created with `python3 -m venv ~/capstone/tools/venv && $T/pip install lizard radon vulture`
- `ruff` from the system
- `jscpd` through `npx`
- `jdeps` from the JDK

## Rules
- evidence: every review finding cites a command's output or a file:line; a reading alone is not a finding.
- dead code: a tool's hit is a candidate; grep the symbol (code, tests, YAML keys, CLI registration, reflection) before deleting.
- proof: a refactor diffs the dry-run outputs before and after (`diff -r`) and reports the result.
- runs: write run outputs under `~/capstone/runs/<date>-<name>/`, never `/tmp`.
- end to end: a change to config, catalogs, discovery or the pipeline also runs `python3 apps/benchmark-runner/pipeline.py --bench --config config/global-demo.yaml --results ~/capstone/runs/<date>-<name>/results` to exit 0; the run lands in `results/<device_id>/`; unit suites alone missed a JDK-specific name clash once.

## Commands
| Question | Command | Flag when |
|---|---|---|
| function too big or branchy | `$T/lizard -C 10 -L 60 -w apps/perf-repair/src scripts tools modules -l python -l kotlin` | CCN > 10 or > 60 lines |
| file hard to maintain (Python) | `$T/radon mi -s apps/perf-repair/src scripts tools` | grade B or worse |
| unused Python code | `$T/vulture apps/perf-repair/src scripts tools --min-confidence 60` | any hit, then grep |
| unused imports, variables, args; commented-out code | `ruff check --select F401,F841,F811,ARG,ERA apps/perf-repair/src scripts tools` | any hit |
| copy-paste, both languages | `npx -y jscpd@4 --min-tokens 60 --reporters console --ignore "**/test/**,**/tests/**,**/build/**,**/fixtures/**" apps/perf-repair/src scripts tools modules` | any clone in main code |
| untested code | `(cd apps/perf-repair && python3 -m pytest -q --cov=perfrepair --cov-report=term-missing)` | 0% files; dead-code candidates |
| Kotlin package dependencies | `jdeps -verbose:package -summary apps/benchmark/modules/<m>/build/classes/kotlin/main` | an edge against `docs/contributing/code.md` |
| change hotspots | `git log --since='30 days' --format= --name-only -- '*.py' '*.kt' \| sort \| uniq -c \| sort -rn \| head` | high churn with high CCN |
| one file, one responsibility | lizard's per-file function list + the file's imports + `git log --format=%s -- <file>` | functions or commits falling into unrelated clusters |
