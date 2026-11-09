"""Package of apps/cli/facade.py: the settings index, the tree check, the phases. Puts the benchmark runner and perfrepair on the path,
as all run here."""
import sys

try:
    from cryptobench import paths
except ModuleNotFoundError:
    sys.exit("facade: missing_dependency: cryptobench; pip install -r requirements.txt")

paths.add_app_imports()
