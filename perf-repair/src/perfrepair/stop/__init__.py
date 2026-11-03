"""The terminator: the code table, terminate() and Halt; `stops.<code>` overrides an overridable code's action."""
from .codes import CODES, SKIP, STOP, WARN
from .halt import Halt, code_of
from .terminate import terminate

__all__ = ["CODES", "SKIP", "STOP", "WARN", "Halt", "code_of", "terminate"]
