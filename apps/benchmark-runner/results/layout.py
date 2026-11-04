"""<results root>/<device_id>/: the probe names the folder, so a run stages its discovery beside it until then."""
import contextlib, os, pathlib, shutil, tempfile

MANIFEST = "manifest.yaml"
DISCOVERY, INTEROP = "discovery", "interop"
STAGING_PREFIX = ".staging-"
TEMP_ROOTS = ("/tmp", "/var/tmp", "/var/folders")


def in_temp(path):
    real = pathlib.Path(path).resolve()
    return any(real.is_relative_to(pathlib.Path(root).resolve()) for root in (*TEMP_ROOTS, tempfile.gettempdir()))


def warn_if_temp(path):
    if in_temp(path):
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
    previous = folder.with_name(folder.name + ".previous")
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


def write_atomic(path, text):
    """The manifest marks a finished run, so a reader sees the old file or the whole new one, never half of one."""
    handle, temporary = tempfile.mkstemp(prefix=f".{path.name}.", dir=path.parent)
    try:
        with os.fdopen(handle, "w") as out:
            out.write(text)
            out.flush()
            os.fsync(out.fileno())
        os.replace(temporary, path)
    except BaseException:
        pathlib.Path(temporary).unlink(missing_ok=True)
        raise


def replace_folder(source, target):
    if target.exists():
        shutil.rmtree(target)
    source.rename(target)


def merge_folder(source, target):
    shutil.copytree(source, target, dirs_exist_ok=True)


def publish(stage, target, discovery_mode):
    """Everything staged moves in; the old manifest goes first, because a folder with one is a finished run."""
    target.mkdir(parents=True, exist_ok=True)
    (target / MANIFEST).unlink(missing_ok=True)
    for folder in stage.iterdir():
        if folder.name == DISCOVERY and discovery_mode != "overwrite":
            merge_folder(folder, target / DISCOVERY)
        else:
            replace_folder(folder, target / folder.name)


def publish_interop(stage, target):
    """Beside a finished run: its capture joins discovery/, and its configuration and manifest stay what they were."""
    merge_folder(stage / DISCOVERY, target / DISCOVERY)
    replace_folder(stage / INTEROP, target / INTEROP)

