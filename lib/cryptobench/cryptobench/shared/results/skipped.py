"""Skip records as preparation's skipped.yaml and config's report.yaml write them: stage, provider, type, name, caseId (one case only), code, reason."""
from cryptobench.shared.document.document import DocumentKind
from cryptobench.shared.paths.names import CONFIG_REPORT, SKIPPED

SKIPPED_DOC = DocumentKind(SKIPPED, 2)
REPORT_DOC = DocumentKind(CONFIG_REPORT, 2)


def records(document, kind=SKIPPED_DOC):
    """The skip records of a document of this kind; an empty document (nothing pulled) has none."""
    return kind.check(document).get("skipped") or [] if document else []
