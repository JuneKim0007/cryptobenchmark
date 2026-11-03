"""How the host runs tools/energy: the interpreter that has its packages, and the arguments of a run's cases."""
import dataclasses, os, pathlib, subprocess

TOOLS = pathlib.Path(__file__).resolve().parent.parent


class EnergyError(Exception):
    pass


@dataclasses.dataclass(frozen=True)
class Host:
    python: str
    stacktrace: bool = False
    platform_tools: pathlib.Path | None = None

    def tool(self, script, *arguments):
        """Runs in tools/energy's own venv: it needs perfetto, which the host pipeline does not."""
        result = subprocess.run([self.python, str(TOOLS / script), *map(str, arguments)], capture_output=True, text=True)
        if result.returncode != 0:
            if "No module named" in result.stderr:
                raise EnergyError(f"missing_module: {result.stderr.strip().splitlines()[-1]}; "
                                  f"pip install -r tools/energy/requirements.txt into {self.python}, or pass --energy-python")
            if self.stacktrace:
                print(result.stdout + result.stderr)
            raise EnergyError(f"tools/energy/{script}: {(result.stderr or result.stdout).strip().splitlines()[-1]}")
        print(result.stdout.rstrip())

    def adb_environment(self):
        """A tool that calls a bare adb finds the one the pipeline uses."""
        path = os.environ.get("PATH", "")
        return os.environ | ({"PATH": f"{self.platform_tools}{os.pathsep}{path}"} if self.platform_tools else {})


def case_arguments(captures_found, capability, preparation, data, traces, dry_calls, out):
    arguments = ["--capability", capability, "-o", out]
    if "measured" in captures_found:
        arguments += ["--prepared", preparation / "prepared.yaml", "--benchmark-data", data, "--traces", traces]
    if "dry" in captures_found:
        arguments += ["--dry-trace", traces / "dry.pftrace", "--dry-calls", dry_calls]
    return arguments
