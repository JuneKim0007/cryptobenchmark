"""usage: manafa_session.py [--check <seconds> --capability <energy.yaml>]

One process holds one EManafa from start to stop: a second one's init kills the session's perfetto.
stdin: `stop`, then one JSON list of energy.py's arguments; end of input stops and writes nothing.
"""
import contextlib, json, pathlib, sys, time

import yaml

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
import energy, manafa_estimate as estimate  # noqa: E402

REQUIREMENTS = "tools/energy/requirements-manafa.txt"


class CannotStart(Exception):
    pass


def quiet():
    """manafa prints as it goes; stdout carries this process's answers."""
    return contextlib.redirect_stdout(sys.stderr)


def load():
    try:
        import manafa
        from manafa.emanafa import EManafa
    except ImportError as error:
        raise CannotStart(f"manafa_missing: {estimate.one_line(error)}; pip install -r {REQUIREMENTS} into {sys.executable}, "
                          "or pass --energy-python") from error
    return pathlib.Path(manafa.__file__).parent, EManafa


def started():
    package, EManafa = load()
    try:
        with quiet():
            # 0.4.14 ships no results folder and its services make only the level below it
            (package / "results").mkdir(exist_ok=True)
            em = EManafa()
            # auto picks rails where they exist, then parses no cpu frequency: the estimate would read one stale sample
            em.profiler_mode = "legacy"
            em.init()
            em.start()
    except Exception as error:
        raise CannotStart(f"manafa_cannot_start: {estimate.one_line(error)}") from error
    return em


def stopped(em):
    """The reason every case is not_measured, or None."""
    try:
        with quiet():
            em.stop()
    except Exception as error:
        with quiet():
            if em.unplugged:
                em.plug_back()
        return f"manafa_stop_failed: {estimate.one_line(error)}"
    return None


def profile_of(em):
    return pathlib.Path(em.power_profile).name


def check(seconds, capability):
    base = {"schemaVersion": 1, "source": estimate.SOURCE, "kind": estimate.KIND}
    out = pathlib.Path(capability)
    try:
        em = started()
    except CannotStart as error:
        out.write_text(yaml.safe_dump(base | {"started": False, "reason": str(error)}, sort_keys=False))
        raise
    time.sleep(seconds)
    reading, reason = estimate.probe(em, stopped(em))
    document = base | {"started": True, "usable": reason is None, "reason": reason, "windowSeconds": seconds,
                       "powerProfile": profile_of(em)} | reading
    out.write_text(yaml.safe_dump(document, sort_keys=False))
    if reason:
        raise CannotStart(f"manafa_cannot_start: {reason}")
    print(f"manafa:    started, {reading['cpuFrequencyEvents']} cpu frequency events, {reading['batteryStatsEvents']} batterystats "
          f"events, estimated {reading['joules']:.3f} J over {seconds} s, profile {profile_of(em)}")


def write_energy(em, failure, request):
    from rails.trace import Trace
    a = energy.parser().parse_args(request)

    def measure(_rails, start, end, _idle, operations):
        return estimate.case(em, failure, start, end, operations)

    cases = {c: estimate.judge(r) for c, r in energy.read_cases(a, None, Trace, measure).items()}
    document = {"schemaVersion": energy.SCHEMA_VERSION, "source": estimate.SOURCE, "kind": estimate.KIND,
                "powerProfile": profile_of(em), "cases": cases}
    pathlib.Path(a.out).write_text(json.dumps(document, indent=1))
    energy.report_cases(cases)


def session():
    em = started()
    print("started", flush=True)
    sys.stdin.readline()
    failure = stopped(em)
    print("stopped", flush=True)
    request = sys.stdin.readline()
    if request:
        write_energy(em, failure, json.loads(request))


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    try:
        if argv:
            check(float(argv[1]), argv[3])
        else:
            session()
    except CannotStart as error:
        print(error)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
