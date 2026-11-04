"""Planned timed cases the final benchmark.json lacks, whatever lost them: the device, the conversion or the merge."""
import json

import yaml

from energy_stage import capture


def timed(prepared):
    document = yaml.safe_load(prepared.read_text()) or {}
    default = capture(document.get("run"))
    return [case["id"] for case in document.get("cases") or [] if capture(case, default) != "dry"]


def lines(prepared, benchmark):
    measured = {case["id"] for case in json.loads(benchmark.read_text()).get("cases") or []}
    return [f"not_measured: {case}" for case in timed(prepared) if case not in measured]


def report(prepared, benchmark, problems):
    for line in lines(prepared, benchmark):
        print(line)
        problems.append(line)
