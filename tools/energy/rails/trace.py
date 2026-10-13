from perfetto.trace_processor import TraceProcessor

# Kotlin's EnergyWindow.PREFIX; the two change together.
MARKER_PREFIX = "energy:"
JETPACK_TIMED = "Benchmark Time"
JETPACK_THERMAL_SLEEP = "Sleep due to Thermal Throttle"


class Trace:

    def __init__(self, path):
        self.processor = TraceProcessor(trace=str(path))

    def close(self):
        self.processor.close()

    def rails(self):
        rows = self.processor.query(
            "select t.name as name, c.ts as ts, c.value as value from counter c "
            "join counter_track t on c.track_id = t.id where t.name like 'power.%' order by t.name, c.ts")
        out = {}
        for r in rows:
            out.setdefault(r.name, []).append((r.ts, r.value))
        return out

    def markers(self):
        rows = self.processor.query(
            f"select name, ts, dur from slice where name like '{MARKER_PREFIX}%' and dur > 0")
        return {r.name[len(MARKER_PREFIX):]: (r.ts, r.ts + r.dur) for r in rows}

    def boot_minus_monotonic(self):
        """BOOTTIME - MONOTONIC (time suspended): rails are stamped in BOOTTIME, androidx 1.5.0 phase slices in MONOTONIC."""
        rows = {r.clock_name: r.clock_value for r in self.processor.query(
            "select clock_name, clock_value from clock_snapshot where snapshot_id = (select min(snapshot_id) from clock_snapshot)")}
        if "BOOTTIME" not in rows or "MONOTONIC" not in rows:
            return None
        return rows["BOOTTIME"] - rows["MONOTONIC"]

    def timed_phases(self):
        """A phase that slept for heat starts after its last sleep: the attempt before it was discarded and re-run."""
        rows = self.processor.query(f"""
            select bt.ts as ts, bt.ts + bt.dur as end_ts,
              (select max(c.ts + c.dur) from slice c where c.parent_id = bt.id and c.name = '{JETPACK_THERMAL_SLEEP}') as slept
            from slice bt where bt.name = '{JETPACK_TIMED}' and bt.dur > 0 order by bt.ts""")
        return [(r.slept or r.ts, r.end_ts) for r in rows]
