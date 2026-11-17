"""A session's plan before anything runs: the devices adb lists, the targets resolved and grouped, each skip and notice as one line."""
from cryptobench.shared import paths
from cryptobench.shared.device import aliases, probe
from cryptobench.shared.device.adb import Device
from cryptobench.shared.log.warn import warn
from cryptobench.shared.session import document, targets


def resolved(session_file, config):
    """The session and its targets; config() is the run's global.yaml chain for a target naming none."""
    session = document.parse(session_file)
    adb = Device(paths.repo().gradle_root, False, False)
    adb.require_adb()
    rows = probe.enumerate_devices(adb.raw)
    known = aliases.read(paths.user_devices())
    return session, rows, known, targets.resolve(session, rows, known, config)


def lines(session, plan, results):
    out = [f"session:   {session.name} ({session.path})"]
    for target in sorted(plan.targets, key=lambda t: t.order):
        device = "host" if target.transport is None else f"{target.key}, adb {target.transport}"
        suites = ", ".join(s.stem for s in target.suites)
        out.append(f"order {target.order}:   {target.name} ({device}): {suites} -> {results}/<device_id>/<suite>/")
    return out


def notices(plan):
    """What resolve noticed, then one parallel_unavailable per group of several targets: groups run their targets one after another."""
    parallel = [f"parallel_unavailable: order {group[0].order} has {len(group)} targets; they run one after another"
                for group in targets.groups(plan.targets) if len(group) > 1]
    return plan.notices + parallel


def check(session_file, results, config):
    """--check-session: the plan, then each skip; runs nothing and writes nothing."""
    session, rows, known, plan = resolved(session_file, config)
    for line in probe.listing(rows, known):
        print(line)
    for line in lines(session, plan, results):
        print(line)
    for line in notices(plan):
        warn(line)
    for name, line in plan.skipped:
        print(f"skipped:   {name}: {line}")
    stop = targets.nothing_to_measure(plan)
    if stop:
        raise stop
