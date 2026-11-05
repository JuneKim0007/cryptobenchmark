"""harness.yaml to generated androidTest sources and scoped-plan.yaml; a scope that fails a check or the compiler is recorded and left out."""
import pathlib, shutil

import yaml

from scope import call_site as scope_call_site
from scope import compile as scope_compile
from scope import dependencies as scope_dependencies
from scope import harness as scope_harness
from scope import inputs as scope_inputs
from scope import interop as scope_interop
from scope import languages as scope_languages
from scope import signature as scope_signature
from scope import wrapper as scope_wrapper

PLAN = "scoped-plan.yaml"
GENERATED_MARK = "/cryptobench/scoped/"


class GenerateError(Exception):
    pass


def clean(root):
    shutil.rmtree(pathlib.Path(root) / scope_wrapper.FOLDER, ignore_errors=True)


def checked(scope):
    signatures = {v: scope_languages.of(scope.language).parse(getattr(scope, v)) for v in scope_wrapper.VARIANTS}
    before, after = signatures["before"], signatures["after"]
    if (before.name, before.parameters, before.returns) != (after.name, after.parameters, after.returns):
        raise scope_signature.SignatureError(f"signature_changed: before {before.name}{before.parameters}, after {after.name}{after.parameters}")
    for parameter in before.parameters:
        scope_inputs.expression(parameter, scope)
    return signatures, scope_dependencies.resolve(scope.dependencies, scope.imports, scope.language)


def entries(scopes, candidates):
    plans = scope_interop.plan({i: candidates[i][0]["before"] for i in scopes}, {i: scopes[i].inverse for i in scopes},
                              {i for i in scopes if scopes[i].upgrade})
    return {i: scope_wrapper.Entry(scopes[i], candidates[i][0], candidates[i][1].stubs, plans[i]) for i in scopes}


def write(root, chosen):
    clean(root)
    for entry in chosen.values():
        for variant in scope_wrapper.VARIANTS:
            relative, text = scope_wrapper.wrapper(entry, variant)
            (root / relative).parent.mkdir(parents=True, exist_ok=True)
            (root / relative).write_text(text)
    (root / scope_wrapper.FOLDER).mkdir(parents=True, exist_ok=True)
    (root / scope_wrapper.FOLDER / f"{scope_wrapper.CATALOG}.kt").write_text(scope_wrapper.catalog(chosen))


def compile_each(root, scopes, candidates, compiler, records):
    write(root, entries(scopes, candidates))
    if not compiler(root):
        return scopes
    passed = {}
    for scope_id, scope in scopes.items():
        write(root, entries({scope_id: scope}, candidates))
        failure = compiler(root)
        if not failure:
            passed[scope_id] = scope
        elif not any(GENERATED_MARK in line for line in failure):
            raise GenerateError("harness_build_failed: the android test sources fail outside the generated scopes:\n" + "\n".join(failure))
        else:
            records[scope_id].update(status="not_compilable", reason="compile_error", compilerErrors=failure)
    if passed:
        write(root, entries(passed, candidates))
        failure = compiler(root)
        if failure:
            raise GenerateError("scopes_conflict: each scope compiles alone, not together:\n" + "\n".join(failure))
    return passed


def record_of(scope):
    return {"id": scope.id, "function": scope.function, "language": scope.language, "current": scope.current,
            "option": scope.option,
            "inputs": {"inputSize": scope.input_size, "keySize": scope.key_size, "from": scope.input_source},
            "metrics": list(scope.metrics),
            "status": "compiled", "callSite": scope_call_site.planned(scope)}


def admitted(scope, record):
    """The scope's checked candidate, or None with the record saying why it is not generated."""
    if scope.not_measurable:
        record.update(status="not_measurable", reason=scope.not_measurable)
        return None
    try:
        candidate = checked(scope)
    except (scope_signature.SignatureError, scope_inputs.InputError) as reason:
        record.update(status="not_compilable", reason=str(reason))
        return None
    resolution = candidate[1]
    if resolution.unsatisfied:
        record.update(status="not_compilable", reason="unsatisfied_dependencies", identifiers=list(resolution.unsatisfied))
        return None
    if resolution.deferred:
        record["deferredToCompiler"] = list(resolution.deferred)
    return candidate


def call_sites(plan):
    return [r for r in plan["scopes"] if (r.get("callSite") or {}).get("status") == "planned"]


def generate(harness_path, root, out, compiler=scope_compile.gradle):
    """No scope compiled still writes an empty catalog: the call sites are measured through the same test APK."""
    root, out = pathlib.Path(root), pathlib.Path(out)
    harness = scope_harness.read(harness_path)
    records, candidates, scopes = {}, {}, {}
    for scope in harness.scopes:
        records[scope.id] = record_of(scope)
        candidate = admitted(scope, records[scope.id])
        if candidate:
            candidates[scope.id], scopes[scope.id] = candidate, scope
    compiled = compile_each(root, scopes, candidates, compiler, records) if scopes else {}
    final = entries(compiled, candidates) if compiled else {}
    if not compiled:
        write(root, final)
    for scope_id, entry in final.items():
        plan = {key: value for key, value in vars(entry.interop).items() if value is not None and key != "index"}
        records[scope_id].update(interop=plan, cases=[f"scope:{scope_id}:{v}" for v in scope_wrapper.VARIANTS])
    out.mkdir(parents=True, exist_ok=True)
    document = {"schemaVersion": 1, "app": harness.app, "harness": str(pathlib.Path(harness_path).resolve()),
                "seed": scope_inputs.SEED, "scopes": list(records.values())}
    (out / PLAN).write_text(yaml.safe_dump(document, sort_keys=False))
    return out / PLAN, list(compiled)

