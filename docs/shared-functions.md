# Shared functions: benchmark runner, cli, tools and lib

| function | module | rule | callers |
|---|---|---|---|
| `load(benchmark_file, prepared_file, effective_file)` | `apps/benchmark-runner/analysis/chart_input.py` | - | analyze, charts |
| `settings(effective)` | `apps/benchmark-runner/analysis/chart_input.py` | - | analyze, charts |
| `count_metrics(raw_cases)` | `apps/benchmark-runner/analysis/chart_model.py` | The metrics a run carries besides timeNs, in the order first seen; only those with at least one run. | analyze, charts |
| `short(algorithm)` | `apps/benchmark-runner/analysis/chart_model.py` | `re.sub('(PKCS5Padding\|NoPadding\|AndMGF1Padding\|/ECB)', '', algorithm).strip('-/')` | chart_draw, chart_report |
| `size_label(size)` | `apps/benchmark-runner/analysis/chart_model.py` | `'n-a' if size is None else f'{size}B' if size < 1024 else f'{size // 1024}KiB'` | chart_draw, chart_report |
| `summarize_count(case, groups, metric)` | `apps/benchmark-runner/analysis/chart_model.py` | One case's runs of a count metric, as measured: no unit conversion. None when the case has no runs for it. | analyze, charts |
| `variant(case)` | `apps/benchmark-runner/analysis/chart_model.py` | ' fixed' or ' notFixed' after a case's name, so an item's two variants never read as one; empty for a row without one. | analyze, chart_draw, chart_report |
| `read(device)` | `apps/benchmark-runner/device/thermal.py` | - | session.dynamic_temperature, session.thermal_hook, session.warmup |
| `one_line(error)` | `apps/benchmark-runner/energy/energy.py` | `' '.join(str(error).split())[:200] or type(error).__name__` | none |
| `one_line(error)` | `apps/benchmark-runner/energy/manafa_estimate.py` | `' '.join(str(error).split()) or type(error).__name__` | manafa_session |
| `case_arguments(captures_found, capability, preparation, data, traces, dry_calls, out)` | `apps/benchmark-runner/energy/sources/runner.py` | - | sources.manafa_source, sources.rails_source |
| `guarded(problems, step)` | `apps/benchmark-runner/energy_stage.py` | An energy step that fails costs this process its energy, never its timing: one error line, recorded. | session.energy_hook, stages.benchmark |
| `fail(message)` | `apps/benchmark-runner/failure.py` | - | dependencies, pipeline |
| `reported()` | `apps/benchmark-runner/failure.py` | A CommandError as fail() prints it; CommandError is imported here because dependencies.py imports this file before it checks for cryptobench. | dependencies, explain, pipeline, stages.harness |
| `global_config(argument)` | `apps/benchmark-runner/global_file.py` | - | dependencies, pipeline |
| `generate(harness_path, root, out, compiler)` | `apps/benchmark-runner/scope/generate.py` | No scope compiled still writes an empty catalog, so no failed scope's source is left to break the test APK. | scope_generate, stages.harness |
| `expression(parameter, scope, side)` | `apps/benchmark-runner/scope/inputs.py` | `side` picks the provider a key pair is decoded by: another provider's key class is converted at every init, a cost on one side only. | scope.generate, scope.wrapper |
| `kind(type_text)` | `apps/benchmark-runner/scope/inputs.py` | `KINDS.get(normalised(type_text))` | scope.interop, scope.wrapper |
| `of(name)` | `apps/benchmark-runner/scope/languages.py` | `LANGUAGES[name]` | scope.dependencies, scope.generate, scope.wrapper |
| `short_samples(data_file)` | `apps/benchmark-runner/session/calibration.py` | One coded line per benchmark whose calls per sample collapsed. | session.launch, session.measure |
| `listed(output)` | `apps/benchmark-runner/session/case_isolation.py` | The timed cases the device planned, in its order: AndroidJUnitRunner's -e log true lists them and runs none. | session.measure, stages.benchmark |
| `process_folder(root, repetition, repetitions)` | `apps/benchmark-runner/session/measure.py` | `root if repetitions == 1 else paths.Measurement(root).process(repetition).root` | session.passes, stages.benchmark |
| `parsed(global_file)` | `apps/benchmark-runner/stages/config_check.py` | `parse_all([pathlib.Path(global_file)])[0]` | pipeline, stages.discover |
| `device_discover(options, configuration, device, root)` | `apps/benchmark-runner/stages/discover.py` | A failed probe or configure leaves nothing; from here on the folder has its real name and no manifest until the run ends. | pipeline, stages.check |
| `file_beside(effective)` | `apps/benchmark-runner/stages/guide.py` | `paths.Configuration(pathlib.Path(effective).parent).guide` | stages.benchmark, stages.check |
| `elapsed(label, started)` | `lib/cryptobench/cryptobench/pipeline/took.py` | - | stages.benchmark, stages.check, stages.discover, stages.harness +2 |
| `warn(line, problems)` | `lib/cryptobench/cryptobench/pipeline/warn.py` | A warning on the terminal and, when the run keeps a list, in its manifest. | session.dynamic_temperature, stages.benchmark, stages.discover, stages.guide |
| `algorithm_id(engine_type, canonical)` | `lib/cryptobench/cryptobench/shared/catalogue/algorithms.py` | `f'{engine_type}{SEPARATOR}{canonical}'` | cryptobench.shared.catalogue.groups, cryptobench.shared.catalogue.guide_items, cryptobench.shared.catalogue.vectors, cryptobench.shared.catalogue.views |
| `algorithms()` | `lib/cryptobench/cryptobench/shared/catalogue/algorithms.py` | `load()` | cryptobench.shared.catalogue.groups, cryptobench.shared.catalogue.guide_items, cryptobench.shared.catalogue.vectors, cryptobench.shared.catalogue.views |
| `fold(name)` | `lib/cryptobench/cryptobench/shared/catalogue/names.py` | `name.upper()` | cryptobench.shared.catalogue.algorithms, cryptobench.shared.catalogue.deviations, cryptobench.shared.catalogue.groups, cryptobench.shared.catalogue.guide_items +2 |
| `override_parent(base, path)` | `lib/cryptobench/cryptobench/shared/catalogue/overrides.py` | A provider override `a.b.c`: the mapping that holds c; a list step picks the item named, or the fact, b. | cryptobench.shared.catalogue.algorithms, cryptobench.shared.catalogue.deviations |
| `provider_builds()` | `lib/cryptobench/cryptobench/shared/catalogue/provider_builds.py` | `load()` | cryptobench.shared.catalogue.algorithms, cryptobench.shared.catalogue.guide_items, cryptobench.shared.catalogue.vectors, cryptobench.shared.catalogue.views |
| `load(path)` | `lib/cryptobench/cryptobench/shared/catalogue/recipes.py` | - | cryptobench.shared.catalogue.algorithms, cryptobench.shared.catalogue.guide_items, cryptobench.shared.catalogue.vectors |
| `view_for(identifier, provider, catalogue, builds)` | `lib/cryptobench/cryptobench/shared/catalogue/views.py` | provider: a build key "<name> @ <build>", or a name one build carries; none is the base entry. Only that build's differences apply; no other build's section is kept. | cryptobench.shared.catalogue.guide_items, cryptobench.shared.catalogue.vectors |
| `ONE_PASSED` | `lib/cryptobench/cryptobench/shared/device/adb.py` | `re.compile('^OK \\(1 test\\)', re.M)` | session.case_isolation, stages.interop_oracle |
| `PASSED` | `lib/cryptobench/cryptobench/shared/device/adb.py` | `re.compile('^OK \\(\\d+ tests?\\)', re.M)` | energy_session, session.measure, session.warmup, stages.check |
| `instrumentation_report(output)` | `lib/cryptobench/cryptobench/shared/device/adb.py` | - | energy_session, stages.check, stages.interop_oracle |
| `read_runtime(path)` | `lib/cryptobench/cryptobench/shared/device/capture.py` | `runtime(read_yaml(path))` | cryptobench.shared.device.identity, device.facts |
| `read(device)` | `lib/cryptobench/cryptobench/shared/device/clocks.py` | `parse(device.shell(READ))` | device.facts, session.clocks_hook |
| `run(arguments, stacktrace, stream, main_class, notices, properties, failed)` | `lib/cryptobench/cryptobench/shared/device/gradle_runner.py` | notices, when given, collects every passed-on line, so a caller can record it; properties are -P build properties; | session.passes, stages.benchmark, stages.check, stages.discover +2 |
| `capture_id(capture)` | `lib/cryptobench/cryptobench/shared/device/identity.py` | `device_id(captured.read_runtime(capture))` | stages.discover, stages.harness, stages.interop |
| `device_id(runtime)` | `lib/cryptobench/cryptobench/shared/device/identity.py` | - | cryptobench.shared.results.manifest, pipeline, stages.discover |
| `push(device, options, plan, energy)` | `lib/cryptobench/cryptobench/shared/device/push.py` | dex2oat runs in the AOT compile, so the energy settle comes after it, never before; energy.yaml follows the settle. | stages.benchmark, stages.harness |
| `run(step, command)` | `lib/cryptobench/cryptobench/shared/device/timeouts.py` | - | cryptobench.shared.device.adb, cryptobench.shared.device.gradle_runner, scope.compile, stages.benchmark |
| `parse_yaml(text, where, code, shape, error)` | `lib/cryptobench/cryptobench/shared/document/document.py` | An empty text is an empty shape; YAML that does not parse, or parses to another shape, is `<code>: <where>: ...`. | cryptobench.shared.results.manifest, facade.index, stages.config_check, stages.discover |
| `read_yaml(path, shape)` | `lib/cryptobench/cryptobench/shared/document/document.py` | The file at path as parse_yaml reads it. | chart_input, cryptobench.shared.catalogue.interchange, cryptobench.shared.device.capture, cryptobench.shared.device.clocks +15 |
| `dump_yaml(doc, profile)` | `lib/cryptobench/cryptobench/shared/document/dump.py` | `yaml.safe_dump(doc, **profile)` | chart_report, cryptobench.shared.device.clocks, cryptobench.shared.results.manifest, device.facts +1 |
| `json_text(doc)` | `lib/cryptobench/cryptobench/shared/document/json_dump.py` | `json.dumps(doc, indent=1)` | chart_report, results.case_files, session.thermal_hook |
| `write_text(path, text, durable, exclusive, staging)` | `lib/cryptobench/cryptobench/shared/document/write.py` | durable: the file and its folder are fsync'd; exclusive: an existing file is refused, checked before staging. | cryptobench.shared.document.json_dump, cryptobench.shared.results.manifest |
| `code_in(text)` | `lib/cryptobench/cryptobench/shared/errors/coded.py` | - | cryptobench.shared.errors.failures, cryptobench.shared.errors.input_error |
| `one_line(error, limit)` | `lib/cryptobench/cryptobench/shared/errors/line.py` | `' '.join(str(error).split())[:limit]` | cryptobench.shared.device.gradle_runner, device.thermal, energy_stage, facade.py +6 |
| `android_home()` | `lib/cryptobench/cryptobench/shared/paths/host.py` | `Path(os.environ.get('ANDROID_HOME') or home() / 'Library/Android/sdk')` | cryptobench.shared.device.adb, scope.compile |
| `platform_tools()` | `lib/cryptobench/cryptobench/shared/paths/host.py` | `android_home() / 'platform-tools'` | cryptobench.shared.device.adb, energy_stage |
| `repo(root)` | `lib/cryptobench/cryptobench/shared/paths/repo.py` | `Repo(Path(root) if root is not None else roots.code_root())` | cryptobench.shared.catalogue.algorithms, cryptobench.shared.catalogue.deviations, cryptobench.shared.catalogue.families, cryptobench.shared.catalogue.glossary +23 |
| `code_root()` | `lib/cryptobench/cryptobench/shared/paths/roots.py` | $CRYPTOBENCH_CODE_ROOT, else the checkout of the script that runs, else this library's own; a script of checkout B beats a library installed from A. | cryptobench.shared.paths.repo, dead_code, facade.phases, lint.tree +6 |
| `against(settings_file, value)` | `lib/cryptobench/cryptobench/shared/paths/settings.py` | A path value of a settings file: ~ expanded, joined to the file's folder, resolved. | facade.index, stages.guide |
| `publish(stage, target, discovery_mode)` | `lib/cryptobench/cryptobench/shared/results/layout.py` | Everything staged moves in; the old manifest goes first, because a folder with one is a finished run. | stages.discover, stages.interop |
| `staged(root)` | `lib/cryptobench/cryptobench/shared/results/layout.py` | - | stages.discover, stages.interop |
| `warn_if_temp(path)` | `lib/cryptobench/cryptobench/shared/results/layout.py` | - | pipeline, stages.harness |
| `manifest(results, mode, configuration, files, problems)` | `lib/cryptobench/cryptobench/shared/results/manifest.py` | - | pipeline, stages.check, stages.harness, stages.interop |
| `digests(global_file)` | `lib/cryptobench/cryptobench/shared/results/run_inputs.py` | Parsed, not raw: a comment or a reordered key reruns nothing; the bundled list is its own input; analysis only | cryptobench.shared.results.manifest, pipeline |
| `gradle_properties(bundled)` | `lib/cryptobench/cryptobench/shared/settings/bundled.py` | `[f"-PbundledArtifacts={','.join((entry['artifact'] for entry in bundled))}"] if bundled else []` | stages.benchmark, stages.check, stages.discover |
| `entry_count(document)` | `lib/cryptobench/cryptobench/shared/settings/effective_view.py` | `sum((len(names) for types in (document.get('providers') or {}).values() for names in types.values()))` | explain, stages.discover |
| `read(effective_file)` | `lib/cryptobench/cryptobench/shared/settings/effective_view.py` | - | stages.benchmark, stages.discover |
| `thermal_gate(document)` | `lib/cryptobench/cryptobench/shared/settings/effective_view.py` | run.thermalGate as :config validated it, or None when absent. | stages.benchmark, stages.measuring |
| `capture(node, default)` | `lib/cryptobench/cryptobench/shared/settings/energy_capture.py` | `_energy(node).get('capture', default)` | dependencies, energy_stage |
| `source(node, default)` | `lib/cryptobench/cryptobench/shared/settings/energy_capture.py` | `_energy(node).get('source', default)` | dependencies, energy_stage |
| `summarize(runs)` | `lib/cryptobench/cryptobench/shared/stats/descriptive.py` | - | analyze, chart_model |
| `clean(token)` | `tools/lint/markdown.py` | `re.sub('#.*$', '', re.sub(':\\d.*$', '', token.strip()))` | lint.claims, lint.tree |
| `map_blocks(path, text)` | `tools/lint/markdown.py` | - | docs_lint, lint.tree |
| `is_doc(path)` | `tools/lint/paths.py` | `not is_guide(path) and 'docs' in local(path).split('/')[:-1]` | docs_lint, lint.markdown |
| `join(base, rel)` | `tools/lint/paths.py` | `posixpath.normpath(posixpath.join(base, rel)) if base else posixpath.normpath(rel)` | docs_lint, lint.claims, lint.tree |
| `router_of(path)` | `tools/lint/paths.py` | `next((r for r in ROUTERS if r and path.startswith(r + '/')), '')` | docs_lint, lint.claims, lint.tree |
