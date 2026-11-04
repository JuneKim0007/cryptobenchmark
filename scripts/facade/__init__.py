"""Package of scripts/facade.py: the settings index, the tree check, the phases. Puts perfrepair on the path, as its parsers run here."""
import sys

from repo import ROOT

SOURCE = ROOT / "perf-repair" / "src"
sys.path.insert(0, str(SOURCE))
