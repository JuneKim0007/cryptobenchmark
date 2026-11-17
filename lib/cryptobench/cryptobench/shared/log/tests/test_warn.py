import logging

from cryptobench.shared.log.emit import EVENT_ATTR, LOGGER
from cryptobench.shared.log.warn import warn


def test_a_warning_is_one_line_a_problem_and_one_event_with_its_code(capsys, caplog):
    problems = []
    with caplog.at_level(logging.INFO, logger=LOGGER.name):
        warn("plan_not_pulled: adb lost", problems)
        warn("prose without a code")
    assert capsys.readouterr().out == "warning: plan_not_pulled: adb lost\nwarning: prose without a code\n"
    assert problems == ["plan_not_pulled: adb lost"]
    events = [getattr(r, EVENT_ATTR) for r in caplog.records]
    assert [(e["event"], e["outcome"], e["data"]["code"]) for e in events] == [("log", "warn", "plan_not_pulled"), ("log", "warn", None)]
