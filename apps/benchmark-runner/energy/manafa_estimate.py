"""Joules from a stopped EManafa per case window; a number it did not give is not_measured with the reason."""
import math

KIND = "estimated"
SOURCE = "manafa"


class NotMeasured(Exception):
    pass


def one_line(error):
    return " ".join(str(error).split()) or type(error).__name__


def cpu_events(em):
    return em.perf_events.events or []


def battery_events(em):
    return (em.bat_events.events if em.bat_events is not None else None) or []


def consumption(em, start, end):
    """Seconds on manafa's clock. Its fallback without batterystats multiplies by millivolts, so it reads 1000 times high."""
    events = cpu_events(em)
    if not events or start < events[0].time or end > events[-1].time:
        raise NotMeasured("window_uncovered")
    if not battery_events(em):
        raise NotMeasured("no_batterystats")
    try:
        total, components, _ = em.get_consumption_in_between(start, end)
    except Exception as error:
        raise NotMeasured(f"consumption_failed: {one_line(error)}") from error
    if not (isinstance(total, (int, float)) and math.isfinite(total) and total > 0):
        raise NotMeasured(f"no_estimate: {total}")
    return float(total), components


def case(em, failure, start_ns, end_ns, operations):
    """start_ns and end_ns on BOOTTIME; manafa places its events at boot time plus BOOTTIME."""
    start, end = em.boot_time + start_ns / 1e9, em.boot_time + end_ns / 1e9
    result = {"joules": None, "netJoules": None, "operations": operations, "joulesPerOperation": None,
              "windowSeconds": (end_ns - start_ns) / 1e9}
    try:
        if failure:
            raise NotMeasured(failure)
        if not operations:
            raise NotMeasured("no_operations")
        total, components = consumption(em, start, end)
    except NotMeasured as reason:
        return result | {"notMeasured": str(reason)}
    return result | {"joules": total, "joulesPerOperation": total / operations, "components": components}


def judge(result):
    reasons = [f"not_measured: {result['notMeasured']}"] if "notMeasured" in result else []
    result.update(valid=not reasons, invalid=reasons)
    return result


def probe(em, failure):
    """A finished session's readings, and the reason its numbers cannot be used, if any."""
    events = cpu_events(em)
    reading = {"cpuFrequencyEvents": len(events), "batteryStatsEvents": len(battery_events(em)), "joules": None}
    if failure:
        return reading, failure
    if len(events) < 2:
        return reading, "no_cpu_frequency_events"
    try:
        reading["joules"] = consumption(em, events[0].time, events[-1].time)[0]
    except NotMeasured as reason:
        return reading, str(reason)
    return reading, None
