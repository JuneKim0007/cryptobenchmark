"""The two phases of a facade run, each a guide child with every path named: crypto stops after the device stage, guided
works on the folder it wrote. Each prints one coded line; the first that fails stops the next."""
import json
import os
import pathlib
import subprocess
import sys
import tempfile
from dataclasses import dataclass

from cryptobench import paths

RESUME = "resume"


@dataclass(frozen=True)
class Outcome:
    code: int
    device: str | None = None
    run: str | None = None
    stop: str | None = None


def child_env(index, root):
    """Pins what a child's own lookups could find: an in-process step takes no --perfrepair-config, so the variable says it."""
    env = {k: v for k, v in os.environ.items() if k != "CRYPTOBENCH_CONFIG"}
    env["PERFREPAIR_CONFIG"] = str(index.llm_config)
    env["CRYPTOBENCH_ROOT"] = str(root)
    env["PYTHONPATH"] = os.pathsep.join(p for p in (str(paths.repo().perf_repair_source), str(paths.repo().library), env.get("PYTHONPATH")) if p)
    return env


def common_flags(index, settings_file, outcome_file):
    harness = ("--harness-config", str(index.harness_config)) if index.harness_config else ()
    return ["--perfrepair-config", str(index.llm_config), "--config", str(index.crypto_config), *harness,
            "--run-settings", str(settings_file), "--outcome", str(outcome_file)]


def crypto_flags(index):
    run_id = ("--run-id", index.run_id) if index.run_id else ()
    return ["--results-root", str(index.results), "--stop-after-device", *run_id, "--on-existing", index.on_existing]


def guided_flags(crypto):
    # resume: the crypto phase applied onExisting; overwrite here would clear what it just wrote
    return ["--device-results", crypto.device, "--run-id", crypto.run, "--on-existing", RESUME]


def _guide(index, flags, settings_file, outcome_file, root):
    command = [sys.executable, "-m", "perfrepair", "guide", *common_flags(index, settings_file, outcome_file), *flags]
    code = subprocess.run(command, cwd=paths.code_root(), env=child_env(index, root), check=False).returncode
    if not outcome_file.is_file():
        return Outcome(code)
    done = json.loads(outcome_file.read_text())
    return Outcome(code, done.get("device"), done.get("run"), done.get("code"))


def _why(outcome):
    return f"{outcome.stop or 'no_code'} exit={outcome.code}"


def run_phases(index, tree_document, root=None, echo=print):
    """The worst exit of the phases that ran."""
    root = paths.code_root() if root is None else root
    with tempfile.TemporaryDirectory(prefix="facade-") as folder:
        folder = pathlib.Path(folder)
        settings_file = folder / "settings.json"
        settings_file.write_text(json.dumps(tree_document))
        crypto = _guide(index, crypto_flags(index), settings_file, folder / "crypto.json", root)
        if crypto.code != 0 or not crypto.device or not crypto.run:
            echo(f"facade crypto: crypto_failed: {_why(crypto)}")
            echo("facade guided: guided_not_run: the crypto phase failed")
            return crypto.code or 1
        echo(f"facade crypto: crypto_ok: device {crypto.device}, run {crypto.run}")
        guided = _guide(index, guided_flags(crypto), settings_file, folder / "guided.json", root)
        echo("facade guided: guided_ok" if guided.code == 0 else f"facade guided: guided_stopped: {_why(guided)}")
        return guided.code
