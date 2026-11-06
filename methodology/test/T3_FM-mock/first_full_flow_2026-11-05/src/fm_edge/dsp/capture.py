import numpy as np

from fm_edge.config.logger import get_logger

log = get_logger(__name__)


def convert_samples(raw: bytes) -> np.ndarray:
    data = np.frombuffer(raw, dtype=np.uint8)
    return convert_samples_from_uint8(data)


def convert_samples_from_uint8(data: np.ndarray) -> np.ndarray:
    i_samples = data[0::2].astype(np.float32)
    q_samples = data[1::2].astype(np.float32)
    iq = (i_samples - 127.5 + 1j * (q_samples - 127.5)) / 127.5
    log.debug("converted %d IQ samples", len(iq))
    return iq.astype(np.complex64)
