"""A case the device's preparation refused with a code codes.yaml holds as an outcome or an error: final, never launched again in its
process, one case_skipped line; any other failure keeps its retries."""
from cryptobench.shared.errors.glossary import codes
from cryptobench.shared.results import skipped

CASE_SKIPPED = "case_skipped"
FINAL_KINDS = ("outcome", "error")


def coded(record):
    """(case, code) when the record names a case and its code is a final kind; else None."""
    case, code = record.get("caseId"), record.get("code")
    return (case, code) if case and (codes().get(code) or {}).get("kind") in FINAL_KINDS else None


def recorded(document):
    """Every final skip a skipped.yaml document holds, by case id; the last record of a case wins."""
    return dict(found for record in skipped.records(document) if (found := coded(record)))


def line(case, code):
    return f"{CASE_SKIPPED}: {case}: {code}"


def every_case(failures):
    return bool(failures) and all(failure.startswith(f"{CASE_SKIPPED}: ") for failure in failures)
