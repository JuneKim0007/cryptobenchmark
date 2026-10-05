"""Reading effective.yaml the way a run needs it: the settings, with what the run noticed joined back from report.yaml."""
import pathlib

import yaml

from failure import fail


def read(effective_file):
    effective = pathlib.Path(effective_file)
    document = yaml.safe_load(effective.read_text()) or {}
    report_file = effective.parent / "report.yaml"
    report = (yaml.safe_load(report_file.read_text()) or {}) if report_file.is_file() else {}
    return {
        "document": document,
        # older effective files carry these inline
        "warnings": (report.get("warnings") or []) + (document.get("warnings") or []),
        "skipped": (report.get("skipped") or []) + (document.get("skipped") or []),
    }


def entry_count(document):
    return sum(len(names) for types in (document.get("providers") or {}).values() for names in types.values())


def process_repetitions(document):
    repetitions = (document.get("run") or {}).get("processRepetitions", 1)
    if not isinstance(repetitions, int) or repetitions < 1:
        fail(f"not_positive: processRepetitions {repetitions}")
    return repetitions
