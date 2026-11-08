"""Review: a higher tier reads another job's answer and its evidence through read tools and gives one verdict: accept,
refuse with a reason (the job's next repass carries it), or unidentified (the item is a person's)."""
from __future__ import annotations

from dataclasses import dataclass

from ..job import ACCEPT, REFUSE, UNIDENTIFIED, Job
from ..tools.catalogue_read import CATALOGUE_READS
from ..tools.tool import READ, Context, Outcome, Tool, args_schema

NAME = "review"
VERDICTS = (ACCEPT, REFUSE, UNIDENTIFIED)


@dataclass(frozen=True)
class Question:
    job: str
    item: str
    label: str
    output: str
    evidence: str

    @property
    def key(self) -> str:
        return f"{self.job}:{self.item}"


class ReviewJob(Job):
    name = NAME
    prompt = NAME
    submit_name = "verdict"
    submit_description = "your one verdict on the job's answer, with the reason a person or the job's next attempt reads"
    submit_schema = args_schema({"verdict": {"type": "string", "enum": list(VERDICTS)},
                                 "reason": {"type": "string", "pattern": r"\S"}}, ("verdict", "reason"))

    def _reads(self) -> list[Tool]:
        return [*CATALOGUE_READS,
                Tool("read_output", "the job's answer as code would record it", args_schema({}), READ, self._output),
                Tool("read_evidence", "what the job was shown for this item: candidates, measurements, facts",
                     args_schema({}), READ, self._evidence)]

    def _output(self, _args: dict, _ctx: Context) -> Outcome:
        return Outcome(True, self.current.output)

    def _evidence(self, _args: dict, _ctx: Context) -> Outcome:
        return Outcome(True, self.current.evidence)

    def question(self, job: Job, item, submitted: dict) -> Question:
        return Question(job.name, job.key(item), job.label(item), job.output_text(item, submitted), job.evidence_text(item))

    def label(self, q: Question) -> str:
        return f"{q.job} {q.label}"

    def render(self, q: Question) -> str:
        return (f"JOB {q.job}\nITEM {q.label}\n"
                "Read the job's answer with read_output and what it was shown with read_evidence, then call verdict.")
