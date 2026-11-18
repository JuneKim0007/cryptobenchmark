"""A case the device's preparation refused with a code codes.yaml holds as an outcome or an error: final, never launched again in its
process, one case_skipped line; any other failure keeps its retries."""
from cryptobench.shared.errors.coded import code_in
from cryptobench.shared.errors.glossary import codes

CASE_SKIPPED = "case_skipped"
FINAL_KINDS = ("outcome", "error")


def split(reason):
    """skipped.yaml's `<case id>: <reason>` (RunnablePlan.guarded) as the id and the reason; a reason naming no case: None and itself."""
    case, separator, rest = str(reason or "").partition(": ")
    return (case, rest) if separator and " " not in case else (None, str(reason or ""))


def coded(record):
    """(case, code) when the record names a case and its code is a final kind; else None."""
    case, reason = split((record or {}).get("reason"))
    code = code_in(reason)
    return (case, code) if case and (codes().get(code) or {}).get("kind") in FINAL_KINDS else None


def recorded(document):
    """Every final skip a skipped.yaml document holds, by case id; the last record of a case wins."""
    return dict(found for record in (document or {}).get("skipped") or [] if (found := coded(record)))


def line(case, code):
    return f"{CASE_SKIPPED}: {case}: {code}"


def every_case(failures):
    return bool(failures) and all(failure.startswith(f"{CASE_SKIPPED}: ") for failure in failures)
