"""Perfetto sessions on the device for energy; rails are read by apps/benchmark-runner/energy, this only starts, stops and pulls."""

from cryptobench import paths
from device.adb import NO_DEFAULT_PROFILER, PASSED, DeviceError, instrumentation_report

TRACES = "/data/misc/perfetto-traces"   # where the shell user's perfetto may write
SCRATCH = "/data/local/tmp"


class EnergySession:

    def __init__(self, device):
        self.device = device

    def pull_traces(self, into, fresh=True):
        """fresh: the folder starts empty; else traces already pulled stay and only new names are added."""
        into.mkdir(parents=True, exist_ok=True)
        if fresh:
            for stale in into.glob("*.perfetto-trace"):
                stale.unlink()
        names = [n for n in self.device.shell(f"ls {self.device.media}").split() if n.endswith(".perfetto-trace")]
        for name in names:
            if not (into / name).is_file():
                self.device.pull(f"{self.device.media}/{name}", into / name)
        return len(list(into.glob("*.perfetto-trace")))

    def record(self, config, remote, busy=False):
        self.device.run("push", str(config), f"{SCRATCH}/{config.name}")
        session = f"cat {SCRATCH}/{config.name} | perfetto --txt -c - -o {remote} >/dev/null 2>&1"
        if busy:
            session = ("pids=; for i in $(seq $(nproc)); do (while :; do :; done) & pids=\"$pids $!\"; done; "
                       f"{session}; kill $pids")
        self.device.shell(session)

    def preflight(self, config, idle, busy):
        for local, loaded in ((idle, False), (busy, True)):
            remote = f"{TRACES}/{local.name}"
            self.record(config, remote, busy=loaded)
            self.device.pull(remote, local)

    def dry_pass(self, config, trace, calls, preparation, test_class="EnergyDryBenchmark"):
        """No Jetpack trace runs in this pass, so none kills the host session."""
        self.device.shell(f"rm -f {self.device.files}/{paths.ENERGY_DRY}")
        self.device.run("push", str(config), f"{SCRATCH}/{config.name}")
        remote = f"{TRACES}/{trace.name}"
        printed = self.device.shell(f"cat {SCRATCH}/{config.name} | perfetto --txt -c - -o {remote} --background-wait")
        started = next((token for token in reversed(printed.split()) if token.isdigit()), None)
        if started is None:
            raise DeviceError(f"perfetto did not start: {printed.strip()}")
        try:
            output = self.device.instrument(test_class, *NO_DEFAULT_PROFILER)
        finally:
            self.device.shell(f"kill {started}; while kill -0 {started} 2>/dev/null; do sleep 0.2; done")
        if not PASSED.search(output):
            raise DeviceError(f"{test_class} failed on the device:\n" + instrumentation_report(output))
        trace.parent.mkdir(parents=True, exist_ok=True)
        self.device.pull(remote, trace)
        self.device.pull(f"{self.device.files}/{paths.ENERGY_DRY}", calls)
        self.device.pull_plan(preparation)
