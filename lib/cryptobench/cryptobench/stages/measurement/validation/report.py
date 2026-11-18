"""validation.yaml: per run the last check_run result, written at every block end and by a restart's content check."""
from cryptobench.shared import paths
from cryptobench.shared.document.document import DocumentKind, read_yaml
from cryptobench.shared.document.dump import dump_yaml
from cryptobench.shared.document.write import write_text
from cryptobench.stages.measurement.validation import rules

VALIDATION_DOC = DocumentKind("validation", 1)
BLOCK_END, RESTART = "block_end", "restart"


def written(unit, by, findings):
    """findings: {run: [Finding]}; each run's entry replaced, the others kept; a file of another schema is replaced whole."""
    path = paths.RunTree(unit).validation
    document = read_yaml(path) if path.is_file() else {}
    runs = (document.get("runs") or {}) if VALIDATION_DOC.accepts(document.get("schemaVersion")) else {}
    for run, found in findings.items():
        runs[run] = {"checkedBy": by, "fails": len(rules.failed(found)), "findings": [finding.document() for finding in found]}
    write_text(path, dump_yaml({"schemaVersion": VALIDATION_DOC.version, "runs": dict(sorted(runs.items()))}))


def checker(unit, pass_folder, expectation):
    """blocks.Blocks.check: a just recorded run's findings, as its record entry holds them, also written to validation.yaml."""
    def check(entry):
        run = rules.RunFolder(unit, pass_folder / entry["folder"], pass_folder, entry["repetition"], tuple(entry["problems"]), entry["files"])
        found = rules.check_run(run, expectation)
        written(unit, BLOCK_END, {run.run: found})
        return [finding.document() for finding in found]
    return check
