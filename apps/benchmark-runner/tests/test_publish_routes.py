"""What --interop and --check publish through publish_unit, beside a finished run and into a new folder, on the host and the fake phone;
the tree, the manifest and the route's stdout against golden/publish_*.txt. UPDATE_GOLDEN=1 rewrites them."""
import os, pathlib, re

import pytest
import yaml

from cryptobench.shared import paths
from cryptobench.stages.verification import check, interop_oracle
from fake_phone import Phone
from test_rerun_safety import CHECKED, Rerun, written

GOLDEN = pathlib.Path(__file__).with_name("golden")
STAMP = re.compile(r"\d{8}T\d{6}Z")
INTEROP = yaml.safe_dump({"pairs": [{"id": "p1", "group": "g", "result": "pass", "reason": ""},
                                    {"id": "p2", "group": "g", "result": "fail", "reason": "bytes differ"}]})
HOST = {"device": False, "bench": True}


class RoutePhone(Phone):
    """The fake phone that also answers EndToEndCheck and InteropCheck with their result files."""

    def instrument(self, test_class, *arguments, step="instrument"):
        if test_class == "InteropCheck":
            self.log.append("instrument InteropCheck")
            return "OK (1 test)\n"
        return super().instrument(test_class, *arguments, step=step)

    def pull(self, remote, local):
        for name, text in ((paths.CHECK_RESULT, CHECKED), (paths.INTEROP_RESULT, INTEROP)):
            if remote.endswith(f"/{name}"):
                self.log.append(f"pull {name}")
                return written(pathlib.Path(local), text)
        return super().pull(remote, local)


def routed(tmp_path, monkeypatch):
    rerun = Rerun(tmp_path, monkeypatch, RoutePhone(tmp_path))
    monkeypatch.setattr(check.answers, "write_known_answers", lambda effective, *_rest: written(paths.Configuration.holding(effective).known_answers, "{}"))
    monkeypatch.setattr(check, "on_host", lambda _o, _e, _c, _t, _k, into: written(paths.CheckFolder(into).result, CHECKED))
    monkeypatch.setattr(interop_oracle, "on_host", lambda _e, _c, _t, _p, out, *_rest: written(out, INTEROP))
    rerun.plan = written(tmp_path / "plan.yaml", "pairs: []\n")
    return rerun


def snapshot(rerun, tmp_path, out):
    root = rerun.root
    tree = sorted(p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file())
    document = yaml.safe_load(paths.RunTree(rerun.device).manifest.read_text())
    document["operations"] = "<engine operations>"
    if "run" in document:
        document["run"].update(commit="<commit>", clean="<clean>", code="<code digests>")
    said = [line for line in out.splitlines() if line.startswith(("results:", "wrote:", "interop:", "check:"))]
    text = "tree:\n" + "".join(f"  {p}\n" for p in tree) + "manifest:\n" + yaml.safe_dump(document, sort_keys=False) + "stdout:\n" + "".join(f"  {s}\n" for s in said)
    return STAMP.sub("<stamp>", text.replace(str(tmp_path), "<tmp>"))


def matches(name, text):
    golden = GOLDEN / f"publish_{name}.txt"
    if os.environ.get("UPDATE_GOLDEN"):
        golden.write_text(text)
    assert text == golden.read_text()


def interop_device_new(rerun):
    rerun(interop=str(rerun.plan))


def interop_device_beside(rerun):
    rerun()
    rerun(interop=str(rerun.plan))


def interop_host_new(rerun):
    rerun(interop=str(rerun.plan), **HOST)


def interop_host_beside(rerun):
    rerun(probe=True, **HOST)
    rerun(interop=str(rerun.plan), **HOST)


def check_device_new(rerun):
    rerun(check=True)


def check_device_beside(rerun):
    rerun()
    rerun(check=True)


def check_host_new(rerun):
    rerun(check=True, **HOST)


def check_host_beside(rerun):
    rerun(probe=True, **HOST)
    rerun(check=True, **HOST)


ROUTES = {f.__name__: f for f in (interop_device_new, interop_device_beside, interop_host_new, interop_host_beside,
                                  check_device_new, check_device_beside, check_host_new, check_host_beside)}


@pytest.mark.parametrize("name", ROUTES)
def test_publish_tree_manifest_and_stdout(name, tmp_path, monkeypatch, capsys):
    rerun = routed(tmp_path, monkeypatch)
    ROUTES[name](rerun)
    matches(name, snapshot(rerun, tmp_path, capsys.readouterr().out))


def test_interop_and_check_beside_a_finished_run_keep_their_configuration(tmp_path, monkeypatch):
    rerun = routed(tmp_path, monkeypatch)
    rerun()
    rerun(interop=str(rerun.plan))
    tree = paths.RunTree(rerun.device)
    assert tree.interop.configuration.effective.is_file()
    rerun(check=True)
    assert tree.check.configuration.effective.is_file()


def test_interop_and_check_print_one_results_line(tmp_path, monkeypatch, capsys):
    rerun = routed(tmp_path, monkeypatch)
    rerun(interop=str(rerun.plan))
    assert [line for line in capsys.readouterr().out.splitlines() if line.startswith("results:")] == [f"results:   {rerun.device}"]
    rerun(check=True)
    assert [line for line in capsys.readouterr().out.splitlines() if line.startswith("results:")] == [f"results:   {rerun.device}"]


def test_interop_into_a_new_folder_writes_no_guide(tmp_path, monkeypatch):
    rerun = routed(tmp_path, monkeypatch)
    rerun(interop=str(rerun.plan))
    files = yaml.safe_load(paths.RunTree(rerun.device).manifest.read_text())["files"]
    assert "guide" not in files and {"interop", "interopPlan"} <= set(files)
