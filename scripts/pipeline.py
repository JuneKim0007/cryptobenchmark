#!/usr/bin/env python3
"""Runs the host pipeline in order and reports one readable failure.

  probe -> trial -> inventory -> effective        (tools/jca-contract)
  [--bench]  prepare -> measure -> analyse        (tools/quick-bench)

Config lookup: --config, then CRYPTOBENCH_CONFIG, then ~/.config/cryptobench/global.yaml, then config/global.yaml.
"""
import argparse, os, pathlib, shutil, subprocess, sys, time

import effective_view
import gradle_runner
from failure import fail

ROOT = pathlib.Path(__file__).resolve().parent.parent


def global_config(argument):
    if argument:
        if not pathlib.Path(argument).is_file():
            fail(f"missing_file: {argument} (--config)")
        return pathlib.Path(argument).resolve()
    for candidate in (os.environ.get("CRYPTOBENCH_CONFIG"),
                      pathlib.Path.home() / ".config/cryptobench/global.yaml", ROOT / "config/global.yaml"):
        if candidate and pathlib.Path(candidate).is_file():
            return pathlib.Path(candidate).resolve()
    fail("no global.yaml: pass --config, set CRYPTOBENCH_CONFIG, or keep config/global.yaml")


def elapsed(label, started):
    print(f"took:      {label} in {time.monotonic() - started:.1f}s")


def summary(effective):
    view = effective_view.read(effective)
    for warning in view["warnings"]:
        print(f"warning: {warning}")
    for skip in view["skipped"]:
        print(f"skipped: {skip.get('provider', '*')} {skip.get('type', '*')} {skip.get('name', '*')}: {skip['reason']}")
    print(f"effective: {effective_view.entry_count(view['document'])} entries, {len(view['skipped'])} skipped")


def main():
    parser = argparse.ArgumentParser(description="run the host pipeline")
    parser.add_argument("--config", help="path to global.yaml")
    parser.add_argument("--results", default=str(ROOT / "results"), help="output root (default: results/)")
    parser.add_argument("--discovery", choices=["overwrite", "keep", "reuse"], default="overwrite",
                        help="overwrite: clear the discovery directory first; keep: add a new capture; reuse: keep the existing capture for this device")
    parser.add_argument("--bench", action="store_true", help="also prepare, measure and analyse (quick-bench, JVM)")
    parser.add_argument("--stacktrace", action="store_true", help="print the tool's full output on failure")
    parser.add_argument("--stream", action="store_true", help="show each tool's progress while it runs")
    options = parser.parse_args()
    sys.stdout.reconfigure(line_buffering=True)

    configuration = global_config(options.config)
    results = pathlib.Path(options.results).resolve()
    discovery, configured = results / "discovery", results / "configuration"
    if options.discovery == "overwrite" and discovery.exists():
        shutil.rmtree(discovery)
    discovery.mkdir(parents=True, exist_ok=True)

    print(f"config:    {configuration}")
    reuse = " --reuse" if options.discovery == "reuse" else ""
    started = time.monotonic()
    written = gradle_runner.run("jca-contract", f"{discovery} {configured} {configuration}{reuse}", options.stacktrace, options.stream)
    for path in written:
        print(f"wrote:     {path}")
    effective = configured / "effective.yaml"
    if not effective.is_file():
        fail(f"missing_file: {effective}")
    summary(effective)
    elapsed("discover and configure", started)

    if not options.bench:
        return
    capture = max(discovery.glob("probe_2*.yaml"), key=lambda p: p.name)
    trial = max(discovery.glob("trial_*.yaml"), key=lambda p: p.name)
    benchmark, preparation = results / "benchmark", results / "preparation"
    started = time.monotonic()
    repetitions = effective_view.process_repetitions(effective_view.read(effective)['document'])
    written = []
    for repetition in range(1, repetitions + 1):
        into = benchmark if repetitions == 1 else benchmark / f"process-{repetition}"
        if repetitions > 1:
            print(f"process:   {repetition} of {repetitions}")
        gradle_runner.run("quick-bench", f"{capture} {trial} {effective} {into} {preparation}", options.stacktrace, options.stream)
        written.append(into / "benchmark.json")
    if repetitions > 1:
        gradle_runner.run("quick-bench", " ".join([str(benchmark)] + [str(path) for path in written]), options.stacktrace, options.stream, main_class="MergeRunsKt")
    print(f"wrote:     {preparation / 'prepared.yaml'}")
    print(f"wrote:     {benchmark / 'benchmark.json'}")
    elapsed("prepare and measure", started)
    analysis = results / "analysis"
    started = time.monotonic()
    subprocess.run([sys.executable, str(ROOT / "tools/quick-bench/analyze.py"), str(benchmark / "benchmark.json"), str(analysis),
                    str(effective), str(preparation / "prepared.yaml")], check=True)
    subprocess.run([sys.executable, str(ROOT / "tools/quick-bench/charts.py"), str(benchmark / "benchmark.json"),
                    str(preparation / "prepared.yaml"), str(effective), str(results)], check=True)
    elapsed("analyse", started)


if __name__ == "__main__":
    main()
