"""Discover and configure: the probe, ConfigureKt or ProbeKt, effective.yaml, and the device folder the capture names."""
import shutil, time

import effective_view, gradle_runner
from device import facts
from device.identity import capture_id, device_id
from failure import fail
from cryptobench import paths
from results import layout as results_layout
import bundled
from stages import capture_files, config_check, guide
from stages.took import elapsed
from cryptobench.document import parse_yaml


def summary(effective):
    view = effective_view.read(effective)
    for warning in view["warnings"]:
        print(f"warning: {warning}")
    for skip in view["skipped"]:
        print(f"skipped: {skip.get('provider', '*')} {skip.get('type', '*')} {skip.get('name', '*')}: {skip['reason']}")
    print(f"effective: {effective_view.entry_count(view['document'])} entries, {len(view['skipped'])} skipped")


def discover(options, configuration, device, results):
    discovery, configured = paths.RunTree(results).discovery.root, paths.RunTree(results).configuration.root
    if options.discovery == "overwrite" and discovery.exists():
        shutil.rmtree(discovery)
    discovery.mkdir(parents=True, exist_ok=True)

    print(f"config:    {configuration}")
    shipped = config_check.parsed(configuration)["bundled"]
    if device:
        started = time.monotonic()
        device.install(bundled.gradle_properties(shipped))
        elapsed("build and install", started)
        started, before = time.monotonic(), capture_files.stamped(discovery)
        device.probe(discovery, bundled.instrumentation_arguments(shipped))
        capture, trial = capture_files.added(discovery, before)
        known = facts.gather(device, discovery, capture)
        written = gradle_runner.run(f"{capture} {trial} {configured} {configuration} --facts={known}", options.stacktrace, options.stream, main_class="ConfigureKt")
    else:
        reuse = " --reuse" if options.discovery == "reuse" else ""
        started, before = time.monotonic(), capture_files.stamped(discovery)
        written = gradle_runner.run(f"{discovery} {configured} {configuration}{reuse}", options.stacktrace, options.stream, main_class="ProbeKt",
                                    properties=bundled.gradle_properties(shipped))
        capture, trial = capture_files.printed(written, discovery)
        if reuse:
            capture_files.reprobed(before, capture)
    for path in written:
        print(f"wrote:     {path}")
    effective = paths.Configuration(configured).effective
    if not effective.is_file():
        fail(f"missing_file: {effective}")
    bundled.check_effective(effective, shipped)
    summary(effective)
    elapsed("discover and configure", started)
    return located(results, capture.name)


def located(results, capture_name):
    """By the name discover() returned: after a publish into a kept discovery/ the folder holds older captures too."""
    discovery, configured = paths.RunTree(results).discovery.root, paths.RunTree(results).configuration.root
    capture, trial = capture_files.pair(discovery / capture_name)
    effective = paths.Configuration(configured).effective
    files = {key: path for key, path in (("probe", capture), ("trial", trial), ("requirements", capture_files.requirements(capture)), ("inventory", paths.Configuration(configured).inventory),
                                         ("effective", effective), ("report", paths.Configuration(configured).report)) if path and path.is_file()}
    return discovery, effective, capture, trial, files


def seed_reuse(options, root, stage):
    """--discovery reuse names no folder until the JVM's id is known; ProbeKt --reuse still decides whether the capture fits."""
    existing = paths.Results(root).device(device_id(host_runtime(options))).discovery.root
    if existing.is_dir():
        results_layout.merge_folder(existing, paths.RunTree(stage).discovery.root)


def discover_staged(options, configuration, device, root, stage):
    if options.discovery == "reuse":
        seed_reuse(options, root, stage)
    return discover(options, configuration, device, stage)


def device_discover(options, configuration, device, root):
    """A failed probe or configure leaves nothing; from here on the folder has its real name and no manifest until the run ends."""
    with results_layout.staged(root) as stage:
        capture = discover_staged(options, configuration, device, root, stage)[2]
        results = root / capture_id(capture)
        results_layout.publish(stage, results, options.discovery)
    print(f"results:   {results}")
    parts = located(results, capture.name)
    parts[4]["guide"] = guide.write(parts[1], parts[2])
    return results, parts


def host_runtime(options):
    return parse_yaml("\n".join(gradle_runner.run("", options.stacktrace, options.stream, main_class="RuntimeFieldsKt")), "RuntimeFieldsKt output")
