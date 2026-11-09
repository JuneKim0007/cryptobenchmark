"""How the host runs apps/benchmark-runner/energy: the interpreter that has its packages, and the arguments of a run's cases."""
import dataclasses, os, pathlib, subprocess
from cryptobench import paths

TOOLS = paths.repo().energy


class EnergyError(Exception):
    pass


@dataclasses.dataclass(frozen=True)
class Host:
    python: str
    stacktrace: bool = False
    platform_tools: pathlib.Path | None = None
    timeout: float | None = None

    def expired(self, what):
        return EnergyError(f"timeout: {what} ran past {self.timeout} s")

    def tool(self, script, *arguments):
        """Runs in apps/benchmark-runner/energy's own venv: it needs perfetto, which the host pipeline does not."""
        try:
            result = subprocess.run([self.python, str(TOOLS / script), *map(str, arguments)], capture_output=True, text=True,
                                    timeout=self.timeout)
        except subprocess.TimeoutExpired:
            raise self.expired(f"apps/benchmark-runner/energy/{script}") from None
        if result.returncode != 0:
            if "No module named" in result.stderr:
                raise EnergyError(f"missing_module: {result.stderr.strip().splitlines()[-1]}; "
                                  f"pip install -r apps/benchmark-runner/energy/requirements.txt into {self.python}, or pass --energy-python")
            if self.stacktrace:
                print(result.stdout + result.stderr)
            raise EnergyError(f"apps/benchmark-runner/energy/{script}: {(result.stderr or result.stdout).strip().splitlines()[-1]}")
        print(result.stdout.rstrip())

    def adb_environment(self):
        """A tool that calls a bare adb finds the one the pipeline uses."""
        path = os.environ.get("PATH", "")
        return os.environ | ({"PATH": f"{self.platform_tools}{os.pathsep}{path}"} if self.platform_tools else {})


def case_arguments(captures_found, capability, preparation, data, traces, dry_calls, out):
    arguments = ["--capability", capability, "-o", out]
    if "measured" in captures_found:
        arguments += ["--prepared", paths.Preparation(preparation).prepared, "--benchmark-data", data, "--traces", traces]
    if "dry" in captures_found:
        arguments += ["--dry-trace", traces / paths.DRY_TRACE, "--dry-calls", dry_calls]
    return arguments
