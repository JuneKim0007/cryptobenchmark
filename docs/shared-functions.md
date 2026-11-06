# Shared functions: benchmark runner, cli and tools

| function | module | rule | callers |
|---|---|---|---|
| `load(benchmark_file, prepared_file, effective_file)` | `apps/benchmark-runner/analysis/chart_input.py` | - | analyze, charts |
| `settings(effective)` | `apps/benchmark-runner/analysis/chart_input.py` | - | analyze, charts |
| `count_metrics(raw_cases)` | `apps/benchmark-runner/analysis/chart_model.py` | The metrics a run carries besides timeNs, in the order first seen; only those with at least one run. | analyze, charts |
| `short(algorithm)` | `apps/benchmark-runner/analysis/chart_model.py` | `re.sub('(PKCS5Padding\|NoPadding\|AndMGF1Padding\|/ECB)', '', algorithm).strip('-/')` | chart_draw, chart_report |
| `size_label(size)` | `apps/benchmark-runner/analysis/chart_model.py` | `'n-a' if size is None else f'{size}B' if size < 1024 else f'{size // 1024}KiB'` | chart_draw, chart_report |
| `summarize_count(case, groups, metric)` | `apps/benchmark-runner/analysis/chart_model.py` | One case's runs of a count metric, as measured: no unit conversion. None when the case has no runs for it. | analyze, charts |
| `variant(case)` | `apps/benchmark-runner/analysis/chart_model.py` | ' fixed' or ' notFixed' after a case's name, so an item's two variants never read as one; empty for a row without one. | analyze, chart_draw, chart_report |
| `latency(ns, units)` | `apps/benchmark-runner/analysis/display_units.py` | `ns / NS_PER[units['latency']]` | analyze, chart_draw, chart_model |
| `latency_label(units)` | `apps/benchmark-runner/analysis/display_units.py` | `f"{units['latency']}/op"` | analyze, chart_draw, chart_model |
| `throughput(ns, size, units)` | `apps/benchmark-runner/analysis/display_units.py` | None where the unit needs an input size the case does not have, or the time is zero. | analyze, chart_model |
| `summarize(runs)` | `apps/benchmark-runner/analysis/stats.py` | - | analyze, chart_model |
| `ONE_PASSED` | `apps/benchmark-runner/device/adb.py` | `re.compile('^OK \\(1 test\\)', re.M)` | session.case_isolation, stages.interop_oracle |
| `PASSED` | `apps/benchmark-runner/device/adb.py` | `re.compile('^OK \\(\\d+ tests?\\)', re.M)` | energy_session, session.measure, session.warmup |
| `instrumentation_report(output)` | `apps/benchmark-runner/device/adb.py` | - | energy_session, stages.interop_oracle |
| `read(device)` | `apps/benchmark-runner/device/clocks.py` | `parse(device.shell(READ))` | device.facts, session.clocks_hook |
| `capture_id(capture)` | `apps/benchmark-runner/device/identity.py` | `device_id((yaml.safe_load(capture.read_text()) or {}).get('runtime') or {})` | stages.discover, stages.harness, stages.interop |
| `device_id(runtime)` | `apps/benchmark-runner/device/identity.py` | - | pipeline, results.manifest, stages.discover |
| `read(device)` | `apps/benchmark-runner/device/thermal.py` | - | session.thermal_gate, session.thermal_hook, session.warmup |
| `entry_count(document)` | `apps/benchmark-runner/effective_view.py` | `sum((len(names) for types in (document.get('providers') or {}).values() for names in types.values()))` | explain, stages.discover |
| `read(effective_file)` | `apps/benchmark-runner/effective_view.py` | - | stages.benchmark, stages.discover |
| `thermal_gate(document)` | `apps/benchmark-runner/effective_view.py` | run.thermalGate as :config validated it, or None when absent or enabled false. | stages.benchmark, stages.measuring |
| `capture(node, default)` | `apps/benchmark-runner/energy/capture.py` | `_energy(node).get('capture', default)` | dependencies, energy, energy_stage |
| `source(node, default)` | `apps/benchmark-runner/energy/capture.py` | `_energy(node).get('source', default)` | dependencies, energy_stage |
| `one_line(error)` | `apps/benchmark-runner/energy/energy.py` | `' '.join(str(error).split())[:200] or type(error).__name__` | none |
| `one_line(error)` | `apps/benchmark-runner/energy/manafa_estimate.py` | `' '.join(str(error).split()) or type(error).__name__` | manafa_session |
| `case_arguments(captures_found, capability, preparation, data, traces, dry_calls, out)` | `apps/benchmark-runner/energy/sources/runner.py` | - | sources.manafa_source, sources.rails_source |
| `guarded(problems, step)` | `apps/benchmark-runner/energy_stage.py` | An energy step that fails costs this process its energy, never its timing: one error line, recorded. | session.energy_hook, stages.benchmark |
| `fail(message)` | `apps/benchmark-runner/failure.py` | - | dependencies, effective_view, global_file, gradle_runner +9 |
| `one_line(error)` | `apps/benchmark-runner/failure.py` | `' '.join(str(error).split())[:500]` | energy_stage, facade.py, gradle_runner, pipeline +1 |
| `global_config(argument)` | `apps/benchmark-runner/global_file.py` | - | dependencies, pipeline |
| `run(arguments, stacktrace, stream, main_class, notices)` | `apps/benchmark-runner/gradle_runner.py` | notices, when given, collects every passed-on line, so a caller can record it. | session.passes, stages.benchmark, stages.discover, stages.interop_oracle +1 |
| `ROOT` | `apps/benchmark-runner/repo.py` | `RUNNER.parents[1]` | explain, global_file, pipeline, scope.code_digest |
| `publish(stage, target, discovery_mode)` | `apps/benchmark-runner/results/layout.py` | Everything staged moves in; the old manifest goes first, because a folder with one is a finished run. | stages.discover, stages.interop |
| `staged(root)` | `apps/benchmark-runner/results/layout.py` | - | stages.discover, stages.interop |
| `warn_if_temp(path)` | `apps/benchmark-runner/results/layout.py` | - | pipeline, stages.harness |
| `manifest(results, mode, configuration, files, problems)` | `apps/benchmark-runner/results/manifest.py` | - | pipeline, stages.harness, stages.interop |
| `digests(global_file)` | `apps/benchmark-runner/results/run_inputs.py` | Parsed, not raw: a comment or a reordered key reruns nothing; the bundled list is its own input; analysis only | pipeline, results.manifest |
| `device_folders(root)` | `apps/benchmark-runner/results/select.py` | - | none |
| `generate(harness_path, root, out, compiler)` | `apps/benchmark-runner/scope/generate.py` | No scope compiled still writes an empty catalog, so no failed scope's source is left to break the test APK. | scope_generate, stages.harness |
| `expression(parameter, scope, side)` | `apps/benchmark-runner/scope/inputs.py` | `side` picks the provider a key pair is decoded by: another provider's key class is converted at every init, a cost on one side only. | scope.generate, scope.wrapper |
| `kind(type_text)` | `apps/benchmark-runner/scope/inputs.py` | `KINDS.get(normalised(type_text))` | scope.interop, scope.wrapper |
| `of(name)` | `apps/benchmark-runner/scope/languages.py` | `LANGUAGES[name]` | scope.dependencies, scope.generate, scope.wrapper |
| `listed(output)` | `apps/benchmark-runner/session/case_isolation.py` | The timed cases the device planned, in its order: AndroidJUnitRunner's -e log true lists them and runs none. | session.measure, stages.benchmark |
| `process_folder(root, repetition, repetitions)` | `apps/benchmark-runner/session/measure.py` | `root if repetitions == 1 else root / f'process-{repetition}'` | session.passes, stages.benchmark |
| `parsed(global_file)` | `apps/benchmark-runner/stages/config_check.py` | `parse_all([pathlib.Path(global_file)])[0]` | pipeline, stages.discover |
| `push(device, options, plan, energy)` | `apps/benchmark-runner/stages/measuring.py` | dex2oat runs in the AOT compile, so the energy settle comes after it, never before; energy.yaml follows the settle. | stages.benchmark, stages.harness |
| `elapsed(label, started)` | `apps/benchmark-runner/stages/took.py` | - | stages.benchmark, stages.discover, stages.harness, stages.interop +1 |
| `run(step, command)` | `apps/benchmark-runner/timeouts.py` | - | device.adb, gradle_runner, scope.compile, stages.benchmark |
| `clean(token)` | `tools/lint/markdown.py` | `re.sub('#.*$', '', re.sub(':\\d.*$', '', token.strip()))` | lint.claims, lint.tree |
| `map_blocks(path, text)` | `tools/lint/markdown.py` | - | docs_lint, lint.tree |
| `is_doc(path)` | `tools/lint/paths.py` | `not is_guide(path) and 'docs' in local(path).split('/')[:-1]` | docs_lint, lint.markdown |
| `join(base, rel)` | `tools/lint/paths.py` | `posixpath.normpath(posixpath.join(base, rel)) if base else posixpath.normpath(rel)` | docs_lint, lint.claims, lint.tree |
| `router_of(path)` | `tools/lint/paths.py` | `next((r for r in ROUTERS if r and path.startswith(r + '/')), '')` | docs_lint, lint.claims, lint.tree |
