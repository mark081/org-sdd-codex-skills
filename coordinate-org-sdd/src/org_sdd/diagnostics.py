"""Safe structured diagnostics; callers must never include artifact values."""
from __future__ import annotations
from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class Diagnostic:
    code: str
    file: str
    record_id: str | None
    field: str
    message: str

    def to_dict(self):
        return asdict(self)


def sorted_diagnostics(items):
    return sorted(items, key=lambda d: (d.file, d.record_id or "", d.field, d.code))
