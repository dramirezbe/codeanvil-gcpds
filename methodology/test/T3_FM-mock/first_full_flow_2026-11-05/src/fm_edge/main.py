import asyncio
import argparse

from fm_edge.config.logger import get_logger
from fm_edge.hal.port import HalPort, HalFrame
from fm_edge.hal.mock import MockHal, SCENES
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
    parser = argparse.ArgumentParser(description="FM occupancy edge service (Mock HAL)")
    parser.add_argument("--scene", choices=SCENES, default="SC-2")
    parser.add_argument("--fc-hz", type=int, default=DEFAULT_FC_HZ)
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--updates", type=int, default=0, help="0 runs continuously")
    parser.add_argument("--period", type=float, default=0.5, help="seconds per update")
    args = parser.parse_args()

    hal = MockHal(args.scene, args.fc_hz, args.seed, args.updates, args.period)
    log.info("Mock HAL active: %s; WebSocket port %d", args.scene, args.port)
    try:
        asyncio.run(run_pipeline(hal, args.fc_hz, args.port))
    except KeyboardInterrupt:
        log.info("fm_edge stopped")
