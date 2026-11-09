"""The capture, trial and requirements a discovery wrote, known by path and paired by stamp; never the newest in a kept folder."""
import re

from cryptobench import paths
from failure import fail

CAPTURE = re.compile(r"probe_(\d{8}T\d{6}Z)\.yaml")


def _stamp(capture):
    return CAPTURE.fullmatch(capture.name).group(1)


def stamped(directory):
    return {path.name for path in paths.Discovery(directory).captures() if CAPTURE.fullmatch(path.name)}


def pair(capture):
    """The trial written with this capture: the same stamp, never another trial in the folder."""
    trial = paths.Discovery(capture.parent).trial(_stamp(capture))
    if not trial.is_file():
        fail(f"missing_file: {trial} (the trial of {capture.name})")
    return capture, trial


def requirements(capture):
    """The requirements written with this capture; absent only in a folder a test wrote."""
    return paths.Discovery(capture.parent).requirements(_stamp(capture))


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


def reprobed(before, capture):
    """--discovery reuse probes again when no kept capture fits this JVM; ProbeKt prints the new capture without saying so."""
    if capture.name not in before:
        print(f"warning: discovery_reprobed: no capture in {capture.parent} fits this JVM's runtime; --discovery reuse probed again")
