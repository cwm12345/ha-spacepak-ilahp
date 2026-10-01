# Written by Claude, guided by Chris.
"""What the unit has been told to do: power, mode and water setpoints."""

from __future__ import annotations

from collections.abc import Callable

from modbus_connection.model import Component, boolean, enum, gauge

from .enums import OperatingMode

__all__ = ["Controls"]


def _within(low: float, high: float) -> Callable[[float], float]:
    """A write validator refusing values outside the register's own range."""

    def validate(value: float) -> float:
        if not low <= value <= high:
            raise ValueError(f"{value} is outside {low}..{high}")
        return value

    return validate


class Controls(Component):
    """Power, operating mode and the heating/cooling water setpoints.

    Every temperature on this unit is stored in tenths of a degree Celsius,
    whatever the display is set to show.

    A setpoint write is checked against the widest range the register
    accepts. The unit narrows that further with its own minimum and maximum
    setpoints (``min_heating_setpoint`` and so on), which the installer sets
    and which this component reads alongside.
    """

    power_on = boolean(1011, writable=True)
    """Unit on/off."""

    operating_mode = enum(1012, OperatingMode)
    """The mode the unit is set to run in. Read-only here."""

    cooling_enabled = boolean(1021)
    """H05, whether the installer enabled cooling. It decides which values
    ``operating_mode`` can take."""

    field_wired_control = boolean(1023)
    """H07, true when the unit takes its commands from field-wired inputs
    ("Slave" on the touchscreen) rather than its own display. In that mode a
    ``power_on`` write alone does not start the unit; the remote on/off input
    decides."""

    hot_water_enabled = boolean(1028)
    """H28, whether the unit's own hot water (DHW) function is enabled. When
    it is not, the hot water tank temperature has no sensor behind it."""

    silence_mode = boolean(1030)
    """H22, whisper mode."""

    heating_target_temperature = gauge(
        1158, 0.1, unit="°C", writable=_within(-30.0, 99.0)
    )
    """R02, the heating water target."""

    cooling_target_temperature = gauge(
        1159, 0.1, unit="°C", writable=_within(-30.0, 80.0)
    )
    """R03, the cooling water target."""

    min_cooling_setpoint = gauge(1162, 0.1, unit="°C")
    """R08, the lowest cooling target the unit accepts."""

    max_cooling_setpoint = gauge(1163, 0.1, unit="°C")
    """R09, the highest cooling target the unit accepts."""

    min_heating_setpoint = gauge(1164, 0.1, unit="°C")
    """R10, the lowest heating target the unit accepts."""

    max_heating_setpoint = gauge(1165, 0.1, unit="°C")
    """R11, the highest heating target the unit accepts."""
