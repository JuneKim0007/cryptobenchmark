"""Discover and configure: the probe, ConfigureKt or ProbeKt, effective.yaml, and the device folder the capture names."""
import pathlib, shutil, time
from dataclasses import dataclass

from cryptobench.shared.settings import effective_view
from cryptobench.shared.device import gradle_runner
from cryptobench.shared.device.identity import capture_id, device_id
from cryptobench.shared.errors.failures import CommandError
from cryptobench.shared import paths
from cryptobench.shared.results import layout as results_layout
from cryptobench.shared.settings import bundled
from cryptobench.stages.discovery import build_versions, capture_files, facts, probe_store
from cryptobench.stages.discovery.probe import probe
from cryptobench.pipeline.took import elapsed
from cryptobench.shared.log.warn import warn
from cryptobench.shared.document.document import parse_yaml


def summary(effective):
    view = effective_view.read(effective)
    for warning in view["warnings"]:
        warn(warning)
    for skip in view["skipped"]:
        print(f"skipped: {skip.get('provider', '*')} {skip.get('type', '*')} {skip.get('name', '*')}: {skip['reason']}")
    print(f"effective: {effective_view.entry_count(view['document'])} entries, {len(view['skipped'])} skipped")


def discover_in_place(options, configuration, device, results, shipped):
    """Writes discovery/ and configuration/ straight into results; shipped is providers.bundled as the parse-only check read it."""
    discovery, configured = paths.RunTree(results).discovery.root, paths.RunTree(results).configuration.root
    if options.discovery in results_layout.REPLACING and discovery.exists():
        shutil.rmtree(discovery)
    discovery.mkdir(parents=True, exist_ok=True)

    print(f"config:    {configuration}")
    if device:
        started = time.monotonic()
        device.install(bundled.gradle_properties(shipped))
        elapsed("build and install", started)
        started, before = time.monotonic(), capture_files.stamped(discovery)
        build = build_versions.read(device, device.identity()["sdkInt"])
        capture, value = probe_store.verified(device, discovery, shipped, store(options), build) if options.discovery == "verify" else (None, None)
        if capture:
            capture, trial = capture_files.pair(capture)
        else:
            probe(device, discovery, bundled.instrumentation_arguments(shipped))
            capture, trial = capture_files.added(discovery, before)
            if value:
                probe_store.keep(store(options), value, capture)
        known = facts.gather(device, discovery, capture, build)
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
        raise CommandError(f"missing_file: {effective}")
    bundled.check_effective(effective, shipped)
    summary(effective)
    elapsed("discover and configure", started)
    return located(results, capture.name)


def store(options):
    return pathlib.Path(options.probe_store).expanduser().resolve()


@dataclass(frozen=True)
class Discovered:
    """A run's discovery folder, its effective.yaml, capture and trial, and the manifest's files of them (callers add to files)."""
    discovery: pathlib.Path
    effective: pathlib.Path
    capture: pathlib.Path
    trial: pathlib.Path | None
    files: dict


def located(results, capture_name):
    """By the name discover_in_place() returned: after a publish into a kept discovery/ the folder holds older captures too."""
    discovery, configured = paths.RunTree(results).discovery.root, paths.RunTree(results).configuration.root
    capture, trial = capture_files.pair(discovery / capture_name)
    effective = paths.Configuration(configured).effective
    files = {key: path for key, path in (("probe", capture), ("trial", trial), ("requirements", capture_files.requirements(capture)), ("inventory", paths.Configuration(configured).inventory),
                                         ("effective", effective), ("report", paths.Configuration(configured).report)) if path and path.is_file()}
    return Discovered(discovery, effective, capture, trial, files)


def seed_reuse(options, root, stage, suite=None):
    """--discovery reuse names no folder until the JVM's id is known; ProbeKt --reuse still decides whether the capture fits."""
    existing = paths.RunTree(results_layout.unit_folder(root, device_id(host_runtime(options)), suite)).discovery.root
    if existing.is_dir():
        results_layout.merge_folder(existing, paths.RunTree(stage).discovery.root)


def discover_staged(options, configuration, device, root, stage, shipped, suite=None):
    """Everything stays in stage; the caller publishes it."""
    if options.discovery == "reuse":
        seed_reuse(options, root, stage, suite)
    return discover_in_place(options, configuration, device, stage, shipped)


def keep_nothing(_effective, _capture, _target):
    return ()


def discover_published(options, configuration, device, root, shipped, kept=keep_nothing, suite=None):
    """A failed probe or configure leaves nothing; from here on the folder has its real name and no manifest until the run ends. kept(effective,
    capture, folder) names the paths of the earlier unit the publish leaves in place."""
    with results_layout.staged(root) as stage:
        found = discover_staged(options, configuration, device, root, stage, shipped, suite)
        results = results_layout.unit_folder(root, capture_id(found.capture), suite)
        results_layout.publish(stage, results, options.discovery, kept(found.effective, found.capture, results))
    print(f"results:   {results}")
    return results, located(results, found.capture.name)


def host_runtime(options):
    return parse_yaml("\n".join(gradle_runner.run("", options.stacktrace, options.stream, main_class="RuntimeFieldsKt")), "RuntimeFieldsKt output")
