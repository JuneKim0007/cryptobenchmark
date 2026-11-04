"""The capture and trial a discovery wrote, known by path: a stamp comes from the device clock, so it never picks the newest."""
import re

from failure import fail

CAPTURE = re.compile(r"probe_(\d{8}T\d{6}Z)\.yaml")
TRIAL = "trial_{}.yaml"


def stamped(directory):
    return {path.name for path in directory.glob("probe_*.yaml") if CAPTURE.fullmatch(path.name)}


def pair(capture):
    """The trial written with this capture: the same stamp, never another trial in the folder."""
    trial = capture.with_name(TRIAL.format(CAPTURE.fullmatch(capture.name).group(1)))
    if not trial.is_file():
        fail(f"missing_file: {trial} (the trial of {capture.name})")
    return capture, trial


def added(directory, before):
    """The one capture a device probe added to directory beside those already there."""
    new = sorted(stamped(directory) - before)
    if len(new) != 1:
        fail(f"missing_file: {directory}/probe_<stamp>.yaml (the probe added {len(new)} captures, expected 1: {new})")
    return pair(directory / new[0])


def printed(lines, directory):
    """The capture ProbeKt names on stdout, written or reused."""
    names = [line for line in lines if CAPTURE.fullmatch(line.rsplit("/", 1)[-1])]
    if len(names) != 1:
        fail(f"missing_file: {directory}/probe_<stamp>.yaml (ProbeKt named {len(names)} captures)")
    return pair(directory / names[0].rsplit("/", 1)[-1])
