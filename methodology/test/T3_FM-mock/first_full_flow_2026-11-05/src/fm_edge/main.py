import asyncio

from fm_edge.config.logger import get_logger
from fm_edge.hal.port import HalPort, HalFrame
from fm_edge.dsp.spectrum import compute_spectrum, validate_fc
from fm_edge.dsp.channels import ChannelDetector
from fm_edge.output.server import UpdateServer, format_message

log = get_logger(__name__)

DEFAULT_FC_HZ = 98_000_000
DEFAULT_PORT = 8765


async def run_pipeline(hal: HalPort, fc_hz: int = DEFAULT_FC_HZ, port: int = DEFAULT_PORT) -> None:
    if not validate_fc(fc_hz):
        raise ValueError(f"Invalid centre frequency: {fc_hz}")

    detector = ChannelDetector(fc_hz)
    server = UpdateServer(port=port)

    await server.start()
    log.info("WebSocket server started on port %d", port)

    try:
        async for frame in hal.stream():
            samples = frame.samples
            spectrum = compute_spectrum(samples, fc_hz)
            channels = detector.update(spectrum)
            message = format_message(spectrum, channels, frame.t_capture_end)
            await server.broadcast(message)
    finally:
        await server.stop()


def main() -> None:
    log.info("fm_edge starting")
    log.info("fm_edge: use run_pipeline() with a HAL instance")
