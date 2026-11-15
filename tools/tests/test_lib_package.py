"""A wheel built from lib/cryptobench ships the glossary codes.yaml beside its loader, and no tests/ folder."""
import pathlib
import shutil
import subprocess
import sys
import zipfile

LIB = pathlib.Path(__file__).resolve().parents[2] / "lib/cryptobench"


def test_the_built_wheel_holds_the_glossary(tmp_path):
    source = tmp_path / "source"
    shutil.copytree(LIB, source, ignore=shutil.ignore_patterns("__pycache__", "build", "*.egg-info"))
    subprocess.run([sys.executable, "-m", "pip", "wheel", "--no-deps", "-q", "-w", tmp_path / "dist", source], check=True)
    [wheel] = (tmp_path / "dist").glob("*.whl")
    names = zipfile.ZipFile(wheel).namelist()
    assert {"cryptobench/shared/errors/codes.yaml", "cryptobench/shared/errors/glossary.py"} <= set(names)
    assert not [name for name in names if "/tests/" in name]
