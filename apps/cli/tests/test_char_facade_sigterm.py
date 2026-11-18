"""Characterization (Py-P6): the facade installs no SIGTERM handler and runs its guide child in its own process group; a SIGTERM to the facade
ends it and leaves the child running."""
import os, pathlib, signal, subprocess, sys, textwrap, time

ROOT = pathlib.Path(__file__).resolve().parents[3]
FACADE = textwrap.dedent("""
    import pathlib, sys, types
    from facade import phases
    folder = pathlib.Path(sys.argv[1])
    phases.sys = types.SimpleNamespace(executable=str(folder / "guide"))
    index = types.SimpleNamespace(llm_config=folder / "l.yaml", crypto_config=folder / "c.yaml", harness_config=None, run_id=None,
                                  results=folder / "results", on_existing="resume")
    phases.run_phases(index, {}, root=folder, echo=print)
""")
GUIDE = "#!/bin/sh\necho $$ > \"$(dirname \"$0\")/child.pid\"\nexec sleep 60\n"


def alive(pid):
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False


def test_today_a_sigterm_to_the_facade_orphans_its_guide_child(tmp_path):
    guide = tmp_path / "guide"
    guide.write_text(GUIDE)
    guide.chmod(0o755)
    env = {**os.environ, "PYTHONPATH": os.pathsep.join(str(ROOT / p) for p in ("apps/cli", "lib/cryptobench", "apps/perf-repair/src"))}
    facade = subprocess.Popen([sys.executable, "-c", FACADE, str(tmp_path)], env=env, start_new_session=True)
    child = None
    try:
        for _ in range(200):
            if (tmp_path / "child.pid").is_file() and (tmp_path / "child.pid").read_text().strip():
                child = int((tmp_path / "child.pid").read_text())
                break
            time.sleep(0.05)
        assert child and os.getpgid(child) == os.getpgid(facade.pid)
        facade.send_signal(signal.SIGTERM)
        assert facade.wait(10) == -signal.SIGTERM
        time.sleep(0.2)
        assert alive(child)
    finally:
        try:
            os.killpg(facade.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        facade.wait(10)
