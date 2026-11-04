# Shared functions: perf-repair

| function | module | rule | callers |
|---|---|---|---|
| `ask(conversations, charter, message, check, limits, on_turn)` | `src/perfrepair/ai/runtime/engine/ask.py` | - | ai.review.grouping_review.run, ai.runtime.engine.decide, review.stability |
| `decide(kind, charter, conversations, root, limits, limit, echo, where)` | `src/perfrepair/ai/runtime/engine/decide.py` | - | ai.evaluate.worthiness.command, ai.parse.algorithm_classify.command, ai.parse.grouping_assign.command, ai.suggest.site_replace.command |
| `project(kind, records)` | `src/perfrepair/ai/runtime/engine/kind.py` | - | ai.runtime.engine.decide, ai.suggest.site_replace.command, device.used, grouping.report.checks |
| `replay_problems(kind, state, records)` | `src/perfrepair/ai/runtime/engine/kind.py` | The state is one version per committed record and equals the projection of the outbox. | ai.evaluate.worthiness.kind, ai.parse.algorithm_classify.kind, ai.parse.grouping_assign.kind, ai.suggest.site_replace.kind |
| `active_outbox(root)` | `src/perfrepair/ai/runtime/engine/outbox.py` | The run's outbox, for every reader; NoOutbox when nothing was ever committed. | ai.parse.grouping_assign.kind, ai.parse.grouping_assign.rekey, ai.runtime.engine.refresh, ai.suggest.site_replace.command +5 |
| `add_agent_args(parser, role)` | `src/perfrepair/ai/runtime/gateway/args.py` | Unset flags resolve per role in `spawn` (docs/settings.md). | ai.__main__, grouping.__main__, guide.command, review.__main__ |
| `spawn(args, settings, dry_run)` | `src/perfrepair/ai/runtime/gateway/spawn.py` | dry_run: the role's stand-in answers, for the gateway that answers without a model. | ai.__main__, grouping.__main__, guide.command, review.__main__ |
| `add_prompt_args(parser)` | `src/perfrepair/ai/runtime/prompt/args.py` | - | ai.__main__, grouping.__main__, guide.command, review.__main__ |
| `load_prompts(parser, args, settings)` | `src/perfrepair/ai/runtime/prompt/args.py` | - | ai.__main__, grouping.__main__, guide.command, review.__main__ |
| `charter(library, inputs)` | `src/perfrepair/ai/suggest/site_replace/kind.py` | `library.charter(NAME, SCHEMA, inputs)` | ai.suggest.site_replace.command, guide.finished, review.stability |
| `app_id(device, path)` | `src/perfrepair/app/facts/path_id.py` | The folder for --app: its own id, else the unit of a multi-root folder that recorded this path as its root. | ai.__main__, repair.__main__, report.__main__ |
| `path_id(path)` | `src/perfrepair/app/facts/path_id.py` | - | app.__main__, guide.state, guide.target_file |
| `fold(name)` | `src/perfrepair/catalog/names.py` | `name.upper()` | catalog.screening, catalog.types, data_handler.inbound.probe._index, data_handler.inbound.probe._names +4 |
| `add_config_arg(parser)` | `src/perfrepair/config/args.py` | - | ai.runtime.gateway.args, app.__main__, data_handler.inbound.__main__, grouping.__main__ +3 |
| `load_settings(parser, args)` | `src/perfrepair/config/args.py` | - | ai.__main__, app.__main__, config.device_results, data_handler.inbound.__main__ +5 |
| `perf_mode(text)` | `src/perfrepair/config/args.py` | The argparse type of --perf-mode: `generic` or `all`, or keys joined by `,` (energy,latency,throughput). | ai.__main__, guide.command, repair.__main__, report.__main__ |
| `positive_int(text)` | `src/perfrepair/config/args.py` | The argparse type of --turns, --sessions, --limit: the check their perfrepair.yaml keys get. | ai.__main__, grouping.__main__, guide.command, review.__main__ |
| `add_device_results_arg(parser)` | `src/perfrepair/config/device_results.py` | - | ai.__main__, app.__main__, data_handler.inbound.__main__, grouping.__main__ +5 |
| `fill_device_results(parser, args, loaded)` | `src/perfrepair/config/device_results.py` | - | ai.__main__, app.__main__, data_handler.inbound.__main__, grouping.__main__ +4 |
| `display_units(device)` | `src/perfrepair/data_handler/inbound/manifest.py` | The units every view of this device folder shows; a folder without a manifest (a test, a hand-made one) the defaults. | ai.evaluate.worthiness.command, ai.suggest.site_replace.command, report.command |
| `manifest_file(manifest, base, key)` | `src/perfrepair/data_handler/inbound/manifest.py` | - | data_handler.inbound.run_context, device.delta, device.inbound, device.measured_check +3 |
| `read_manifest(path)` | `src/perfrepair/data_handler/inbound/manifest.py` | - | data_handler.inbound.run_context, device.delta, device.inbound, device.measured_check +7 |
| `identify(config, on_device, benchmark)` | `src/perfrepair/data_handler/outbound/benchmark_runner.py` | pipeline.py --identify: deviceId, mode, config and input digests, before any probe; nothing is written. | device.delta, device.stage, guide.finished |
| `run_pipeline(config, results, stage, benchmark, harness, echo, tail, extra, app, device, env)` | `src/perfrepair/data_handler/outbound/benchmark_runner.py` | results: the root, unused with harness, where pipeline.py picks measured/ itself; device: the folder whose log/ | device.delta, device.stage_run, guide.app_steps |
| `write_inbound(device)` | `src/perfrepair/device/inbound.py` | The lines to print: a count, then each comparability warning. | data_handler.inbound.__main__, device.gate_after, device.stage_run |
| `measured_rows(device, app)` | `src/perfrepair/device/missing_rows.py` | A site's item the run log says was never measured: skipped, not runnable, or planned with no samples. | guide.app_steps, guide.device_steps, guide.targets |
| `inputs(device)` | `src/perfrepair/device/primitives.py` | The digests the table is made from; items.json is bound into screen.json's own `built`. | device.gate_after, device.seen, device.stage |
| `write_used(device, apps)` | `src/perfrepair/device/used.py` | - | device.stage, device.stage_pass, guide.device_steps, guide.gate_steps |
| `admits(max_change, change)` | `src/perfrepair/dto/change.py` | `change in CHANGES and CHANGES.index(change) <= CHANGES.index(max_change)` | result.candidates, validation.dossiers.document, validation.dossiers.dossier, validation.report +1 |
| `output_changes(diff)` | `src/perfrepair/dto/change.py` | `diff is not None and diff.output != SAME` | result.change, result.options, validation.dossiers.dossier |
| `reason_code(reason)` | `src/perfrepair/dto/dossier.py` | A noOptions reason's code; `no_evidence` names its metrics after a colon. | repair.dossier, result.configurations, validation.dossiers.document |
| `algorithm_of(item)` | `src/perfrepair/dto/grouping.py` | `parse_qualified(item)[1]` | ai.suggest.site_replace.options, ai.suggest.site_replace.render, validation.suggest.site_edits |
| `parse_qualified(text)` | `src/perfrepair/dto/grouping.py` | - | ai.review.grouping_review.render, ai.suggest.site_replace.rows, device.delta_config, device.delta_estimate +8 |
| `provider_of(item)` | `src/perfrepair/dto/grouping.py` | `parse_qualified(item)[2]` | ai.suggest.site_replace.options, ai.suggest.site_replace.render, result.candidates, result.dossier +3 |
| `qualified(engine_type, name, provider)` | `src/perfrepair/dto/grouping.py` | `SEPARATOR.join((engine_type, name, provider))` | device.measured_check, device.missing_rows, device.selection_adds, device.used +7 |
| `read_items(doc)` | `src/perfrepair/dto/grouping.py` | - | ai.parse.grouping_assign.kind, check.device, check.grouping, device.gate +7 |
| `read_profiles(doc)` | `src/perfrepair/dto/grouping.py` | - | ai.parse.grouping_assign.kind, review.sheet, validation.grouping.output |
| `code_made(group)` | `src/perfrepair/dto/grouping_state.py` | `group.startswith(CODE_PREFIX)` | ai.parse.grouping_assign.command, ai.review.grouping_review.run, grouping.report.rules, validation.grouping.code_groups +1 |
| `pair_status(groups, a, b)` | `src/perfrepair/dto/interop.py` | - | result.evidence, result.options, result.unit_dossiers, validation.dossiers.against_run |
| `required_risks(scope, option)` | `src/perfrepair/dto/replacement.py` | Each risk the scope facts, and the chosen option's when given, imply, with the plain words that imply it. | ai.suggest.site_replace.options, ai.suggest.site_replace.render, validation.replacements, validation.suggest.site_replace |
| `has_views(metric)` | `src/perfrepair/dto/report.py` | A metric throughput selects is time: its row carries latency and throughput in the display units. | ai.evaluate.worthiness.render, ai.suggest.site_replace.rows, report.metrics, validation.report_metrics |
| `lowers_status(current, target)` | `src/perfrepair/dto/screen.py` | A never-target status is allowed only as the current item's own algorithm, never at a worse status. | result.evidence, result.options, validation.dossiers.against_run |
| `qualified_verdicts(groups, screen)` | `src/perfrepair/dto/screen.py` | screen.json's verdicts keyed by groups.json's qualified names; None without screen.json. | ai.evaluate.worthiness.command, check.grouping, screen.handler |
| `shipped(app_doc)` | `src/perfrepair/dto/shipped.py` | `tuple((Shipped(b['artifact'], b.get('providerName'), b.get('version')) for b in app_doc.get('bundled') or []))` | device.bundled_missing, device.missing_rows, result.dossier, result.provider_path |
| `shipped_names(app_doc)` | `src/perfrepair/dto/shipped.py` | `{s.providerName for s in shipped(app_doc) if s.providerName}` | app.__main__, device.missing_rows, repair.dossier, result.dossier |
| `read_units(doc)` | `src/perfrepair/dto/unit.py` | - | check.apps, repair.__main__, repair.dossier, report.app_report |
| `units_by_scope(units)` | `src/perfrepair/dto/unit.py` | `{member: u for u in units for member in u.members}` | repair.edit.app, repair.harness, report.app_report |
| `number(x)` | `src/perfrepair/dto/units.py` | Significant figures, so a sub-unit value never rounds to 0 (64 B AES-CBC is 0.000662 ms). | ai.evaluate.worthiness.render, ai.suggest.site_replace.rows, report.markdown |
| `newest(versions)` | `src/perfrepair/dto/version.py` | - | app.facts.versions, device.bundled_suggest, dto.bundled |
| `reported(step)` | `src/perfrepair/failure.py` | step's exit code when it returns one, else 0; a FAILURES exception is `error <it>` on stderr and its code's exit. | ai.__main__, app.__main__, data_handler.inbound.__main__, grouping.__main__ +6 |
| `json_text(doc)` | `src/perfrepair/files.py` | `json.dumps(doc, indent=1)` | ai.suggest.site_replace.kind, device.coverage, device.delta_merge |
| `read_json(path)` | `src/perfrepair/files.py` | `json.loads(read_text(path))` | ai.parse.grouping_assign.kind, ai.review.grouping_review.run, ai.runtime.engine.charter_file, ai.runtime.engine.outbox +28 |
| `read_jsonl(path)` | `src/perfrepair/files.py` | - | ai.runtime.engine.journal, log.read, validation.events |
| `read_yaml(path)` | `src/perfrepair/files.py` | `yaml.safe_load(Path(path).read_text()) or {}` | ai.runtime.prompt.library, app.facts.dependencies, app.facts.target_set, app.find.sources +29 |
| `sha256_file(path)` | `src/perfrepair/files.py` | The digest of the file's bytes as written; None when it is absent. | device.gate_after, device.primitives, device.seen, device.stage +4 |
| `sha256_text(text)` | `src/perfrepair/files.py` | `hashlib.sha256(text.encode()).hexdigest()` | ai.parse.grouping_assign.command, ai.suggest.site_replace.kind, app.facts.path_id, guide.finished |
| `write_json(path, doc, durable, exclusive)` | `src/perfrepair/files.py` | `write_text(path, json_text(doc), durable, exclusive)` | ai.evaluate.worthiness.command, ai.evaluate.worthiness.kind, ai.parse.algorithm_classify.command, ai.parse.algorithm_classify.kind +16 |
| `write_text(path, text, durable, exclusive)` | `src/perfrepair/files.py` | - | ai.parse.algorithm_classify.command, ai.runtime.engine.outbox, device.bundled, device.primitives +9 |
| `write_text_making_parents(path, text)` | `src/perfrepair/files.py` | - | device.benchmark_coverage, device.delta, device.delta_config, device.delta_merge +4 |
| `attach(device_results)` | `src/perfrepair/log/attach.py` | At a command's start with no folder: handlers, a new run; again once the folder is known: events.jsonl. | ai.__main__, app.__main__, data_handler.inbound.__main__, grouping.__main__ +6 |
| `run_id()` | `src/perfrepair/log/attach.py` | The attached run's id; a call outside any command run gets one of its own. | data_handler.outbound.benchmark_runner, device.benchmark_coverage, device.gate, device.primitives_missing |
| `elapsed_ms(started)` | `src/perfrepair/log/emit.py` | `int((time.monotonic() - started) * 1000)` | ai.runtime.engine.decide, guide.run, log.attach |
| `emit(stage, step, event, kind, item, app, outcome, durationMs, tokens, costUsd, ref, detail, data, level)` | `src/perfrepair/log/emit.py` | - | ai.evaluate.worthiness.command, ai.runtime.engine.decide, ai.runtime.engine.events, ai.suggest.site_replace.command +12 |
| `step(stage, name, kind, item, app, detail, data)` | `src/perfrepair/log/emit.py` | - | ai.parse.grouping_assign.rekey, ai.review.grouping_review.run, app.__main__, device.bundled +11 |
| `status_line(e)` | `src/perfrepair/log/status.py` | - | log.progress, log.summary, log.views |
| `string_literal(value, language)` | `src/perfrepair/repair/edit/literal.py` | - | repair.edit.algorithm, repair.edit.provider, repair.edit.specs |
| `apply(text, splices)` | `src/perfrepair/repair/edit/splice.py` | Newlines inside a replaced span follow the new text, so a scope's lines `start..end` stay put in the copy. | repair.edit.alone, repair.edit.app, repair.edit.plan |
| `level(p_improve)` | `src/perfrepair/result/confidence.py` | - | report.metrics, result.evidence, validation.report_metrics |
| `operations(scope)` | `src/perfrepair/result/configurations.py` | The operations the lifecycle performs; empty, meaning every one, when it does not know. | ai.suggest.site_replace.rows, repair.call_site, result.options |
| `parse_label(text)` | `src/perfrepair/result/configurations.py` | label()'s fields back from a stored configuration; `estimated` when the side's energy is estimated. | ai.suggest.site_replace.options, repair.call_site, result.category |
| `compare(before, after, lower_is_better)` | `src/perfrepair/result/estimate.py` | `after` against `before`, oriented so a ratio below 1 and a high pImprove are better: after ÷ before of the | device.delta, report.metrics, result.configurations, result.evidence |
| `change_of(ratio, pImprove)` | `src/perfrepair/result/gain.py` | - | device.delta, report.metrics, report.swaps, result.category +1 |
| `criteria()` | `src/perfrepair/result/modes.py` | `read_yaml(CRITERIA)` | report.summary, report.thermal, result.confidence, result.gain |
| `mode_of(perf)` | `src/perfrepair/result/modes.py` | `Mode(perf, criteria()['rule'], float(criteria()['improvingRatio']))` | ai.__main__, check.grouping, guide.command, report.__main__ |
| `app_dirs(device)` | `src/perfrepair/run_dir/layout.py` | Device-level folders sit beside the apps, so an app's folder is the one holding app.json. | app.facts.path_id, check.run, guide.device_steps, guide.index +4 |
| `device_folders(root)` | `src/perfrepair/run_dir/layout.py` | The finished devices of a results root: a folder without a manifest is a run that did not end. | config.device_results |
| `worthiness(device, mode)` | `src/perfrepair/run_dir/layout.py` | `Path(device) / f'{WORTHINESS_PREFIX}{mode}'` | ai.evaluate.worthiness.command, check.grouping, check.run, review.sheet |
| `load_measurements(device)` | `src/perfrepair/run_dir/read.py` | `Measurements.from_json(read_json(Path(device) / MEASUREMENTS))` | ai.evaluate.worthiness.command, ai.suggest.site_replace.command, check.device, check.grouping +5 |
| `load_rows(device)` | `src/perfrepair/run_dir/read.py` | `[PrimitiveRow.from_json(r) for r in read_versioned(ROWS_DOC, Path(device) / ROWS)['rows']]` | ai.evaluate.worthiness.command, check.run, device.measured_check, device.primitives +2 |
| `load_screen(paths)` | `src/perfrepair/run_dir/read.py` | `read_screen(read_json(paths.screen)) if paths.screen.exists() else None` | ai.evaluate.worthiness.command, check.grouping, check.run, device.primitives +2 |
| `load_screen_catalog(paths)` | `src/perfrepair/run_dir/read.py` | `read_screen_catalog(read_json(paths.screen)) if paths.screen.exists() else None` | check.grouping, guide.device_steps, repair.dossier |
| `load_used(device)` | `src/perfrepair/run_dir/read.py` | None without used.json: every item counts as used. | ai.parse.grouping_assign.kind, check.device, guide.device_steps, guide.gate_steps |
| `read_dossiers(path)` | `src/perfrepair/run_dir/read.py` | `read_versioned(DOSSIERS_DOC, path)` | ai.suggest.site_replace.command, guide.app_steps, repair.__main__, review.stability |
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
| `screening_catalog(loaded)` | `src/perfrepair/screen/catalog.py` | None stands for no perfrepair.yaml; a set catalog that does not load is missing_file, never the packaged one. | grouping.__main__, guide.device_steps, repair.__main__, validation.__main__ |
| `matching(masked, i)` | `src/perfrepair/source/brackets.py` | Offset of the bracket closing the one at i, in masked text. | app.facts.kind, app.facts.sdk, app.find.constants, repair.edit.init +3 |
| `of_build_file(name)` | `src/perfrepair/source/language.py` | Groovy and properties build files are lexed by Java's comment and string rules. | app.facts.dependencies, app.facts.kind, app.facts.sdk |
| `of_file(name)` | `src/perfrepair/source/language.py` | - | app.find.sources, repair.edit.plan, scope.build, scope.units.shapes +1 |
| `mask(text, language, strings)` | `src/perfrepair/source/lexer.py` | Comments always, and string contents when `strings`, become spaces; newlines and quotes stay. | app.facts.dependencies, app.facts.kind, app.facts.sdk, repair.dependencies +2 |
| `halt_of(code, detail)` | `src/perfrepair/stop/terminate.py` | A fixed stop terminated and its Halt handed back, for a caller that records it instead of raising it. | guide.run, guide.target_file, guide.targets |
| `terminate(code, detail, stage, step, item, app, ref, data, inner, trace, next_step)` | `src/perfrepair/stop/terminate.py` | Returns warn or skip; trace: lines the Halt's message carries and the status line leaves out; next_step: what this | ai.runtime.engine.journal, app.__main__, data_handler.outbound.benchmark_runner, device.bundled +7 |
| `perf_of(doc)` | `src/perfrepair/validation/dossiers/document.py` | - | ai.suggest.site_replace.kind, validation.dossiers.against_run, validation.dossiers.parse |
| `check_dossier(raw, app, perf, max_change)` | `src/perfrepair/validation/dossiers/dossier.py` | One dossier on its own: its scope, its items, its aliases R1..Rn, its pins, interop labels, estimates of | ai.suggest.site_replace.kind, validation.dossiers.against_run, validation.dossiers.parse |
| `require(what, problems)` | `src/perfrepair/validation/failure.py` | - | ai.evaluate.worthiness.command, ai.runtime.engine.decide, ai.suggest.site_replace.command, app.__main__ +13 |
| `read_groups(paths)` | `src/perfrepair/validation/grouping/output.py` | - | ai.evaluate.worthiness.command, ai.review.grouping_review.run, check.run, grouping.interop_plan +1 |
| `parse_object(text)` | `src/perfrepair/validation/json_reply.py` | - | validation.evaluate.worthiness, validation.parse.algorithm_classify, validation.parse.grouping_assign, validation.review.grouping_review +1 |
| `validate_measurements(m, rows)` | `src/perfrepair/validation/measurements.py` | - | ai.evaluate.worthiness.command, check.device, device.inbound, device.primitives +1 |
