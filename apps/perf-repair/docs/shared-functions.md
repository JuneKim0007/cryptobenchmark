# Shared functions: perf-repair

| function | module | rule | callers |
|---|---|---|---|
| `project(kind, records)` | `src/perfrepair/ai/runtime/engine/kind.py` | - | ai.runtime.engine.decide, device.used, grouping.report.checks |
| `active_outbox(root)` | `src/perfrepair/ai/runtime/engine/outbox.py` | The run's outbox, for every reader; NoOutbox when nothing was ever committed. | ai.select.replay, check.grouping, device.coverage, device.used +2 |
| `add_agent_args(parser, role)` | `src/perfrepair/ai/runtime/gateway/args.py` | Unset flags resolve per role in `spawn` (docs/settings.md). | ai.__main__, grouping.__main__, guide.command |
| `spawn(args, settings, dry_run)` | `src/perfrepair/ai/runtime/gateway/spawn.py` | dry_run: the role's stand-in answers, for the gateway that answers without a model. | ai.__main__, grouping.__main__, guide.command |
| `add_prompt_args(parser)` | `src/perfrepair/ai/runtime/prompt/args.py` | - | ai.__main__, grouping.__main__, guide.command |
| `load_prompts(parser, args, settings)` | `src/perfrepair/ai/runtime/prompt/args.py` | - | ai.__main__, grouping.__main__, guide.command |
| `args_schema(properties, required)` | `src/perfrepair/ai/tools/tool.py` | `{'type': 'object', 'properties': properties, 'required': list(required), 'additionalProperties': False}` | ai.review.job, ai.select.job, ai.tools.catalogue_read |
| `app_id(device, path)` | `src/perfrepair/app/facts/path_id.py` | The folder for --app: its own id, else the unit of a multi-root folder that recorded this path as its root. | ai.__main__, repair.__main__, report.__main__ |
| `path_id(path)` | `src/perfrepair/app/facts/path_id.py` | - | app.__main__, guide.state, guide.target_file |
| `algorithm_id(engine_type, canonical)` | `../../lib/cryptobench/cryptobench/catalogue/algorithms.py` | `f'{engine_type}{SEPARATOR}{canonical}'` | catalog.groups, catalog.views, probe.identified, validation.catalogue_entry |
| `algorithms()` | `../../lib/cryptobench/cryptobench/catalogue/algorithms.py` | `load()` | catalog.groups, catalog.types, catalog.views |
| `group_catalog()` | `../../lib/cryptobench/cryptobench/catalogue/groups.py` | `load(CATALOG)` | ai.parse.grouping_assign.render, catalog.identity, catalog.views, grouping.report.candidates +6 |
| `interchange()` | `../../lib/cryptobench/cryptobench/catalogue/interchange.py` | `load()` | ai.parse.grouping_assign.render, catalog.groups, catalog.signature |
| `fold(name)` | `../../lib/cryptobench/cryptobench/catalogue/names.py` | `name.upper()` | catalog.algorithms, catalog.deviations, catalog.groups, catalog.screening +11 |
| `function_parameters(resolved)` | `src/perfrepair/catalog/resolved.py` | Each value by its canonical digest name: providers report one digest under different spellings. | catalog.signature, grouping.report.rules, probe.identified |
| `types()` | `src/perfrepair/catalog/types.py` | `of_catalogues(algorithms())` | catalog.upgrades, repair.dossier, validation.boundary |
| `add_config_arg(parser)` | `src/perfrepair/config/args.py` | - | ai.runtime.gateway.args, app.__main__, data_handler.inbound.__main__, grouping.__main__ +3 |
| `load_settings(parser, args)` | `src/perfrepair/config/args.py` | - | ai.__main__, app.__main__, config.device_results, data_handler.inbound.__main__ +4 |
| `perf_mode(text)` | `src/perfrepair/config/args.py` | The argparse type of --perf-mode: `generic` or `all`, or keys joined by `,` (energy,latency,throughput). | guide.command, repair.__main__, report.__main__ |
| `positive_int(text)` | `src/perfrepair/config/args.py` | The argparse type of --turns, --sessions, --limit: the check their perfrepair.yaml keys get. | ai.__main__, grouping.__main__, guide.command |
| `add_device_results_arg(parser)` | `src/perfrepair/config/device_results.py` | - | ai.__main__, app.__main__, data_handler.inbound.__main__, grouping.__main__ +5 |
| `fill_device_results(parser, args, loaded)` | `src/perfrepair/config/device_results.py` | - | ai.__main__, app.__main__, data_handler.inbound.__main__, grouping.__main__ +4 |
| `manifest_file(manifest, base, key)` | `src/perfrepair/data_handler/inbound/manifest.py` | - | data_handler.inbound.run_context, device.delta, device.inbound, device.interop +4 |
| `read_manifest(path)` | `src/perfrepair/data_handler/inbound/manifest.py` | - | check.device, data_handler.inbound.run_context, device.delta, device.inbound +10 |
| `run_pipeline(config, results, stage, benchmark, harness, echo, tail, extra, app, device, env)` | `src/perfrepair/data_handler/outbound/benchmark_runner.py` | results: the root, unused with harness, where pipeline.py picks checked/ itself; device: the folder whose log/ | device.delta, device.interop, device.stage_run, guide.app_steps |
| `write_inbound(device)` | `src/perfrepair/device/inbound.py` | The lines to print: a count, then each comparability warning. | data_handler.inbound.__main__, device.gate_after, device.stage_run |
| `measured_rows(device, app)` | `src/perfrepair/device/missing_rows.py` | A site's item the run log says was never measured: skipped, not runnable, or planned with no samples. | guide.app_steps, guide.device_steps, guide.targets |
| `inputs(device)` | `src/perfrepair/device/primitives.py` | The digests the table is made from; items.json is bound into screen.json's own `built`. | device.gate_after, device.seen, device.stage |
| `write_used(device, apps)` | `src/perfrepair/device/used.py` | - | device.stage, device.stage_pass, guide.device_steps, guide.gate_steps |
| `admits(max_change, change)` | `src/perfrepair/dto/change.py` | `change in CHANGES and CHANGES.index(change) <= CHANGES.index(max_change)` | ai.select.unit_candidates, result.candidates, validation.dossiers.document, validation.dossiers.dossier +1 |
| `output_changes(diff)` | `src/perfrepair/dto/change.py` | `diff is not None and diff.output != SAME` | result.change, result.options, validation.dossiers.dossier |
| `parse_yaml(text, where, code, shape, error)` | `../../lib/cryptobench/cryptobench/catalogue/document.py` | An empty text is an empty shape; YAML that does not parse, or parses to another shape, is `<code>: <where>: ...`. | catalog.bundled_providers, catalog.screening, files |
| `reason_code(reason)` | `src/perfrepair/dto/dossier.py` | A noOptions reason's code; `no_evidence` names its metrics after a colon, `person_judges` its reject reasons. | ai.select.upgrades, repair.dossier, result.configurations, validation.dossiers.document |
| `algorithm_of(item)` | `../../lib/cryptobench/cryptobench/catalogue/grouping.py` | `parse_qualified(item)[1]` | ai.select.options, ai.select.render, ai.select.upgrade_render, result.upgrades +1 |
| `parse_qualified(text)` | `../../lib/cryptobench/cryptobench/catalogue/grouping.py` | - | ai.select.rows, device.delta_config, device.delta_estimate, device.measured_check +5 |
| `provider_of(item)` | `../../lib/cryptobench/cryptobench/catalogue/grouping.py` | `parse_qualified(item)[2]` | ai.select.options, ai.select.render, ai.select.upgrade_render, catalog.names +6 |
| `qualified(engine_type, name, provider)` | `../../lib/cryptobench/cryptobench/catalogue/grouping.py` | `SEPARATOR.join((engine_type, name, provider))` | catalog.identity, device.measured_check, device.missing_rows, device.selection_adds +8 |
| `read_items(doc)` | `../../lib/cryptobench/cryptobench/catalogue/grouping.py` | - | ai.parse.grouping_assign.kind, check.device, check.grouping, device.gate +7 |
| `read_profiles(doc)` | `../../lib/cryptobench/cryptobench/catalogue/grouping.py` | - | ai.parse.grouping_assign.kind, grouping.interop_plan, review.sheet, validation.grouping.output |
| `code_made(group)` | `src/perfrepair/dto/grouping_state.py` | `group.startswith(CODE_PREFIX)` | ai.parse.grouping_assign.command, grouping.report.rules, validation.grouping.code_groups, validation.grouping.knowledge |
| `pair_status(groups, a, b)` | `src/perfrepair/dto/interop.py` | - | result.options, result.unit_dossiers, validation.dossiers.against_run |
| `required_risks(scope, option)` | `src/perfrepair/dto/replacement.py` | Each risk the scope facts, and the chosen option's when given, imply, with the plain words that imply it. | ai.select.options, ai.select.render, ai.select.unit_candidates, result.upgrades +1 |
| `shipped(app_doc)` | `src/perfrepair/dto/shipped.py` | `tuple((Shipped(b['artifact'], b.get('providerName'), b.get('version')) for b in app_doc.get('bundled') or []))` | device.bundled_missing, device.missing_rows, result.dossier, result.provider_path |
| `shipped_names(app_doc)` | `src/perfrepair/dto/shipped.py` | `{s.providerName for s in shipped(app_doc) if s.providerName}` | app.__main__, device.missing_rows, repair.dossier, result.dossier |
| `read_units(doc)` | `src/perfrepair/dto/unit.py` | - | check.apps, repair.__main__, repair.dossier, report.app_report |
| `units_by_scope(units)` | `src/perfrepair/dto/unit.py` | `{member: u for u in units for member in u.members}` | repair.edit.app, repair.harness, report.app_report, result.unit_dossiers |
| `newest(versions)` | `src/perfrepair/dto/version.py` | - | app.facts.versions, device.bundled_suggest, dto.bundled |
| `reported(step)` | `src/perfrepair/failure.py` | step's exit code when it returns one, else 0; a FAILURES exception is `error <it>` on stderr and its code's exit. | ai.__main__, app.__main__, data_handler.inbound.__main__, grouping.__main__ +6 |
| `json_text(doc)` | `src/perfrepair/files.py` | `json.dumps(doc, indent=1)` | ai.runtime.engine.kind, ai.select.replay, ai.select.units, ai.select.upgrades +2 |
| `read_json(path)` | `src/perfrepair/files.py` | `json.loads(read_text(path))` | ai.parse.algorithm_classify.command, ai.parse.grouping_assign.kind, ai.runtime.engine.charter_file, ai.runtime.engine.outbox +30 |
| `read_yaml(path, shape)` | `src/perfrepair/files.py` | `parse_yaml(read_text(path), str(path), shape=shape)` | ai.runtime.prompt.library, app.facts.dependencies, app.facts.target_set, app.find.sources +31 |
| `sha256_file(path)` | `src/perfrepair/files.py` | The digest of the file's bytes as written; None when it is absent. | device.gate_after, device.primitives, device.seen, device.stage +5 |
| `sha256_text(text)` | `src/perfrepair/files.py` | `hashlib.sha256(text.encode()).hexdigest()` | ai.parse.grouping_assign.command, ai.select.units, ai.select.upgrades, app.facts.path_id +1 |
| `write_json(path, doc, durable, exclusive)` | `src/perfrepair/files.py` | `write_text(path, json_text(doc), durable, exclusive)` | ai.parse.algorithm_classify.command, ai.runtime.engine.charter_file, ai.runtime.engine.decide, ai.runtime.engine.outbox +11 |
| `write_text(path, text, durable, exclusive)` | `src/perfrepair/files.py` | - | ai.parse.algorithm_classify.command, ai.runtime.engine.outbox, device.bundled, device.interop +11 |
| `write_text_making_parents(path, text)` | `src/perfrepair/files.py` | - | ai.log.attempt_log, device.benchmark_coverage, device.delta, device.delta_config +5 |
| `attach(device_results)` | `src/perfrepair/log/attach.py` | At a command's start with no folder: handlers, a new run; again once the folder is known: events.jsonl. | ai.__main__, app.__main__, data_handler.inbound.__main__, grouping.__main__ +6 |
| `run_id()` | `src/perfrepair/log/attach.py` | The attached run's id; a call outside any command run gets one of its own. | ai.log.attempt_log, data_handler.outbound.benchmark_runner, device.benchmark_coverage, device.gate +2 |
| `elapsed_ms(started)` | `src/perfrepair/log/emit.py` | `int((time.monotonic() - started) * 1000)` | ai.job, ai.runtime.engine.decide, guide.run, log.attach |
| `emit(stage, step, event, kind, item, app, outcome, durationMs, tokens, costUsd, ref, detail, data, level)` | `src/perfrepair/log/emit.py` | - | ai.job, ai.log.attempt_log, ai.runtime.engine.decide, device.bundled +12 |
| `step(stage, name, kind, item, app, detail, data)` | `src/perfrepair/log/emit.py` | - | app.__main__, device.bundled, device.gate, device.inbound +9 |
| `status_line(e)` | `src/perfrepair/log/status.py` | - | log.progress, log.summary, log.views |
| `string_literal(value, language)` | `src/perfrepair/repair/edit/literal.py` | - | repair.edit.algorithm, repair.edit.provider, repair.edit.specs |
| `apply(text, splices)` | `src/perfrepair/repair/edit/splice.py` | Newlines inside a replaced span follow the new text, so a scope's lines `start..end` stay put in the copy. | repair.edit.alone, repair.edit.app, repair.edit.plan |
| `reach(scope)` | `src/perfrepair/result/change.py` | A field keeps the object past the function, so where its output goes is not read: unknown, never local. | ai.select.upgrade_render, result.options, result.upgrades |
| `operations(scope)` | `src/perfrepair/result/configurations.py` | The operations the lifecycle performs; empty, meaning every one, when it does not know. | ai.select.rows, result.options, result.upgrades |
| `by_change(estimates, change)` | `src/perfrepair/result/gain.py` | The metrics with an estimate of this change, in estimate order, each once. | ai.select.options, ai.select.unit_candidates, ai.select.units |
| `option_label(estimates)` | `src/perfrepair/result/gain.py` | `label_of([change_of(e.ratio, e.pImprove) for e in estimates])` | ai.select.options, ai.select.upgrade_render, review.sheet |
| `app_dirs(device)` | `src/perfrepair/run_dir/layout.py` | Device-level folders sit beside the apps, so an app's folder is the one holding app.json. | app.facts.path_id, check.apps, check.run, guide.device_steps +4 |
| `device_folders(root)` | `src/perfrepair/run_dir/layout.py` | The finished devices of a results root: a folder without a manifest is a run that did not end. | config.device_results |
| `load_measurements(device)` | `src/perfrepair/run_dir/read.py` | `Measurements.from_json(read_json(Path(device) / MEASUREMENTS))` | ai.select.units, check.device, device.delta, device.measured_check +3 |
| `load_rows(device)` | `src/perfrepair/run_dir/read.py` | `[PrimitiveRow.from_json(r) for r in read_versioned(ROWS_DOC, Path(device) / ROWS)['rows']]` | check.run, device.measured_check, device.primitives, device.seen +1 |
| `load_screen(paths)` | `src/perfrepair/run_dir/read.py` | `read_screen(read_json(paths.screen)) if paths.screen.exists() else None` | check.grouping, check.run, device.primitives, device.stage_pass +2 |
| `load_screen_catalog(paths)` | `src/perfrepair/run_dir/read.py` | `read_screen_catalog(read_json(paths.screen)) if paths.screen.exists() else None` | check.grouping, guide.device_steps, repair.dossier |
| `load_upgrades(path)` | `src/perfrepair/run_dir/read.py` | What each broken use became; none before the upgrade step ran. | guide.app_steps, repair.__main__, report.app_report |
| `load_used(device)` | `src/perfrepair/run_dir/read.py` | None without used.json: every item counts as used. | ai.parse.grouping_assign.kind, check.device, guide.device_steps, guide.gate_steps |
| `read_dossiers(path)` | `src/perfrepair/run_dir/read.py` | `read_versioned(DOSSIERS_DOC, path)` | ai.select.units, ai.select.upgrades, guide.app_steps, repair.__main__ |
| `read_edits(path)` | `src/perfrepair/run_dir/read.py` | `read_versioned(EDITS_DOC, path)` | check.apps, guide.app_steps, repair.__main__ |
| `read_scopes(path)` | `src/perfrepair/run_dir/read.py` | `read_versioned(SCOPES_DOC, path)` | check.apps, device.missing_rows, guide.app_steps, repair.__main__ +2 |
| `read_sites(path)` | `src/perfrepair/run_dir/read.py` | `read_versioned(SITES_DOC, path)` | device.bundled_missing, device.missing_rows, device.used, report.app_report |
| `read_engines(path)` | `src/perfrepair/scope/engines.py` | - | scope.build, scope.units.shapes, validation.scoping.invariants |
| `origin(e, engines, depth)` | `src/perfrepair/scope/lifecycle/origins.py` | - | scope.lifecycle.depth1, scope.lifecycle.read, scope.lifecycle.settle |
| `as_call(n)` | `src/perfrepair/scope/syntax/calls.py` | - | scope.lifecycle.depth1, scope.lifecycle.origins, scope.lifecycle.settle, scope.lifecycle.slice +1 |
| `declaration_value(declaration)` | `src/perfrepair/scope/syntax/declarations.py` | What a declarator or property declaration initialises to; None when it has no initialiser. | scope.lifecycle.depth1, scope.lifecycle.origins, scope.lifecycle.settle |
| `declared_names(n)` | `src/perfrepair/scope/syntax/declarations.py` | The locals a statement declares, each with its declaring node. | scope.lifecycle.slice, scope.syntax.resolve, scope.syntax.usage |
| `enclosing_method(n)` | `src/perfrepair/scope/syntax/declarations.py` | - | scope.lifecycle.depth1, scope.lifecycle.read, scope.lifecycle.settle, scope.units.shapes |
| `method_body(method)` | `src/perfrepair/scope/syntax/declarations.py` | - | scope.lifecycle.depth1, scope.lifecycle.read, scope.lifecycle.settle |
| `methods_named(body, name, arity)` | `src/perfrepair/scope/syntax/declarations.py` | - | scope.lifecycle.depth1, scope.lifecycle.origins, scope.lifecycle.settle |
| `outermost_class(n)` | `src/perfrepair/scope/syntax/declarations.py` | The outermost class body; the file when the code has no class around it. | scope.lifecycle.depth1, scope.lifecycle.origins, scope.lifecycle.settle, scope.units.shapes |
| `parameters(method)` | `src/perfrepair/scope/syntax/declarations.py` | - | scope.lifecycle.depth1, scope.lifecycle.origins, scope.lifecycle.slice, scope.syntax.resolve +1 |
| `resolve_field(name, at)` | `src/perfrepair/scope/syntax/resolve.py` | - | scope.lifecycle.depth1, scope.lifecycle.origins, scope.lifecycle.read, scope.lifecycle.settle |
| `resolve_local(name, at)` | `src/perfrepair/scope/syntax/resolve.py` | The nearest local or parameter visible at `at`; stops at the class boundary. | scope.lifecycle.binding, scope.lifecycle.depth1, scope.lifecycle.origins, scope.lifecycle.read |
| `unwrapped(n)` | `src/perfrepair/scope/syntax/usage.py` | - | scope.lifecycle.origins, scope.lifecycle.output, scope.lifecycle.settle |
| `use_of(n)` | `src/perfrepair/scope/syntax/usage.py` | Follows the value out through parentheses, casts and branches to what finally receives it. | scope.lifecycle.binding, scope.lifecycle.output, scope.lifecycle.slice |
| `screening_catalog(loaded)` | `src/perfrepair/screen/catalog.py` | None stands for no perfrepair.yaml; a set catalog that does not load is missing_file, never the packaged one. | grouping.__main__, guide.device_steps, repair.__main__, validation.__main__ |
| `matching(masked, i)` | `src/perfrepair/source/brackets.py` | Offset of the bracket closing the one at i, in masked text. | app.facts.kind, app.facts.sdk, app.find.constants, repair.edit.init +3 |
| `of_build_file(name)` | `src/perfrepair/source/language.py` | Groovy and properties build files are lexed by Java's comment and string rules. | app.facts.dependencies, app.facts.kind, app.facts.sdk |
| `of_file(name)` | `src/perfrepair/source/language.py` | - | app.find.sources, repair.edit.plan, scope.build, scope.units.shapes +1 |
| `mask(text, language, strings)` | `src/perfrepair/source/lexer.py` | Comments always, and string contents when `strings`, become spaces; newlines and quotes stay. | app.facts.dependencies, app.facts.kind, app.facts.sdk, repair.dependencies +2 |
| `halt_of(code, detail)` | `src/perfrepair/stop/terminate.py` | A fixed stop terminated and its Halt handed back, for a caller that records it instead of raising it. | guide.run, guide.target_file, guide.targets |
| `terminate(code, detail, stage, step, item, app, ref, data, inner, trace, next_step)` | `src/perfrepair/stop/terminate.py` | Returns warn or skip; trace: lines the Halt's message carries and the status line leaves out; next_step: what this | app.__main__, data_handler.outbound.benchmark_runner, device.bundled, device.energy +6 |
| `perf_of(doc)` | `src/perfrepair/validation/dossiers/document.py` | - | ai.select.units, ai.select.upgrades, validation.dossiers.against_run, validation.dossiers.parse |
| `require(what, problems)` | `src/perfrepair/validation/failure.py` | - | ai.job, ai.runtime.engine.decide, ai.select.job, ai.select.units +14 |
| `read_groups(paths)` | `src/perfrepair/validation/grouping/output.py` | - | check.run, grouping.interop_plan, repair.dossier |
| `validate_manifest(manifest, base)` | `src/perfrepair/validation/manifest.py` | - | app.__main__, check.device, device.inbound |
| `validate_measurements(m, rows)` | `src/perfrepair/validation/measurements.py` | - | check.device, device.inbound, device.primitives, repair.dossier |
