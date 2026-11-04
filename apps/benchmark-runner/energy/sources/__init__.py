"""energy.source names and their adapters; each has preflight, window and joules."""
from .manafa_source import ManafaSource
from .rails_source import RailsSource

SOURCES = {"rails": RailsSource, "manafa": ManafaSource}
