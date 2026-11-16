"""<results root>/<device_id>/: the probe names the folder, so a run stages its discovery beside it until then; an earlier unit moves aside whole."""
import contextlib, datetime, itertools, pathlib, shutil, tempfile

from cryptobench.shared import paths

STAGING_PREFIX = ".staging-"
# one run's unit, manifest first; discovery/ joins it when the next run replaces discovery (overwrite)
UNIT = (paths.MANIFEST, paths.CONFIGURATION, paths.PREPARATION, paths.BENCHMARK, paths.ANALYSIS, paths.CHART, paths.CHECK, paths.INTEROP)
STAMP = "%Y%m%dT%H%M%SZ"


def warn_if_temp(path):
    if paths.in_temp(path):
        print(f"warning: results_in_temp: {path} is under a temporary folder the system may wipe; keep results elsewhere")


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
    """A new superseded/<UTC second>[-n]/: mkdir refuses an existing name, so two moves in one second never meet."""
    root = paths.RunTree(target).superseded
    root.mkdir(exist_ok=True)
    stamp = datetime.datetime.now(datetime.timezone.utc).strftime(STAMP)
    for n in itertools.count(1):
        folder = root / (stamp if n == 1 else f"{stamp}-{n}")
        try:
            folder.mkdir()
            return folder
        except FileExistsError:
            continue


def supersede(target, discovery_mode):
    """The unit target holds, finished or not, renamed whole into superseded/<stamp>/; None when it holds none."""
    names = UNIT + ((paths.DISCOVERY,) if discovery_mode == "overwrite" else ())
    present = [name for name in names if (target / name).exists()]
    if not present:
        return None
    into = aside(target)
    for name in present:
        (target / name).rename(into / name)
    print(f"warning: run_superseded: {target}: {', '.join(present)} moved to {into}")
    return into


def publish(stage, target, discovery_mode):
    """The earlier unit moves aside, then everything staged moves in; under keep and reuse the staged captures join discovery/."""
    target.mkdir(parents=True, exist_ok=True)
    supersede(target, discovery_mode)
    for folder in stage.iterdir():
        if folder.name == paths.DISCOVERY and (target / folder.name).exists():
            merge_folder(folder, target / folder.name)
        else:
            folder.rename(target / folder.name)


def publish_beside(stage, target, name):
    """Beside a finished run: its capture joins discovery/, the stage's `name` folder replaces the run's, and its configuration and manifest stay."""
    merge_folder(paths.RunTree(stage).discovery.root, paths.RunTree(target).discovery.root)
    replace_folder(stage / name, target / name)

