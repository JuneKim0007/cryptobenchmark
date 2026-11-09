"""A --harness run: perf-repair's scopes generated and interop-checked on the device, original against patched; nothing is timed."""
import pathlib, shutil, time

import yaml

from device.identity import capture_id
from failure import fail
from cryptobench import paths
from results import layout as results_layout
from results.manifest import manifest
from scope import generate as scope_generate
from scope import results as scope_results
from scope.harness import HarnessError
from stages.discover import discover
from stages.measuring import push
from stages.took import elapsed

# beside scoped/, which a failed run rolls back: the plan a failure line points at
FAILED_PLAN = "scoped-plan.failed.yaml"


def generate_scopes(options, scoped):
    started = time.monotonic()
    plan, compiled = scope_generate.generate(options.harness, paths.repo().gradle_root, scoped)
    elapsed(f"generate and compile {len(compiled)} scopes", started)
    if not compiled:
        fail(f"nothing_to_check: no scope compiled, see {scoped.parent / FAILED_PLAN}")
    print(f"wrote:     {plan}")
    return plan


def require_harness_device(harness, capture):
    """A harness belongs to one device's folder; another device's numbers there would read as that device's."""
    built_for = harness.parent.parent / results_layout.MANIFEST
    if built_for.is_file():
        wanted, attached = (yaml.safe_load(built_for.read_text()) or {}).get("deviceId"), capture_id(capture)
        if wanted != attached:
            fail(f"harness_other_device: {harness} was built for {wanted}, the attached device is {attached}")


def check_scopes(options, configuration, device, results, scoped, plan):
    """The interop check in one process; the files for the manifest."""
    _discovery, effective, capture, trial, files = discover(options, configuration, device, results)
    require_harness_device(pathlib.Path(options.harness).resolve(), capture)
    push(device, options, [effective, capture, trial])
    started = time.monotonic()
    print("check:     ScopedInterop on the device")
    interop = device.check_scopes(scoped)
    record = scope_results.merge(plan, interop)
    files.update(scopedPlan=plan, scopedInterop=interop)
    for scope in record["scopes"]:
        print(f"scope:     {scope['id']} {scope['status']}" + (f": {scope['reason']}" if scope.get("reason") else "")
              + (f" ({scope['interop'].get('reason')})" if scope.get("interop", {}).get("reason") else ""))
    elapsed("interop check", started)
    return files


def keep_failed_plan(scoped):
    """The rollback removes scoped/; the plan of the failed run is kept beside it."""
    plan, kept = scoped / scope_generate.PLAN, scoped.parent / FAILED_PLAN
    if plan.is_file():
        shutil.copyfile(plan, kept)
        print(f"kept:      {kept}")


def harness_run(options, configuration, device, results):
    (results / FAILED_PLAN).unlink(missing_ok=True)
    try:
        with results_layout.kept_until_replaced(results / "scoped") as scoped:
            try:
                plan = generate_scopes(options, scoped)
                files = check_scopes(options, configuration, device, results, scoped, plan)
            except (HarnessError, scope_generate.GenerateError, scope_results.ScopeResultError) as error:
                keep_failed_plan(scoped)
                fail(str(error))
            except BaseException:
                keep_failed_plan(scoped)
                raise
            manifest(results, "device", configuration, files)
    finally:
        scope_generate.clean(paths.repo().gradle_root)


def checked_folder(options):
    if options.results:
        fail("--results: a --harness run writes checked/ beside its harness.yaml")
    checked = pathlib.Path(options.harness).resolve().parent / "checked"
    results_layout.warn_if_temp(checked)
    return checked
