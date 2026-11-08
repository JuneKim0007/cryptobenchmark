"""Select's message and the evidence digest it is decided on: members that stay, links, shared source, measured lines,
run warnings, unknown input size."""
import dataclasses

from select_data import dossier, item, linked

from perfrepair.ai.select.render import render
from perfrepair.ai.select.unit_candidates import unit_candidates
from perfrepair.ai.select.units import evidence
from perfrepair.dto.dossier import Estimate, Option
from perfrepair.dto.perf_mode import GENERIC_MODE, PerfMode
from perfrepair.dto.primitives import PrimitiveLine, PrimitivesTable
from perfrepair.dto.unit import PairInterop, Stay, UnitDossiers
from perfrepair.dto.units import DisplayUnits

A = dossier()
C = dossier(file="src/Pair.kt", options=(Option("R1", "TypeA|ALG-A/MODE-X|P3", {}, "pass", (Estimate("timeNs", 0.8, 0.99, 40, "OP1 key 128 input 1024"),)),),
            sinks=("local",), key_source="derived")


def test_the_message_lists_the_members_that_stay_and_each_inverse_pairs_interop():
    lone = dossier(file="src/Lone.kt", options=())
    pair = PairInterop("TypeA|ALG-A/MODE-X|P1", "TypeA|ALG-A/MODE-X|P2", "pass")
    u = UnitDossiers(linked(A, lone), (A,), (Stay(lone.key, lone.current, "no_alternative"),), (pair,))
    text = render(u)
    for part in ("UNIT of 2 members: S1, S2", "STAYS (no option; these members keep what they use)",
                 "  S2: current TypeA|ALG-A/MODE-X|P1 | reason no_alternative", "    S1 R1 with S2 current: interop pass",
                 "    every other choice: interop not_planned"):
        assert part in text, part
    assert "MEMBER S2" not in text and "MEMBER S1" in text


def test_a_unit_is_one_message_showing_every_member_and_its_links():
    u = UnitDossiers(linked(A, C), (A, C))
    text = render(u, candidates=unit_candidates(u, GENERIC_MODE, "drop-in"))
    for part in ("UNIT of 2 members: S1, S2", "S1 inverse S2 (key): lines 3, 20 | lines 3, 21", "MEMBER S1", "MEMBER S2",
                 "src/Box.kt", "src/Pair.kt"):
        assert part in text, part
    assert text.count("CANDIDATES") == 1


def test_same_function_source_is_shown_once_in_a_unit():
    same = dossier(line=12, call="Engine.other")
    text = render(UnitDossiers(linked(A, same), (A, same)))
    assert "FUNCTION SOURCE: as S1" in text and text.count(" BEGIN") == 1


def _table():
    def line(provider, ns, op="OP1", key=128):
        return PrimitiveLine("TypeA", "ALG-A/MODE-X", provider, op, key, "WARM", "notFixed", "accepted",
                             {"timeNs@64": ns, "timeNs@-": None, "energyJ@64": 0.5}, {"timeNs": 40, "energyJ": 1},
                             {"timeNs": 0.01, "energyJ": 0.2})
    lines = (line("P1", 662.0), line("P2", 400.0), line("P2", 1.0, op="OP2"), line("P3", 500.0, key=256), line("P9", 1.0))
    return PrimitivesTable(("timeNs@64", "timeNs@-", "energyJ@64"), ("timeNs", "energyJ"), lines)


def test_the_message_shows_the_current_and_option_lines_in_the_display_units_of_the_selected_metrics_only():
    perf = PerfMode(("latency", "throughput"))
    text = render(item(A), perf, _table(), DisplayUnits())
    measured = text.split("MEASURED", 1)[1].split("FUNCTION SOURCE", 1)[0]
    assert "latency ms/op, throughput MB/s" in measured and "latency@64 | throughput@64 | timeNs n | timeNs cv" in measured
    assert "  current | OP1 | 128 | WARM | accepted | 0.000662 | 96.68 | 40 | 0.010" in measured
    assert "  R1 | OP1 | 128 | WARM | accepted | 0.0004 | 160 | 40 | 0.010" in measured
    assert "OP2" not in measured and "P9" not in measured and "R2" not in measured and "energyJ" not in measured


def test_a_changed_primitives_line_is_new_evidence_but_a_display_unit_is_not():
    table = _table()
    moved = PrimitivesTable(table.columns, table.metrics, (dataclasses.replace(table.lines[0], medians={"timeNs@64": 1.0}),) + table.lines[1:])
    u = item(A)
    assert evidence(u, GENERIC_MODE, table) != evidence(u, GENERIC_MODE, moved)
    shown = [render(u, GENERIC_MODE, table, units) for units in (DisplayUnits(), DisplayUnits("ns"))]
    assert shown[0] != shown[1]


def test_a_changed_link_is_new_evidence():
    u = UnitDossiers(linked(A, C), (A, C))
    moved = dataclasses.replace(u.unit, links=(dataclasses.replace(u.unit.links[0], kind="shared_key", via="field"),))
    assert evidence(u, GENERIC_MODE) != evidence(dataclasses.replace(u, unit=moved), GENERIC_MODE)


def test_the_run_warnings_reach_the_message_and_its_evidence():
    text = render(item(A), warnings=("cpu_not_locked: clocks float",))
    assert text.startswith("RUN WARNINGS:\n  - cpu_not_locked: clocks float\n\nPERFMODE generic | rule overall")
    assert evidence(item(A), GENERIC_MODE, warnings=("cpu_not_locked: clocks float",)) != evidence(item(A), GENERIC_MODE)


def test_a_site_of_unknown_input_size_is_not_said_to_have_a_nearest_configuration():
    unknown = dataclasses.replace(A, scope=dataclasses.replace(A.scope, inputSize=None))
    text = render(item(unknown))
    assert "nearest" not in text and "every measured input size (this site's is unknown)" in text
