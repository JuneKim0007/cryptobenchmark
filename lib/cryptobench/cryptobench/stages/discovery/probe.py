"""DeviceProbe on the device: the plan directory emptied, the probe run, the capture and trial it wrote pulled into discovery/."""
import time

from cryptobench.shared.device.adb import DeviceError, instrumentation_report


def probe(device, discovery, arguments=()):
    # The app must create its own directory: one made by shell is not writable by the app's uid.
    device.shell(f"rm -rf {device.files}")
    device.shell(f"rm -f {device.media}/*-benchmarkData.json")
    output = device.instrument("DeviceProbe", "-e", "hostMillis", str(int(time.time() * 1000)), *arguments)
    if "OK (1 test)" not in output:
        raise DeviceError("DeviceProbe failed on the device:\n" + instrumentation_report(output))
    device.pull(f"{device.files}/.", discovery)
