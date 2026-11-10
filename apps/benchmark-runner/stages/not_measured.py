"""Planned timed cases the final benchmark.json lacks, whatever lost them: the device, the conversion or the merge."""
import json


from energy_stage import capture
from cryptobench.document import read_yaml


def timed(prepared):
    document = read_yaml(prepared)
    default = capture(document.get("run"))
    return [case["id"] for case in document.get("cases") or [] if capture(case, default) != "dry"]


def lines(prepared, benchmark):
    measured = {case["id"] for case in json.loads(benchmark.read_text()).get("cases") or []}
    return [f"not_measured: {case}" for case in timed(prepared) if case not in measured]


def report(prepared, benchmark, problems):
    for line in lines(prepared, benchmark):
        print(line)
        problems.append(line)
