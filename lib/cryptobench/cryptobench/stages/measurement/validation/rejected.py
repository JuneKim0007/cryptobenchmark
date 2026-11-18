"""rejected/<UTC>/[<pass>/]process-<n>/<case>.json with why.yaml: an attempt that failed a rule, kept as evidence; nothing prunes it."""
from cryptobench.shared import paths
from cryptobench.shared.document.document import DocumentKind
from cryptobench.shared.document.dump import dump_yaml
from cryptobench.shared.document.write import write_text
from cryptobench.shared.results.layout import stamped

WHY_DOC = DocumentKind("rejected attempt", 1)


def run_of(unit, into, repetition):
    """The process folder under benchmark/, always ending in process-<n>: the run a finding and a rejected file name."""
    relative = into.relative_to(paths.RunTree(unit).benchmark.root)
    process = paths.PROCESS_FORM.format(repetition)
    return (relative if relative.name == process else relative / process).as_posix()


def moved(unit, result, attempt, findings):
    """The attempt's file, when there is one, renamed under rejected/ beside why.yaml; the folder it went to."""
    into = stamped(paths.RunTree(unit).rejected) / result.run
    into.mkdir(parents=True)
    if result.path.is_file():
        result.path.rename(into / result.path.name)
    why = {"schemaVersion": WHY_DOC.version, "case": result.case, "run": result.run, "attempt": attempt,
           "findings": [finding.document() for finding in findings]}
    write_text(into / paths.WHY, dump_yaml(why))
    return into
