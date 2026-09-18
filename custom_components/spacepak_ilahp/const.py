# Written by Claude, guided by Chris.
"""Constants for the SpacePak ILAHP integration."""
from __future__ import annotations

DOMAIN = "spacepak_ilahp"

DEFAULT_GATEWAY_HOST = ""
DEFAULT_UNIT_ID = 1
DEFAULT_SCAN_INTERVAL = 30  # seconds

MANUFACTURER = "SpacePak"
MODEL = "Solstice Inverter Extreme (ILAHP)"

CONF_UNIT_ID = "unit_id"

# Heating target temp bounds, Celsius -- per the unit's own manual, register
# 1158 (R02) range is documented as roughly 50-140F (10-60C). Kept generous
# but not unbounded, since this writes directly to a live heat pump.
MIN_TARGET_TEMP_C = 10.0
MAX_TARGET_TEMP_C = 60.0
