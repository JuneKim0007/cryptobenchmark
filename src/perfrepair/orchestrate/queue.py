"""File-backed FIFO of decision items, saved after every item so a run resumes where it stopped.

An item leaves the queue only through `done`, after its decision is saved: a crash between the
agent's answer and the save re-asks that item instead of losing it.
"""
from __future__ import annotations

from pathlib import Path
from typing import Generic, Protocol, TypeVar

from ..files import read_json, write_json

SCHEMA_VERSION = 1


class Item(Protocol):
    itemId: str


T = TypeVar("T", bound=Item)


class ItemQueue(Generic[T]):
    def __init__(self, path: Path, items: list[T], pending: list[str], done: list[str]):
        self.path, self._items = Path(path), {i.itemId: i for i in items}
        self.pending, self.done_ids = pending, done

    @classmethod
    def open(cls, path: Path, items: list[T]) -> "ItemQueue[T]":
        """Resume from `path` when it holds the same items; start fresh when it does not exist."""
        path, ids = Path(path), [i.itemId for i in items]
        if path.exists():
            doc = read_json(path)
            if sorted(doc["pending"] + doc["done"]) != sorted(ids):
                raise ValueError(f"{path}: queue holds other items than this run; remove it to restart")
            q = cls(path, items, doc["pending"], doc["done"])
        else:
            q = cls(path, items, ids, [])
        q.save()
        return q

    def __len__(self) -> int:
        return len(self.pending)

    def peek(self) -> T | None:
        return self._items[self.pending[0]] if self.pending else None

    def done(self, item_id: str) -> None:
        if not self.pending or self.pending[0] != item_id:
            raise ValueError(f"{item_id} is not the head of the queue")
        self.done_ids.append(self.pending.pop(0))
        self.save()

    def save(self) -> None:
        write_json(self.path, {"schemaVersion": SCHEMA_VERSION, "pending": self.pending, "done": self.done_ids})
