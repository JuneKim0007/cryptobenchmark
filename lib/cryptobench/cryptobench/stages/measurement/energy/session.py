"""Perfetto sessions on the device for energy; rails are read by apps/benchmark-runner/energy, this only starts, stops and pulls."""
import contextlib

from cryptobench.shared import paths
from cryptobench.shared.device import instrumentation, reconnect
from cryptobench.shared.device.adb import NO_DEFAULT_PROFILER, DeviceError
from cryptobench.shared.device.plan import plan_pulls

TRACES, SCRATCH = paths.DeviceDirs.TRACES, paths.DeviceDirs.SCRATCH


class EnergySession:

    def __init__(self, device, waits=reconnect.Off()):
        self.device, self.waits = device, waits

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
        remote, dry = f"{TRACES}/{trace.name}", f"{self.device.files}/{paths.ENERGY_DRY}"
        row = instrumentation.Instrumented(test_class, cleared=(dry,), pulled=((remote, trace), (dry, calls), *plan_pulls(self.device, preparation)))
        instrumentation.run(self.device, self.waits, row, *NO_DEFAULT_PROFILER, during=lambda: self.traced(config, remote))

    @contextlib.contextmanager
    def traced(self, config, remote):
        self.device.run("push", str(config), f"{SCRATCH}/{config.name}")
        printed = self.device.shell(f"cat {SCRATCH}/{config.name} | perfetto --txt -c - -o {remote} --background-wait")
        started = next((token for token in reversed(printed.split()) if token.isdigit()), None)
        if started is None:
            raise DeviceError(f"perfetto did not start: {printed.strip()}")
        try:
            yield
        finally:
            self.device.shell(f"kill {started}; while kill -0 {started} 2>/dev/null; do sleep 0.2; done")
