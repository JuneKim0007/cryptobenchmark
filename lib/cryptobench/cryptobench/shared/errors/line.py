"""A failure as the one line a terminal or a log shows."""


def one_line(error, limit=500):
    return " ".join(str(error).split())[:limit]
