"""The energy steps of pipeline.py --device: capture selection, the rail pre-flight, and tools/energy."""
import pathlib, subprocess, sys, time

import yaml

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.append(str(ROOT / "tools/energy"))
from capture import capture  # noqa: E402
PREFLIGHT_SECONDS = 3
# The busy window spins every core; the first case must not start on that heat.
SETTLE_SECONDS = 15
RAILS_CONFIG = ('buffers { size_kb: 4096 }\n'
                'data_sources { config { name: "android.power" android_power_config { battery_poll_ms: 100 collect_power_rails: true } } }\n'
                'duration_ms: {millis}\n')


class EnergyError(Exception):
    pass


def captures(effective):
    document = yaml.safe_load(effective.read_text())
    default = capture(document.get("run"))
    found = set()
    for types in (document.get("providers") or {}).values():
        for names in types.values():
            for entry in names.values():
                for one in entry if isinstance(entry, list) else [entry]:
                    found.add(capture(one, default))
    return found or {default}


def tool(python, script, *arguments, stacktrace=False):
    """Runs in tools/energy's own venv: it needs perfetto, which the host pipeline does not."""
    result = subprocess.run([python, str(ROOT / "tools/energy" / script), *map(str, arguments)], capture_output=True, text=True)
    if result.returncode != 0:
        if "No module named" in result.stderr:
            raise EnergyError(f"missing_module: {result.stderr.strip().splitlines()[-1]}; "
                              f"pip install -r tools/energy/requirements.txt into {python}, or pass --energy-python")
        if stacktrace:
            print(result.stdout + result.stderr)
        raise EnergyError(f"tools/energy/{script}: {(result.stderr or result.stdout).strip().splitlines()[-1]}")
    print(result.stdout.rstrip())


def preflight(session, discovery, python, accept_unresponsive, stacktrace=False):
    folder = discovery / "energy-preflight"
    folder.mkdir(exist_ok=True)
    config = folder / "rails.pbtx"
    config.write_text(RAILS_CONFIG.replace("{millis}", str(PREFLIGHT_SECONDS * 1000)))
    session.preflight(config, folder / "idle.pftrace", folder / "busy.pftrace")
    capability = discovery / "energy.yaml"
    tool(python, "preflight.py", folder / "idle.pftrace", folder / "busy.pftrace", PREFLIGHT_SECONDS, capability,
         *(["--accept-unresponsive"] if accept_unresponsive else []), stacktrace=stacktrace)
    time.sleep(SETTLE_SECONDS)
    return capability


def joules(python, captures_found, capability, preparation, data, traces, dry_calls, out, stacktrace=False):
    arguments = ["--capability", capability, "-o", out]
    if "measured" in captures_found:
        arguments += ["--prepared", preparation / "prepared.yaml", "--benchmark-data", data, "--traces", traces]
    if "dry" in captures_found:
        arguments += ["--dry-trace", traces / "dry.pftrace", "--dry-calls", dry_calls]
    tool(python, "energy.py", *arguments, stacktrace=stacktrace)
