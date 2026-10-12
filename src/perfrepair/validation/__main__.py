"""python3 -m perfrepair.validation <run dir> — validate every artifact; exit 1 on any problem."""
from __future__ import annotations

import sys
from pathlib import Path

from .run import validate_run


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print(__doc__.strip(), file=sys.stderr)
        return 2
    report = validate_run(Path(argv[0]))
    for artifact, problems in report.items():
        print(f"{artifact}: {'ok' if not problems else f'{len(problems)} problem(s)'}")
        for p in problems:
            print(f"  - {p}")
    return 1 if any(report.values()) else 0


if __name__ == "__main__":
    sys.exit(main())
