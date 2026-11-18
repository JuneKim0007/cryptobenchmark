"""DeviceProbe on the device: the plan directory emptied, the probe run, the capture and trial it wrote pulled into discovery/."""
import time

from cryptobench.shared.device import instrumentation
from cryptobench.shared.device.adb import ONE_PASSED


def probe(device, discovery, waits, arguments=()):
    # The app must create its own directory: one made by shell is not writable by the app's uid.
    row = instrumentation.Instrumented("DeviceProbe", cleared=(f"{device.media}/*-benchmarkData.json",), cleared_dirs=(device.files,),
                                       passed=ONE_PASSED, pulled=((f"{device.files}/.", discovery),))
    # hostMillis read again on each attempt: a wait for the device must not age it
    waits.retried(lambda: instrumentation.once(device, row, "-e", "hostMillis", str(int(time.time() * 1000)), *arguments), "the DeviceProbe run")
