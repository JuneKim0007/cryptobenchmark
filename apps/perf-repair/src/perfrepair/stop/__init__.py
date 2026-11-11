"""The terminator: the code table, terminate() and Halt; `stops.<code>` overrides an overridable code's action."""
from .codes import CODES
from .terminate import halt_of, terminate

__all__ = ["CODES", "halt_of", "terminate"]
