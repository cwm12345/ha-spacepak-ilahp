# Written by Claude, guided by Chris.
"""Installer tuning: cycling, outdoor compensation, pump and compressor limits."""

from __future__ import annotations

from modbus_connection.model import Component, boolean, enum, gauge, integer

from .enums import PumpMode

__all__ = ["Tuning"]


class Tuning(Component):
    """Installer parameters that shape how the unit cycles and what water it makes.

    Read-only here. These are the installer's settings, and a wrong value can
    short-cycle the compressor or leave the house short of heat, so change
    them at the unit. Absolute temperatures are signed tenths of a degree
    Celsius; differentials (unit ``K``) are tenths of a kelvin, the same size
    step as a degree Celsius.

    The manual gives the range of each parameter but not always the exact
    rule behind it; the docstrings say where the meaning is inferred.
    """

    shutdown_ambient_temperature = gauge(1037, 0.1, unit="°C")
    """A03, the outdoor temperature below which the unit stops."""

    heating_restart_difference = gauge(1160, 0.1, signed=False, unit="K")
    """R04, how far the water drops below the heating target before the
    unit restarts."""

    heating_stop_difference = gauge(1161, 0.1, signed=False, unit="K")
    """R05, the manual's "constant temperature downtime difference" for
    heating: the margin around the target at which the unit stops."""

    low_ambient_compensation_start = gauge(1167, 0.1, unit="°C")
    """R29, the outdoor temperature at which low-ambient compensation of the
    heating target begins."""

    low_ambient_compensation_end = gauge(1168, 0.1, unit="°C")
    """R30, the outdoor temperature at which low-ambient compensation ends."""

    low_ambient_heating_target = gauge(1169, 0.1, unit="°C")
    """R31, the heating target low-ambient compensation aims for."""

    cooling_restart_difference = gauge(1174, 0.1, signed=False, unit="K")
    """R06, how far the water rises above the cooling target before the unit
    restarts."""

    cooling_stop_difference = gauge(1175, 0.1, signed=False, unit="K")
    """R07, the cooling counterpart of ``heating_stop_difference``."""

    heating_restart_ambient_temperature = gauge(1192, 0.1, unit="°C")
    """R39, the outdoor temperature for heating mode's automatic restart."""

    pump_mode = enum(1197, PumpMode)
    """P01, how the water pump runs while the unit is idle."""

    pump_interval = integer(1198, signed=False, unit="min")
    """P02, minutes between idle pump runs in ``PumpMode.INTERVAL``."""

    pump_run_time = integer(1199, signed=False, unit="min")
    """P03, minutes per idle pump run in ``PumpMode.INTERVAL``."""

    compressor_min_frequency = integer(1219, signed=False, unit="Hz")
    """C02."""

    compressor_max_frequency = integer(1220, signed=False, unit="Hz")
    """C03."""

    weather_compensation_slope = gauge(1234, 0.1, signed=False)
    """The weather compensation curve's slope (0 to 3.5)."""

    weather_compensation_offset = gauge(1235, 0.1, unit="°C")
    """The weather compensation curve's offset."""

    weather_compensation_enabled = boolean(1236)
    """Whether weather compensation adjusts the heating target. See
    ``Status.compensated_heating_target_temperature`` for the result."""
