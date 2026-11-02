# App

## Calls
- `docs/replacement.md` : the detect and scope steps, the Scope contract
- `docs/artifacts.md` : `<app>/sites.json`, `app.json`, `scopes.json`

## Rules
- static: detect and scope read the app tree and never edit it; no model call.
- data: crypto libraries live in `app/facts/libraries.yaml`, sink and key-source patterns in `scope/patterns.yaml`, never in code.
- drop: a site that is not the platform class is recorded in `sites.json` `dropped` with its reason; one without an enclosing function in `scopes.json` `unscoped`.
- parser: a bracket-matching lexer over comment- and string-masked text, no grammar dependency, so ids do not depend on what is installed.
- roots: one project root keeps the given name; several are units `<name>.<root dirs joined by '.'>`, each scanned from its root.
- layers: `app/find/` reads only source text, never device data; `app/facts/` reads the app tree; `app/resolve.py` is the only module where a site meets the device's primitives (Probe, providers); `tests/test_layers.py` checks it.
- ids: a scope id is `scope_id(app, file, function, line, call)`; output is sorted, so reruns are byte-identical.

## Workflow
- run: `python3 -m perfrepair.app --device-results <device> --app <src>`

## File structure

```
src/perfrepair/app/__init__.py : docstring only
src/perfrepair/app/__main__.py : command: app source → <device>/<path id>/sites.json, app.json, scopes.json per project root, validated before writing
src/perfrepair/app/detect.py : the detect step: non-test sources → import-checked, constant-folded sites, each resolved by the given resolver
src/perfrepair/app/facts/__init__.py : docstring only
src/perfrepair/app/facts/app_facts.py : the app.json document: project root, bundled, registers, SDK levels
src/perfrepair/app/facts/dependencies.py : declared crypto libraries from Gradle and the version catalog; Security provider registrations
src/perfrepair/app/facts/gate.py : app gate: directory, readable, project roots found, per root Android project, no escaping symlink, size caps; coded reasons
src/perfrepair/app/facts/libraries.yaml : artifact group and name prefix → JCA provider name
src/perfrepair/app/facts/path_id.py : the app's id from its absolute path; a multi-root unit's id; the folder for --app
src/perfrepair/app/facts/roots.py : outermost Android project roots under a folder, depth 4, symlinks not followed
src/perfrepair/app/facts/sdk.py : minSdk and targetSdk of the application module
src/perfrepair/app/find/__init__.py : docstring only
src/perfrepair/app/find/constants.py : same-file string constants folded: const val, top-level or object val, static final String, '+'
src/perfrepair/app/find/imports.py : whether a type name is the java.security / javax.crypto class
src/perfrepair/app/find/scan.py : getInstance calls in one file, across lines; Site and Argument
src/perfrepair/app/find/sources.py : source files tagged main, test or generated; build files; ignored folders
src/perfrepair/app/resolve.py : the only meeting of a site and the device: Primitives (probe, names, providers from the manifest); a site's provider and canonical algorithm, explicit or by manifest precedence
src/perfrepair/scope/__init__.py : docstring only
src/perfrepair/scope/build.py : the scope step: resolved sites → Scope per site, and the unscoped
src/perfrepair/scope/extract.py : named functions and their spans: Java methods, Kotlin funs, expression bodies, constructors
src/perfrepair/scope/facts.py : a function's sinks and key source from patterns.yaml
src/perfrepair/scope/patterns.yaml : sink and key-source patterns
src/perfrepair/source/__init__.py : docstring only
src/perfrepair/source/language.py : the language table: suffix, script suffix, statement terminators, template, comment nesting, `name: Type`
src/perfrepair/source/lexer.py : the one Java and Kotlin lexer: per-char code/literal/comment classes, masking, literals, bracket matching, argument spans, expression end
```
