"""The facade turns SIGTERM into Ctrl-C and runs its guide child in a session of its own; a SIGTERM to the
facade stops the child's group, then the facade ends as on Ctrl-C."""
import os, pathlib, signal, subprocess, sys, textwrap, time

ROOT = pathlib.Path(__file__).resolve().parents[3]
FACADE = textwrap.dedent("""
    import pathlib, sys, types
    from cryptobench.shared.stop.child import stop_like_ctrl_c
    from facade import phases
    stop_like_ctrl_c()
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


def test_a_sigterm_to_the_facade_stops_its_guide_child(tmp_path):
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
        assert child and os.getpgid(child) == child != os.getpgid(facade.pid)
        facade.send_signal(signal.SIGTERM)
        assert facade.wait(10) == -signal.SIGINT
        assert not alive(child)
    finally:
        for group in {facade.pid, child} - {None}:
            try:
                os.killpg(group, signal.SIGKILL)
            except ProcessLookupError:
                pass
        facade.wait(10)
