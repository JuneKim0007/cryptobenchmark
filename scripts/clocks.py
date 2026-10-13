"""CPU clock state read through adb shell; locked means every online core's floor equals its ceiling."""
import yaml

CLOCKS = "clocks.yaml"

READ = ('for c in /sys/devices/system/cpu/cpu[0-9]*; do f=$c/cpufreq; '
        'echo "${c##*/} $(cat $c/online 2>/dev/null || echo 1) $(cat $f/scaling_governor 2>/dev/null || echo -) '
        '$(cat $f/scaling_min_freq 2>/dev/null || echo -) $(cat $f/scaling_max_freq 2>/dev/null || echo -)"; done')


def parse(text):
    cores = []
    for line in text.splitlines():
        fields = line.split()
        if len(fields) != 5:
            continue
        name, online, governor, low, high = fields
        cores.append({"core": name, "online": online == "1", "governor": governor,
                      "minKhz": int(low) if low.isdigit() else None, "maxKhz": int(high) if high.isdigit() else None})
    return cores


def locked(snapshots):
    cores = [core for snapshot in snapshots for core in snapshot if core["online"]]
    if not cores or any(core["minKhz"] is None or core["maxKhz"] is None for core in cores):
        return None
    return all(core["minKhz"] == core["maxKhz"] for core in cores)


def read(device):
    return parse(device.shell(READ))


def write(path, before, after):
    state = locked([before, after])
    document = {"schemaVersion": 1, "locked": "unknown" if state is None else state, "before": before, "after": after}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(document, sort_keys=False))
    return path


def runtime_locked(paths):
    states = [yaml.safe_load(path.read_text())["locked"] for path in paths]
    if any(state == "unknown" for state in states):
        return "unknown"
    return str(all(states)).lower()
