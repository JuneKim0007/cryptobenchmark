"""An energy source's packages, installed on first use into one venv per source and requirements digest under the user cache."""
import hashlib
import shutil
import subprocess
import sys

from cryptobench.shared import paths
from cryptobench.stages.measurement.energy.sources import SOURCES

COMPLETE = ".complete"


class InstallFailed(Exception):
    pass


def cache_root():
    return paths.user_cache() / "energy"


def files(source_name):
    return [paths.repo().energy / name for name in SOURCES[source_name].REQUIREMENTS]


def venv(source_name):
    digest = hashlib.sha256(b"".join(f.read_bytes() for f in files(source_name))).hexdigest()[:12]
    return cache_root() / f"{source_name}-{digest}"


def python_of(folder):
    return folder / "bin" / "python"


def installed(source_name, run=subprocess.run):
    """The venv's python, built when absent or left half-built; raises InstallFailed with pip's last line."""
    folder = venv(source_name)
    if (folder / COMPLETE).is_file():
        return str(python_of(folder))
    building = folder.parent / f"{folder.name}.building"
    shutil.rmtree(building, ignore_errors=True)
    print(f"energy:    installing {source_name} packages into {folder}")
    steps = [[sys.executable, "-m", "venv", str(building)],
             [str(python_of(building)), "-m", "pip", "install", "-q", *[a for f in files(source_name) for a in ("-r", str(f))]]]
    for step in steps:
        result = run(step, capture_output=True, text=True)
        if result.returncode != 0:
            shutil.rmtree(building, ignore_errors=True)
            lines = (result.stderr or result.stdout).strip().splitlines()
            raise InstallFailed(f"energy_install_failed: {source_name}: {lines[-1] if lines else f'exit {result.returncode}'}")
    (building / COMPLETE).write_text("")
    shutil.rmtree(folder, ignore_errors=True)
    building.rename(folder)
    return str(python_of(folder))
