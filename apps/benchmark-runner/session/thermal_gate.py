"""The temperature gate's place among a session's hooks: it writes what happened beside the readings and prints one line per pass."""
import json

from session.measure import Hooks
from cryptobench import paths


class GateRecords(Hooks):

    def __init__(self, gate):
        self.gate = gate

    def after_process(self, process):
        # after_* run in reverse, so thermal_hook has written thermal.json by now
        path = paths.Measurement(process.into).thermal
        if not path.is_file():
            return
        document, records = json.loads(path.read_text()), self.gate.records()
        document["gate"] = self.gate.document()
        for case, reading in document["cases"].items():
            if case in records:
                reading["gate"] = records[case]
        path.write_text(json.dumps(document, indent=1))

    def after_session(self, _processes):
        line = self.gate.summary()
        if line:
            print(f"gate:      {line}")
