# App

## Calls
- `docs/replacement.md` : the detect and scope steps, the Scope contract
- `docs/artifacts.md` : `<app>/sites.json`, `app.json`, `scopes.json`

## Rules
- static: detect and scope read the app tree and never edit it; no model call.
- data: crypto libraries live in `app/facts/libraries.yaml`, sink and key-source patterns in `scope/patterns.yaml`, never in code.
- detect: engine types come from the packaged names catalog, never the probe, and no site is filtered by registered names; a site the device cannot serve resolves `not_on_device` with `missing` and the next step.
- drop: a site that is not the platform class is recorded in `sites.json` `dropped` with its reason; one without an enclosing function in `scopes.json` `unscoped`.
- parser: ids, function bounds, sinks and the pattern key source come from a bracket-matching lexer over comment- and string-masked text, no grammar dependency, so ids do not depend on what is installed.
- syntax: the lifecycle reads a tree-sitter tree through `scope/syntax/` only, the pinned optional extra `perf-repair[scope]` imported lazily in `parser.py`; without it every lifecycle is `unsupported` `parser_missing`, never a pattern fallback; `tests/test_scope_syntax.py` checks no other module names the parser.
- lifecycle: per engine type, the lifecycle calls, requirements, operations and consumers live in `scope/engines.yaml`, origin calls too; code names none of them.
- lifecycle: `bounded` only when one method creates, configures and uses the object with no escape, consumer or deferred lambda; depth 1 stays in the class and is capped by `METHOD_BUDGET`; over it is `partially_bounded` `budget`.
- settlement: an open requirement whose every path closes one way inside `REACH_METHODS`, `REACH_HOPS`, `REACH_LINES`, with no outside writer, holds `settled`; past a budget it stays open, never widened; no model is asked and no cross-file analysis runs.
- units: links are read from lifecycles, never by name; inverse operations and key producers live in `scope/units/relations.yaml`; every link cites lines on both sides.
- roots: one project root keeps the given name; several are units `<name>.<root dirs joined by '.'>`, each scanned from its root.
- layers: `app/find/` reads only source text, never device data; `app/facts/` reads the app tree; `app/resolve.py` is the only module where a site meets the device's primitives (Probe, providers); `tests/test_layers.py` checks it.
- ids: a scope id is `scope_id(app, file, function, line, call)`; output is sorted, so reruns are byte-identical.

## Workflow
- run: `python3 -m perfrepair.app --device-results <device> --app <src>`

## File structure

