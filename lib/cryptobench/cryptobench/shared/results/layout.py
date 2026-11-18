"""<results root>/<device_id>/: the probe names the folder, so a run stages its discovery beside it until then; an earlier unit moves aside whole."""
import contextlib, datetime, itertools, os, pathlib, shutil, tempfile

from cryptobench.shared import paths
from cryptobench.shared.log.warn import warn

STAGING_PREFIX = ".staging-"
# one run's unit, manifest first; discovery/ joins it when the next run replaces discovery (overwrite)
UNIT = (paths.MANIFEST, paths.CONFIGURATION, paths.PREPARATION, paths.BENCHMARK, paths.ANALYSIS, paths.CHART, paths.CHECK, paths.INTEROP, paths.VALIDATION)
STAMP = "%Y%m%dT%H%M%SZ"


def unit_folder(root, device_id, suite=None):
    """A run's folder: <root>/<device_id>/, or <root>/<device_id>/<suite>/ for a session's suite."""
    return root / device_id / suite if suite else root / device_id


def warn_if_temp(path):
    if paths.in_temp(path):
        warn(f"results_in_temp: {path} is under a temporary folder the system may wipe; keep results elsewhere")


@contextlib.contextmanager
def staged(root):
    root.mkdir(parents=True, exist_ok=True)
    stage = pathlib.Path(tempfile.mkdtemp(prefix=STAGING_PREFIX, dir=root))
    try:
        yield stage
    finally:
        shutil.rmtree(stage, ignore_errors=True)


@contextlib.contextmanager
def kept_until_replaced(folder):
    """The last finished run's folder survives a failed or interrupted one: set aside, restored on failure, dropped on success."""
    previous = folder.parent / f"{folder.name}.previous"
    if previous.exists():
        shutil.rmtree(folder, ignore_errors=True)
        previous.rename(folder)
    if folder.exists():
        folder.rename(previous)
    try:
        yield folder
    except BaseException:
        shutil.rmtree(folder, ignore_errors=True)
        if previous.exists():
            previous.rename(folder)
        raise
    shutil.rmtree(previous, ignore_errors=True)


def replace_folder(source, target):
    if target.exists():
        shutil.rmtree(target)
    source.rename(target)


def merge_folder(source, target):
    shutil.copytree(source, target, dirs_exist_ok=True)


def aside(target):
    return stamped(paths.RunTree(target).superseded)


def stamped(root):
    """A new <root>/<UTC second>[-n]/: mkdir refuses an existing name, so two moves in one second never meet."""
    root.mkdir(exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(STAMP)
    for n in itertools.count(1):
        folder = root / (stamp if n == 1 else f"{stamp}-{n}")
        try:
            folder.mkdir()
            return folder
        except FileExistsError:
            continue


DISCOVERY_MODES = ("overwrite", "keep", "reuse", "verify")
# --discovery modes that clear discovery/ and probe or verify again
REPLACING = ("overwrite", "verify")


def supersede(target, discovery_mode, kept=()):
    """The unit target holds, finished or not, renamed into superseded/<stamp>/ but for the kept paths under it; None when it holds none."""
    names = UNIT + ((paths.DISCOVERY,) if discovery_mode in REPLACING else ())
    present = [name for name in names if (target / name).exists()]
    if not present:
        return None
    into = aside(target)
    for name in present:
        moved(target, into, pathlib.PurePosixPath(name), kept)
    warn(f"run_superseded: {target}: {', '.join(present)} moved to {into}")
    return into


def moved(target, into, relative, kept):
    """relative moves whole unless a kept path is it or lies under it; then everything beside the kept paths moves, by rename only."""
    if relative in kept:
        return
    if not any(path.is_relative_to(relative) for path in kept):
        (into / relative).parent.mkdir(parents=True, exist_ok=True)
        (target / relative).rename(into / relative)
        return
    for child in sorted((target / relative).iterdir()):
        moved(target, into, relative / child.name, kept)


def held_bytes(root):
    total = 0
    for folder, _, files in os.walk(root):
        for name in files:
            with contextlib.suppress(OSError):
                total += os.lstat(os.path.join(folder, name)).st_size
    return total


def report_superseded(target):
    """At a run's end, what superseded/ holds; nothing prunes it."""
    root = paths.RunTree(target).superseded
    if not root.is_dir():
        return
    units = sum(1 for p in root.iterdir() if p.is_dir())
    warn(f"superseded_kept: {root}: {units} earlier {'unit' if units == 1 else 'units'}, {held_bytes(root) / 1e6:.1f} MB; never pruned, remove by hand")


def publish(stage, target, discovery_mode, kept=()):
    """The earlier unit moves aside but for its kept paths, then everything staged moves in; under keep and reuse the staged captures join discovery/."""
    target.mkdir(parents=True, exist_ok=True)
    supersede(target, discovery_mode, kept)
    for folder in stage.iterdir():
        if folder.name == paths.DISCOVERY and (target / folder.name).exists():
            merge_folder(folder, target / folder.name)
        else:
            folder.rename(target / folder.name)


def publish_beside(stage, target, name):
    """Beside a finished run: its capture joins discovery/, the stage's `name` folder replaces the run's, and its configuration and manifest stay."""
    merge_folder(paths.RunTree(stage).discovery.root, paths.RunTree(target).discovery.root)
    replace_folder(stage / name, target / name)

