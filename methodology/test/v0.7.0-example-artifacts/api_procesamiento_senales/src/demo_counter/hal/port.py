from itertools import cycle
from typing import Protocol


class SamplePort(Protocol):
    def read(self) -> float: ...


class RuntimeMockHAL:
    """Shipped deterministic source; no verification dependency."""

    def __init__(self) -> None:
        self._values = cycle((0.0, 1.0, 2.0))

    def read(self) -> float:
        return next(self._values)
