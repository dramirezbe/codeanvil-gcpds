from dataclasses import dataclass
from typing import AsyncIterator, Protocol

import numpy as np


@dataclass(frozen=True)
class HalFrame:
    samples: np.ndarray  # complex64, shape (65536,)
    t_capture_end: str   # ISO 8601 with ms
    fc_hz: int


class HalPort(Protocol):
    def stream(self) -> AsyncIterator[HalFrame]: ...
