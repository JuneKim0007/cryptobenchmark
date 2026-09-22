#!/usr/bin/env python3
"""Runs the host pipeline in order and reports one readable failure.

  probe -> trial -> inventory -> effective        (tools/jca-contract)
  [--bench]  prepare -> measure -> analyse        (tools/quick-bench)

Config lookup: --config, then CRYPTOBENCH_CONFIG, then ~/.config/cryptobench/global.yaml, then config/global.yaml.
"""
import argparse, os, pathlib, shutil, subprocess, sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def fail(message):
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(1)


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


def gradle(project, arguments, stacktrace):
    wrapper = ROOT / "tools/jca-contract/gradlew"
    if not wrapper.is_file():
        fail(f"missing_file: {wrapper}")
    command = [str(wrapper), "-p", str(ROOT / "tools" / project), "run", "--no-daemon", "-q", f"--args={arguments}"]
    result = subprocess.run(command, capture_output=True, text=True)
    output = (result.stdout + result.stderr).splitlines()
    if result.returncode != 0:
        if stacktrace:
            print("\n".join(output), file=sys.stderr)
        reported, following = [], False
        for line in output:
            if line.startswith(("error:", "skipped:", "warning:")):
                reported.append(line[len("error: "):] if line.startswith("error: ") else line)
                following = True
            elif following and line.startswith("  "):
                reported.append(line)
            else:
                following = False
        noise = ("FAILURE:", "BUILD FAILED", "* Try:", "* Get more help", "* What went wrong", "> Process 'command", "Run with --", "* Exception is:")
        fallback = [line for line in output if line.strip() and not line.startswith(noise)]
        fail("\n".join(reported or fallback[-5:])[:2000])
    for line in output:
        if line.startswith(("warning:", "skipped:")):
            print(line)
    return result.stdout.strip().splitlines()


def summary(effective):
    import yaml
    document = yaml.safe_load(effective.read_text())
    entries = sum(len(names) for types in document["providers"].values() for names in types.values())
    for warning in document.get("warnings") or []:
        print(f"warning: {warning}")
    for skip in document.get("skipped") or []:
        print(f"skipped: {skip.get('provider', '*')} {skip.get('type', '*')} {skip.get('name', '*')}: {skip['reason']}")
    print(f"effective: {entries} entries, {len(document.get('skipped') or [])} skipped")


def main():
    parser = argparse.ArgumentParser(description="run the host pipeline")
    parser.add_argument("--config", help="path to global.yaml")
    parser.add_argument("--results", default=str(ROOT / "results"), help="output root (default: results/)")
    parser.add_argument("--discovery", choices=["overwrite", "keep"], default="overwrite",
                        help="overwrite: clear the discovery directory first; keep: add a new timestamped capture")
    parser.add_argument("--bench", action="store_true", help="also prepare, measure and analyse (quick-bench, JVM)")
    parser.add_argument("--stacktrace", action="store_true", help="print the tool's full output on failure")
    options = parser.parse_args()

    configuration = global_config(options.config)
    results = pathlib.Path(options.results).resolve()
    discovery, configured = results / "discovery", results / "configuration"
    if options.discovery == "overwrite" and discovery.exists():
        shutil.rmtree(discovery)
    discovery.mkdir(parents=True, exist_ok=True)

    print(f"config:    {configuration}")
    written = gradle("jca-contract", f"{discovery} {configured} {configuration}", options.stacktrace)
    for path in written:
        print(f"wrote:     {path}")
    effective = configured / "effective.yaml"
    if not effective.is_file():
        fail(f"missing_file: {effective}")
    summary(effective)

    if not options.bench:
        return
    capture = max(discovery.glob("probe_2*.yaml"), key=lambda p: p.name)
    trial = max(discovery.glob("trial_*.yaml"), key=lambda p: p.name)
    benchmark = results / "benchmark"
    gradle("quick-bench", f"{capture} {trial} {effective} {benchmark}", options.stacktrace)
    print(f"wrote:     {benchmark / 'benchmark.json'}")
    analysis = results / "analysis"
    subprocess.run([sys.executable, str(ROOT / "tools/quick-bench/analyze.py"), str(benchmark / "benchmark.json"), str(analysis)], check=True)


if __name__ == "__main__":
    main()
