"""A failure as the one line a terminal or a log shows."""


def one_line(error):
    return " ".join(str(error).split())[:500]
