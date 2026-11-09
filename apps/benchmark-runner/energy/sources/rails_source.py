"""The rails source on the host: its pre-flight over Perfetto sessions, and energy.py after the run."""
import contextlib, time

from .runner import case_arguments
from cryptobench import paths

PREFLIGHT_SECONDS = 3
# The busy window spins every core; the first case must not start on that heat.
SETTLE_SECONDS = 15
RAILS_CONFIG = ('buffers { size_kb: 4096 }\n'
                'data_sources { config { name: "android.power" android_power_config { battery_poll_ms: 100 collect_power_rails: true } } }\n'
                'duration_ms: {millis}\n')


class RailsSource:

    def __init__(self, host):
        self.host = host

    def preflight(self, session, discovery, accept_unresponsive):
        folder = paths.Discovery(discovery).energy_preflight
        folder.mkdir(exist_ok=True)
        config = paths.Discovery(discovery).rails_config
        config.write_text(RAILS_CONFIG.replace("{millis}", str(PREFLIGHT_SECONDS * 1000)))
        session.preflight(config, paths.Discovery(discovery).idle_trace, paths.Discovery(discovery).busy_trace)
        capability = paths.Discovery(discovery).energy
        self.host.tool("preflight.py", paths.Discovery(discovery).idle_trace, paths.Discovery(discovery).busy_trace, PREFLIGHT_SECONDS, capability,
                       *(["--accept-unresponsive"] if accept_unresponsive else []))
        time.sleep(SETTLE_SECONDS)
        return capability

    def window(self, _folder):
        """The rails count on their own; only the run's traces are read."""
        return contextlib.nullcontext()

    def joules(self, *case_paths):
        self.host.tool("energy.py", *case_arguments(*case_paths))
