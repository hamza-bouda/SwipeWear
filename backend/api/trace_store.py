"""Small in-process trace store used by the authenticated development endpoint."""
from __future__ import annotations

from collections import OrderedDict
from threading import Lock
from uuid import UUID

from contracts.trace import RequestTrace

_MAX_TRACES = 500
_traces: OrderedDict[UUID, RequestTrace] = OrderedDict()
_lock = Lock()


def save(trace: RequestTrace) -> None:
    with _lock:
        _traces[trace.trace_id] = trace
        _traces.move_to_end(trace.trace_id)
        while len(_traces) > _MAX_TRACES:
            _traces.popitem(last=False)


def get(trace_id: UUID) -> RequestTrace | None:
    with _lock:
        return _traces.get(trace_id)


def reset() -> None:
    with _lock:
        _traces.clear()

