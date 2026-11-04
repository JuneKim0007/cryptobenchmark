"""#78 flow 7: one run per device folder (the lock), and two writers of one file never take each other's temp file."""
import os
import subprocess
import sys
import threading
from pathlib import Path

import pytest

from perfrepair.dto.coded import InputError
from perfrepair.files import TEMP_SUFFIX, read_json, write_json
from perfrepair.run_dir import LOCK
from perfrepair.run_dir.lock import DeviceLock

SRC = Path(__file__).parents[1] / "src"
HOLD = "import sys; from perfrepair.run_dir.lock import DeviceLock; DeviceLock.take(sys.argv[1]); print('held', flush=True); sys.stdin.read()"


@pytest.fixture
def held(tmp_path):
    """Another process holding the folder's lock until the test ends."""
    folder = tmp_path / "dev"
    p = subprocess.Popen([sys.executable, "-c", HOLD, str(folder)], stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
                         env={**os.environ, "PYTHONPATH": str(SRC)})
    assert p.stdout.readline().strip() == "held"
    yield folder, p.pid
    p.stdin.close()
    p.wait(10)


def test_a_second_process_is_device_busy_naming_the_holder(held):
    folder, pid = held
    with pytest.raises(InputError, match=rf"^device_busy: {folder} is in use by another run \(pid {pid}\)"):
        DeviceLock.take(folder)


def test_the_holder_may_take_it_again_and_it_frees_on_the_last_release(tmp_path):
    outer = DeviceLock.take(tmp_path)
    inner = DeviceLock.take(tmp_path)
    inner.release()
    inner.release()
    probe = [sys.executable, "-c", "import sys; from perfrepair.run_dir.lock import DeviceLock; DeviceLock.take(sys.argv[1])",
             str(tmp_path)]
    env = {**os.environ, "PYTHONPATH": str(SRC)}
    assert subprocess.run(probe, env=env, capture_output=True).returncode == 1
    outer.release()
    assert subprocess.run(probe, env=env).returncode == 0
    assert (tmp_path / LOCK).read_text() != str(os.getpid())


def test_two_writers_of_one_file_never_fail_and_leave_no_temp_file(tmp_path):
    """The probe's race: a shared `<name>.tmp` failed 50-80% of writes with FileNotFoundError."""
    target, errors = tmp_path / "finished.json", []

    def writer(tag):
        for _ in range(300):
            try:
                write_json(target, {"writer": tag, "pad": "x" * 2000})
            except OSError as e:
                errors.append(e)
    threads = [threading.Thread(target=writer, args=(t,)) for t in "AB"]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert errors == [] and read_json(target)["writer"] in "AB"
    assert not list(tmp_path.glob("*" + TEMP_SUFFIX))
    assert oct(target.stat().st_mode & 0o777) == oct(0o666 & ~_umask())


def _umask():
    mask = os.umask(0)
    os.umask(mask)
    return mask
