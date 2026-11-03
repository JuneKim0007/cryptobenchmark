from perfetto.trace_processor import TraceProcessor

# Kotlin's EnergyWindow.PREFIX; the two change together.
MARKER_PREFIX = "energy:"
JETPACK_TIMED = "Benchmark Time"
JETPACK_THERMAL_SLEEP = "Sleep due to Thermal Throttle"
JETPACK_RUN = "measurement "


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
        # the first snapshot can lack MONOTONIC (seen on a Pixel 10), so take the first that has both
        rows = list(self.processor.query(
            "select b.clock_value - m.clock_value as offset from clock_snapshot b join clock_snapshot m "
            "on b.snapshot_id = m.snapshot_id where b.clock_name = 'BOOTTIME' and m.clock_name = 'MONOTONIC' "
            "order by b.snapshot_id limit 1"))
        return rows[0].offset if rows else None

    def timed_phases(self):
        """Each Jetpack timed phase with its numbered measurement runs and its heat sleeps, MONOTONIC, in time order."""
        phases = list(self.processor.query(f"select id, ts, ts + dur as end_ts from slice where name = '{JETPACK_TIMED}' and dur > 0 order by ts"))
        out = []
        for phase in phases:
            children = list(self.processor.query(f"select name, ts, ts + dur as end_ts from slice where parent_id = {phase.id} and dur > 0 order by ts"))
            runs = [(int(c.name[len(JETPACK_RUN):]), c.ts, c.end_ts) for c in children
                    if c.name.startswith(JETPACK_RUN) and c.name[len(JETPACK_RUN):].isdigit()]
            sleeps = [(c.ts, c.end_ts) for c in children if c.name == JETPACK_THERMAL_SLEEP]
            out.append({"start": phase.ts, "end": phase.end_ts, "runs": runs, "sleeps": sleeps})
        return out
