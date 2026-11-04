# Shared functions: scripts and tools

| function | module | rule | callers |
|---|---|---|---|
| `ONE_PASSED` | `scripts/device/adb.py` | `re.compile('^OK \\(1 test\\)', re.M)` | session.case_isolation, stages.interop_oracle |
| `PASSED` | `scripts/device/adb.py` | `re.compile('^OK \\(\\d+ tests?\\)', re.M)` | energy_session, session.measure, session.warmup |
| `instrumentation_report(output)` | `scripts/device/adb.py` | - | energy_session, stages.interop_oracle |
| `read(device)` | `scripts/device/clocks.py` | `parse(device.shell(READ))` | device.facts, session.clocks_hook |
| `capture_id(capture)` | `scripts/device/identity.py` | `device_id((yaml.safe_load(capture.read_text()) or {}).get('runtime') or {})` | stages.discover, stages.harness, stages.interop |
| `device_id(runtime)` | `scripts/device/identity.py` | - | pipeline, results.manifest, stages.discover |
| `read(device)` | `scripts/device/thermal.py` | - | session.thermal_gate, session.thermal_hook, session.warmup |
| `case_cooldown(document)` | `scripts/effective_view.py` | `(document.get('run') or {}).get('caseCooldownSeconds') or 0` | stages.benchmark, stages.harness |
| `entry_count(document)` | `scripts/effective_view.py` | `sum((len(names) for types in (document.get('providers') or {}).values() for names in types.values()))` | explain, stages.discover |
| `isolation(document)` | `scripts/effective_view.py` | - | stages.benchmark, stages.harness |
| `read(effective_file)` | `scripts/effective_view.py` | - | stages.benchmark, stages.discover, stages.harness |
| `thermal_gate(document)` | `scripts/effective_view.py` | run.thermalGate as :config validated it, or None when absent or enabled false. | stages.benchmark, stages.measuring |
| `throttle_sleep(document)` | `scripts/effective_view.py` | None keeps Jetpack's own sleep; RunSettings already refused a negative value. | stages.benchmark, stages.harness |
| `guarded(problems, step)` | `scripts/energy_stage.py` | An energy step that fails costs this process its energy, never its timing: one error line, recorded. | session.energy_hook, stages.benchmark |
| `source(effective, python, stacktrace)` | `scripts/energy_stage.py` | `SOURCES[source_name(effective)](Host(python, stacktrace, android_home() / 'platform-tools', ...` | stages.benchmark, stages.harness |
| `fail(message)` | `scripts/failure.py` | - | dependencies, effective_view, global_file, gradle_runner +8 |
| `one_line(error)` | `scripts/failure.py` | `' '.join(str(error).split())[:500]` | energy_stage, facade.py, gradle_runner, pipeline +1 |
| `global_config(argument)` | `scripts/global_file.py` | - | dependencies, pipeline |
| `run(project, arguments, stacktrace, stream, main_class, notices)` | `scripts/gradle_runner.py` | notices, when given, collects every passed-on line, so a caller can record it. | session.passes, stages.benchmark, stages.discover, stages.interop_oracle +1 |
| `map_blocks(path, text)` | `scripts/lint/markdown.py` | - | docs_lint, lint.tree |
| `is_doc(path)` | `scripts/lint/paths.py` | `not is_guide(path) and 'docs' in local(path).split('/')[:-1]` | docs_lint, lint.markdown |
| `join(base, rel)` | `scripts/lint/paths.py` | `posixpath.normpath(posixpath.join(base, rel)) if base else posixpath.normpath(rel)` | docs_lint, lint.tree |
| `router_of(path)` | `scripts/lint/paths.py` | `next((r for r in ROUTERS if r and path.startswith(r + '/')), '')` | docs_lint, lint.tree |
| `ROOT` | `scripts/repo.py` | `pathlib.Path(__file__).resolve().parent.parent` | dependencies, device.facts, energy_stage, explain +11 |
| `publish(stage, target, discovery_mode)` | `scripts/results/layout.py` | Everything staged moves in; the old manifest goes first, because a folder with one is a finished run. | stages.discover, stages.interop |
| `staged(root)` | `scripts/results/layout.py` | - | stages.discover, stages.interop |
| `warn_if_temp(path)` | `scripts/results/layout.py` | - | pipeline, stages.harness |
| `manifest(results, mode, configuration, files, problems)` | `scripts/results/manifest.py` | - | pipeline, stages.harness, stages.interop |
| `digests(global_file)` | `scripts/results/run_inputs.py` | Parsed, not raw: a comment or a reordered key reruns nothing; the bundled list is its own input; analysis only | pipeline, results.manifest |
| `device_folders(root)` | `scripts/results/select.py` | - | none |
| `generate(harness_path, root, out, compiler)` | `scripts/scope/generate.py` | - | scope_generate, stages.harness |
| `expression(parameter, scope)` | `scripts/scope/inputs.py` | - | scope.generate, scope.wrapper |
| `kind(type_text)` | `scripts/scope/inputs.py` | `KINDS.get(normalised(type_text))` | scope.interop, scope.wrapper |
| `of(name)` | `scripts/scope/languages.py` | `LANGUAGES[name]` | scope.dependencies, scope.generate, scope.wrapper |
| `listed(output)` | `scripts/session/case_isolation.py` | The timed cases the device planned, in its order: AndroidJUnitRunner's -e log true lists them and runs none. | session.measure, stages.benchmark |
| `process_folder(root, repetition, repetitions)` | `scripts/session/measure.py` | `root if repetitions == 1 else root / f'process-{repetition}'` | session.passes, stages.benchmark |
| `run_session(device, plan, repetitions, isolation, hooks, folder, problems)` | `scripts/session/measure.py` | folder(repetition) is the process's folder; a case that failed is one problem line, a process that measured none the run's failure. | stages.benchmark, stages.harness |
| `read(document, captures)` | `scripts/session/passes.py` | The run's passes in the order written; none configured is the single pass. | stages.benchmark, stages.harness |
| `run_all(chosen, repetitions, root, measure_one, options)` | `scripts/session/passes.py` | measure_one(pass, folder, written) runs one pass's session; returns the per-process files the manifest lists. | stages.benchmark, stages.harness |
| `run(device, test_class, arguments, planned, cases, document)` | `scripts/session/warmup.py` | One process over the chosen cases; a failure warns and the session goes on. Returns the cases it ran. | stages.benchmark, stages.harness |
| `parsed(global_file)` | `scripts/stages/config_check.py` | `parse_all([pathlib.Path(global_file)])[0]` | pipeline, stages.discover |
| `convert(run, arguments)` | `scripts/stages/measuring.py` | ConvertKt on one process; a case that did not get the samples it asked for is a problem the manifest records. | stages.benchmark, stages.harness |
| `energy_preflight(options, source, session, discovery, files)` | `scripts/stages/measuring.py` | - | stages.benchmark, stages.harness |
| `gated(run, document)` | `scripts/stages/measuring.py` | `dataclasses.replace(run, gate=thermal_gate.start(run.device, effective_view.thermal_gate(document)))` | stages.benchmark, stages.harness |
| `pass_arguments(run, one)` | `scripts/stages/measuring.py` | `tuple(measure_arguments(run.options.suppress_errors, one.metrics, run.throttle_sleep)) + one.arguments()` | stages.benchmark, stages.harness |
| `push(device, options, plan, energy)` | `scripts/stages/measuring.py` | dex2oat runs in the AOT compile, so the energy settle comes after it, never before; energy.yaml follows the settle. | stages.benchmark, stages.harness |
| `record(files, into, captures, device)` | `scripts/stages/measuring.py` | - | stages.benchmark, stages.harness |
| `session_arguments(run, document)` | `scripts/stages/measuring.py` | `measure_arguments(run.options.suppress_errors, effective_view.metrics(document), run.throttle_sleep)` | stages.benchmark, stages.harness |
| `singles(files, repetitions)` | `scripts/stages/measuring.py` | - | stages.benchmark, stages.harness |
| `thermal_flag(process)` | `scripts/stages/measuring.py` | - | stages.benchmark, stages.harness |
| `timed_hooks(run, one, isolation)` | `scripts/stages/measuring.py` | The cool-down, then the gate, so a case's start temperature and clocks are read after both. | stages.benchmark, stages.harness |
| `elapsed(label, started)` | `scripts/stages/took.py` | - | stages.benchmark, stages.discover, stages.harness, stages.interop +1 |
| `run(step, command)` | `scripts/timeouts.py` | - | device.adb, gradle_runner, scope.compile, stages.benchmark |
| `capture(node, default)` | `tools/energy/capture.py` | `_energy(node).get('capture', default)` | dependencies, energy, energy_stage |
| `source(node, default)` | `tools/energy/capture.py` | `_energy(node).get('source', default)` | dependencies, energy_stage |
| `one_line(error)` | `tools/energy/energy.py` | `' '.join(str(error).split())[:200] or type(error).__name__` | none |
| `one_line(error)` | `tools/energy/manafa_estimate.py` | `' '.join(str(error).split()) or type(error).__name__` | manafa_session |
| `case_arguments(captures_found, capability, preparation, data, traces, dry_calls, out)` | `tools/energy/sources/runner.py` | - | sources.manafa_source, sources.rails_source |
| `load(benchmark_file, prepared_file, effective_file)` | `tools/quick-bench/chart_input.py` | - | analyze, charts |
| `settings(effective)` | `tools/quick-bench/chart_input.py` | - | analyze, charts |
| `count_metrics(raw_cases)` | `tools/quick-bench/chart_model.py` | The metrics a run carries besides timeNs, in the order first seen; only those with at least one run. | analyze, charts |
| `short(algorithm)` | `tools/quick-bench/chart_model.py` | `re.sub('(PKCS5Padding\|NoPadding\|AndMGF1Padding\|/ECB)', '', algorithm).strip('-/')` | chart_draw, chart_report |
| `size_label(size)` | `tools/quick-bench/chart_model.py` | `'n-a' if size is None else f'{size}B' if size < 1024 else f'{size // 1024}KiB'` | chart_draw, chart_report |
| `summarize_count(case, groups, metric)` | `tools/quick-bench/chart_model.py` | One case's runs of a count metric, as measured: no unit conversion. None when the case has no runs for it. | analyze, charts |
| `variant(case)` | `tools/quick-bench/chart_model.py` | ' fixed' or ' notFixed' after a case's name, so an item's two variants never read as one; empty for a row without one. | analyze, chart_draw, chart_report |
| `latency(ns, units)` | `tools/quick-bench/display_units.py` | `ns / NS_PER[units['latency']]` | analyze, chart_draw, chart_model |
| `latency_label(units)` | `tools/quick-bench/display_units.py` | `f"{units['latency']}/op"` | analyze, chart_draw, chart_model |
| `throughput(ns, size, units)` | `tools/quick-bench/display_units.py` | None where the unit needs an input size the case does not have, or the time is zero. | analyze, chart_model |
| `summarize(runs)` | `tools/quick-bench/stats.py` | - | analyze, chart_model |
