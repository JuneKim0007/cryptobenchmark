"""The rails source on the host: its pre-flight over Perfetto sessions, and energy.py after the run."""
import contextlib, json

from .runner import case_arguments
from cryptobench.shared import paths

# The busy window only proves the rails respond to load; the idle window is run.energyIdleSeconds.
BUSY_SECONDS = 3
RAILS_CONFIG = ('buffers { size_kb: 4096 }\n'
                'data_sources { config { name: "android.power" android_power_config { battery_poll_ms: 100 collect_power_rails: true } } }\n'
                'duration_ms: {millis}\n')


class RailsSource:
    MODULE = "perfetto"
    REQUIREMENTS = ("requirements.txt",)

    def __init__(self, host, idle_seconds):
        self.host, self.idle_seconds = host, idle_seconds

    def preflight(self, session, discovery, accept_unresponsive, held):
        """held(record) runs an idle reading behind the thermal gate and returns the skin temperature at its start and end."""
        at = paths.Discovery(discovery)
        at.energy_preflight.mkdir(exist_ok=True)
        for config, seconds in ((at.idle_rails_config, self.idle_seconds), (at.busy_rails_config, BUSY_SECONDS)):
            config.write_text(RAILS_CONFIG.replace("{millis}", str(seconds * 1000)))
        skin = held(lambda: session.reading(at.idle_rails_config, at.idle_trace))
        session.reading(at.busy_rails_config, at.busy_trace, busy=True)
        capability = at.energy
        self.host.tool("preflight.py", at.idle_trace, at.busy_trace, self.idle_seconds, BUSY_SECONDS, capability,
                       *(["--accept-unresponsive"] if accept_unresponsive else []), "--skin", json.dumps(skin))
        return capability

    def idle_end(self, session, discovery, held):
        """After the last pass: the same idle window again, added to energy.yaml; joules then read the line between the two."""
        at = paths.Discovery(discovery)
        skin = held(lambda: session.reading(at.idle_rails_config, at.idle_end_trace))
        self.host.tool("preflight.py", "--end", at.idle_end_trace, self.idle_seconds, at.energy, "--skin", json.dumps(skin))
        return True

    def window(self, _folder):
        """The rails count on their own; only the run's traces are read."""
        return contextlib.nullcontext()

    def joules(self, *case_paths):
        self.host.tool("energy.py", *case_arguments(*case_paths))
