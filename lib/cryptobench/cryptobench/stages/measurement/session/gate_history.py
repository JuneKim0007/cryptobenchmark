"""What one temperature gate session did: each case's waits and discards for thermal.json, every started run's limit and wait for its line."""


class GateHistory:
    """The gate writes it, the Thermal hook reads it; no document means no gate: no line, and thermal.json's gate is null."""

    def __init__(self, label=None, document=None):
        self.label, self.document = label, document
        self.held, self.limits, self.waits, self.discards = {}, [], [], 0

    def passed(self, case, limit, waited):
        self.limits.append(limit)
        self.waits.append(waited)
        before = self.held.get(case, {})
        self.held[case] = {"waitedSeconds": round(before.get("waitedSeconds", 0.0) + waited, 1), "target": limit, "discards": before.get("discards", 0)}

    def discarded(self, case):
        self.discards += 1
        self.held[case]["discards"] += 1

    def records(self):
        """What this process's cases waited and discarded, then cleared for the next process."""
        records, self.held = self.held, {}
        return records

    def summary(self):
        if self.document is None:
            return None
        limit = f"start limit {min(self.limits):.2f}-{max(self.limits):.2f} C" if self.limits else "no run started"
        return f"{self.label}: {sum(1 for w in self.waits if w)} of {len(self.waits)} runs waited, {sum(self.waits):.0f} s; {self.discards} runs discarded; {limit}"
