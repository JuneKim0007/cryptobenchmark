"""A pipeline.py stand-in: the suite's file stem picks what it does; it prints ANDROID_SERIAL and its mode like a run's lines."""
import os, pathlib, signal, sys, time

import yaml

args = sys.argv[1:]
config = pathlib.Path(args[args.index("--config") + 1])
results = pathlib.Path(args[args.index("--results") + 1])
suite = pathlib.Path(yaml.safe_load(config.read_text())["selection"]["testSet"]).stem
mode = "--device" if "--device" in args else "--bench"
print(f"config:    {config}")
print(f"serial:    {os.environ.get('ANDROID_SERIAL', '-')} {mode} {'--per-suite' in args}", flush=True)
if suite == "fails":
    print("error: device_lost: adb shell: error: closed", file=sys.stderr)
    sys.exit(1)
if suite == "sleeps":
    def stopped(*_):
        print("error: interrupted: stopped by SIGTERM", file=sys.stderr, flush=True)
        sys.exit(130)
    signal.signal(signal.SIGTERM, stopped)
    time.sleep(60)
print(f"results:   {results}/dev-{os.environ.get('ANDROID_SERIAL', 'host')}/{suite}")
