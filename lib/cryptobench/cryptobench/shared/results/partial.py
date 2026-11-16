"""A run that stopped before its end: its manifest marked partial, with the case runs each process folder holds."""
import contextlib

from cryptobench.shared import paths
from cryptobench.shared.errors.line import one_line


def done(benchmark):
    """{process folder: case files} under benchmark/, the cases measured and the case runs behind them."""
    folders = {p.parent.relative_to(benchmark).as_posix() or ".": sorted(f.stem for f in p.glob("*.json")) for p in sorted(benchmark.rglob(paths.CASES)) if p.is_dir()}
    return {"caseRuns": sum(len(cases) for cases in folders.values()), "cases": len({c for cases in folders.values() for c in cases}),
            "processes": {folder: len(cases) for folder, cases in folders.items()}}


def reason(error):
    return "interrupted" if isinstance(error, KeyboardInterrupt) else f"{type(error).__name__}: {one_line(error)}"


@contextlib.contextmanager
def kept(results, write):
    """write(partial, pulled) records the manifest of a measure that raised; the error still ends the run, a failed write only warns."""
    try:
        yield
    except BaseException as error:
        tree = paths.RunTree(results)
        record = {"reason": reason(error), **done(tree.benchmark.root)}
        prepared = tree.preparation
        try:
            write(record, {key: path for key, path in (("prepared", prepared.prepared), ("skipped", prepared.skipped)) if path.is_file()})
        except Exception as failed:
            print(f"warning: partial_manifest_failed: {type(failed).__name__}: {one_line(failed)}")
        raise
