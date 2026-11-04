"""The manafa source on the host: its process (manafa_session.py), started around the measured window."""
import json, pathlib, subprocess

from .runner import TOOLS, EnergyError, case_arguments

SESSION = TOOLS / "manafa_session.py"
PREFLIGHT_SECONDS = 3
LOG = "manafa.log"
CANNOT_START = "manafa_cannot_start"


def _last_line(text):
    lines = text.strip().splitlines()
    return lines[-1] if lines else ""


class ManafaSource:

    def __init__(self, host):
        self.host = host
        self.process = None

    def python(self):
        # the process runs in its own folder; a venv's python is a symlink that must not be resolved
        return str(pathlib.Path(self.host.python).absolute()) if "/" in self.host.python else self.host.python

    def preflight(self, _session, discovery, _accept_unresponsive):
        folder = discovery / "energy-preflight"
        folder.mkdir(exist_ok=True)
        capability = (discovery / "energy.yaml").resolve()
        try:
            result = subprocess.run([self.python(), str(SESSION), "--check", str(PREFLIGHT_SECONDS), "--capability", str(capability)],
                                    capture_output=True, text=True, cwd=folder, env=self.host.adb_environment(), timeout=self.host.timeout)
        except subprocess.TimeoutExpired:
            raise self.host.expired("manafa pre-flight") from None
        if result.returncode != 0:
            if self.host.stacktrace:
                print(result.stderr)
            raise EnergyError(_last_line(result.stdout) or f"{CANNOT_START}: {_last_line(result.stderr)}")
        print(result.stdout.rstrip())
        return discovery / "energy.yaml"

    def window(self, folder):
        return ManafaWindow(self, pathlib.Path(folder).resolve() / "manafa")

    def joules(self, *case_paths):
        if self.process is None:
            raise EnergyError("manafa_not_started: joules without a window around the run")
        process, self.process = self.process, None
        request = [str(pathlib.Path(a).resolve()) if isinstance(a, pathlib.Path) else a for a in case_arguments(*case_paths)]
        try:
            output, _ = process.communicate(json.dumps(request) + "\n", timeout=self.host.timeout)
        except subprocess.TimeoutExpired:
            process.kill()
            raise self.host.expired("manafa joules") from None
        if process.returncode != 0:
            raise EnergyError(_last_line(output) or f"manafa_failed: exit {process.returncode}")
        print(output.rstrip())


class ManafaWindow:

    def __init__(self, source, folder):
        self.source, self.folder = source, folder

    def __enter__(self):
        self.folder.mkdir(parents=True, exist_ok=True)
        with open(self.folder / LOG, "w") as log:
            process = subprocess.Popen([self.source.python(), str(SESSION)], stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                       stderr=log, text=True, cwd=self.folder, env=self.source.host.adb_environment())
        answer = process.stdout.readline().strip()
        if answer != "started":
            process.wait()
            raise EnergyError(answer or f"{CANNOT_START}: {_last_line((self.folder / LOG).read_text())}")
        self.source.process = process
        return self

    def __exit__(self, failure, _value, _traceback):
        process = self.source.process
        if failure is not None:
            # end of input stops the session and writes nothing
            self.source.process = None
            process.communicate()
            return False
        process.stdin.write("stop\n")
        process.stdin.flush()
        if process.stdout.readline().strip() != "stopped":
            raise EnergyError(f"manafa_failed: no answer to stop, see {self.folder / LOG}")
        return False
