"""Constants for the SpacePak ILAHP integration."""

# Written by Claude, guided by Chris.

DOMAIN = "spacepak_ilahp"

MANUFACTURER = "SpacePak"
MODEL = "Solstice Inverter Extreme (ILAHP)"
DEFAULT_NAME = "SpacePak ILAHP"

CONF_UNIT_ID = "unit_id"
DEFAULT_PORT = 502
DEFAULT_UNIT_ID = 1

SCAN_INTERVAL = 30
SETTINGS_SCAN_INTERVAL = 300

# The installer's own setpoint limits (R08-R11) as shipped, used until the unit
# has answered with its configured ones.
DEFAULT_MIN_HEATING_SETPOINT = 15.0
DEFAULT_MAX_HEATING_SETPOINT = 50.0
DEFAULT_MIN_COOLING_SETPOINT = 8.0
DEFAULT_MAX_COOLING_SETPOINT = 28.0