```
src/perfrepair/app/__init__.py : docstring only
src/perfrepair/app/__main__.py : command: app source → <device>/<path id>/sites.json, app.json, scopes.json, units.json per project root, validated before writing; then one not_on_device per missing provider through terminate
src/perfrepair/app/detect.py : the detect step: non-test sources → import-checked, constant-folded sites, each resolved by the given resolver
src/perfrepair/app/facts/__init__.py : docstring only
src/perfrepair/app/facts/app_facts.py : the app.json document: project root, bundled, registers, SDK levels
src/perfrepair/app/facts/dependencies.py : declared crypto libraries from Gradle and the version catalog; Security provider registrations
src/perfrepair/app/facts/gate.py : app gate: directory, readable, project roots found, per root Android project, no escaping symlink, size caps; coded reasons
src/perfrepair/app/facts/libraries.yaml : artifact group and name prefix → JCA provider name
src/perfrepair/app/facts/path_id.py : the app's id from its absolute path; a multi-root unit's id; the folder for --app
src/perfrepair/app/facts/roots.py : outermost Android project roots under a folder, depth 4, symlinks not followed
src/perfrepair/app/facts/sdk.py : minSdk and targetSdk of the application module
src/perfrepair/app/facts/versions.py : per group:name the pinned version the build files hold: a literal coordinate, a Gradle map, a version catalog entry; newest wins; a variable or a range is none
src/perfrepair/app/find/__init__.py : docstring only
src/perfrepair/app/find/constants.py : same-file string constants folded: const val, top-level or object val, static final String, '+'
src/perfrepair/app/find/imports.py : whether a type name is the java.security / javax.crypto class
src/perfrepair/app/find/scan.py : getInstance calls in one file, across lines; Site and Argument
src/perfrepair/app/find/sources.py : source files tagged main, test or generated; build files; ignored folders
src/perfrepair/app/resolve.py : the only meeting of a site and the device: Primitives (probe, names, providers from the manifest); a site's provider and canonical algorithm, explicit or by manifest precedence
src/perfrepair/scope/__init__.py : docstring only
src/perfrepair/scope/build.py : the scope step: resolved sites → Scope per site with its lifecycle and settled requirements, and the unscoped; counts per lifecycle status
src/perfrepair/scope/engines.py : engines.yaml read and checked once: Engine (configuration, terminal, optional, requirements, operations, consumers), the origin tables
src/perfrepair/scope/engines.yaml : per engine type its lifecycle calls, requirement arguments, operations and consumers; origin calls, value-carrying specs, accessors, decoders
src/perfrepair/scope/extract.py : named functions and their spans: Java methods, Kotlin funs, expression bodies, constructors
src/perfrepair/scope/facts.py : a function's sinks and key source from patterns.yaml; the key source from the lifecycle's key origin when known, and from its settled origin where the view stayed open
src/perfrepair/scope/lifecycle/__init__.py : docstring only
src/perfrepair/scope/lifecycle/binding.py : where the created object goes first: chain, local, field, returned, argument, discarded
src/perfrepair/scope/lifecycle/depth1.py : one method away in the class: a field's other methods, a helper's callers, a callee; METHOD_BUDGET; requirement origins one away
src/perfrepair/scope/lifecycle/origins.py : a value's origin in the closed list, read back through same-method definitions, with its line
src/perfrepair/scope/lifecycle/read.py : one site's Reading: its Lifecycle (binding, steps, requirements, operations, status) and each requirement's argument
src/perfrepair/scope/lifecycle/settle.py : code settlement: field writes, in-class call arguments, returned values, a branch's operands; the budget; whether every path closes to one origin
src/perfrepair/scope/lifecycle/slice.py : calls on one named object in one scope from a point on, shadowing-aware; its escapes
src/perfrepair/scope/lifecycle/status.py : status and reasons from what the slice found
src/perfrepair/scope/patterns.yaml : sink and key-source patterns
src/perfrepair/scope/syntax/__init__.py : docstring only
src/perfrepair/scope/syntax/calls.py : a call's receiver, name, arguments and trailing lambda; the factory call at a line; a lambda's parameter and owner
src/perfrepair/scope/syntax/declarations.py : enclosing method and class, parameters, fields, what a name resolves to at a point
src/perfrepair/scope/syntax/grammar.py : the grammars' node types mapped to neutral kinds; language facts (scope functions, inline calls)
src/perfrepair/scope/syntax/node.py : Node: a parsed node as plain data
src/perfrepair/scope/syntax/parser.py : the one tree-sitter adapter, lazily imported; ParserMissing; source → Node tree
src/perfrepair/scope/syntax/usage.py : what the code around a value does with it; when a node runs later than it is written
src/perfrepair/scope/units/__init__.py : docstring only
src/perfrepair/scope/units/build.py : connected components of the links as Units; units.json's document; counts
src/perfrepair/scope/units/links.py : shared key and inverse links within a file, from lifecycles; which scopes link at all
src/perfrepair/scope/units/producers.py : producer → consumer links: by line, helper call, field write or parameter type
src/perfrepair/scope/units/relations.py : relations.yaml read and checked once
src/perfrepair/scope/units/relations.yaml : inverse operations, calls that perform one, calls that produce a key
src/perfrepair/scope/units/shapes.py : a scope's class, its method's return and parameter types, a file's lines
src/perfrepair/source/__init__.py : docstring only
src/perfrepair/source/language.py : the language table: suffix, script suffix, statement terminators, template, comment nesting, `name: Type`
src/perfrepair/source/lexer.py : the one Java and Kotlin lexer: per-char code/literal/comment classes, masking, literals, bracket matching, argument spans, expression end
```
