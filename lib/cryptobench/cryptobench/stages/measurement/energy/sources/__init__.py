"""energy.source names and their adapters; each has preflight, idle_end, window and joules, the module it imports and its requirements files
(requirements.txt holds the trace reader every source parses windows with)."""
from .manafa_source import ManafaSource
from .rails_source import RailsSource

SOURCES = {"rails": RailsSource, "manafa": ManafaSource}
