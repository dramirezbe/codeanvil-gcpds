import math
import os

TIMEZONE = "America/Bogota"
HAL_MODE = os.environ.get("FM_HAL", "real")
SCAN_PERIOD_S = 0.5

# Live receiver screening compares each channel with the sweep median plus this margin.
OCCUPANCY_MARGIN_DB = float(os.environ.get("FM_OCCUPANCY_MARGIN_DB", "4"))
if not math.isfinite(OCCUPANCY_MARGIN_DB) or OCCUPANCY_MARGIN_DB < 0:
    raise ValueError("FM_OCCUPANCY_MARGIN_DB must be a finite nonnegative number")
