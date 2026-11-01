# App

## Calls
- `docs/replacement.md` : the detect and scope steps, the Scope contract
- `docs/artifacts.md` : `apps/<app>/sites.json`, `app.json`, `scopes.json`

## Rules
- static: detect and scope read the app tree and never edit it; no model call.
- data: crypto libraries live in `app/libraries.yaml`, sink and key-source patterns in `scope/patterns.yaml`, never in code.
- drop: a site that is not the platform class is recorded in `sites.json` `dropped` with its reason; one without an enclosing function in `scopes.json` `unscoped`.
- parser: a bracket-matching lexer over comment- and string-masked text, no grammar dependency, so ids do not depend on what is installed.
- ids: a scope id is `scope_id(app, file, function, line, call)`; output is sorted, so reruns are byte-identical.

## Workflow
- run: `python3 -m perfrepair.app --manifest <m> --app <src> --run <run> --name <app>`

## File structure

```
src/perfrepair/app/__init__.py : docstring only
src/perfrepair/app/__main__.py : command: app source → apps/<name>/sites.json, app.json, scopes.json, validated before writing
src/perfrepair/app/app_facts.py : the app.json document
src/perfrepair/app/constants.py : same-file string constants folded: const val, top-level or object val, static final String, '+'
src/perfrepair/app/dependencies.py : declared crypto libraries from Gradle and the version catalog; Security provider registrations
src/perfrepair/app/detect.py : the detect step: non-test sources → import-checked, constant-folded, resolved sites
src/perfrepair/app/gate.py : app root gate: directory, readable, Android project, no escaping symlink, size caps; coded reasons
src/perfrepair/app/imports.py : whether a type name is the java.security / javax.crypto class
src/perfrepair/app/lexer.py : the one Java and Kotlin lexer: per-char code/literal/comment classes, masking, literals, bracket matching, argument spans, expression end
src/perfrepair/app/libraries.yaml : artifact group and name prefix → JCA provider name
src/perfrepair/app/resolve.py : a site's provider and canonical algorithm, explicit or by manifest precedence
src/perfrepair/app/scan.py : getInstance calls in one file, across lines; Site and Argument
src/perfrepair/app/sdk.py : minSdk and targetSdk of the application module
src/perfrepair/app/sources.py : source files tagged main, test or generated; build files; ignored folders
src/perfrepair/scope/__init__.py : docstring only
src/perfrepair/scope/build.py : the scope step: resolved sites → Scope per site, and the unscoped
src/perfrepair/scope/extract.py : named functions and their spans: Java methods, Kotlin funs, expression bodies, constructors
src/perfrepair/scope/facts.py : a function's sinks and key source from patterns.yaml
src/perfrepair/scope/patterns.yaml : sink and key-source patterns
```
