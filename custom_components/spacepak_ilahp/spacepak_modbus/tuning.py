# Written by Claude, guided by Chris.
"""Installer tuning: cycling, outdoor compensation, pump and compressor limits."""

from __future__ import annotations

from collections.abc import Callable

from modbus_connection.model import Component, boolean, enum, gauge, integer

from .enums import PumpMode

__all__ = ["Tuning"]


def _difference_within(high: float) -> Callable[[float], float]:
    """A write validator for a differential, refusing values outside 0..high."""

    def validate(value: float) -> float:
        if not 0.0 <= value <= high:
            raise ValueError(f"{value} is outside 0.0..{high}")
        return value

    return validate


def _whole_minutes(low: int, high: int) -> Callable[[float], int]:
    """A write validator for a whole number of minutes in low..high."""

    def validate(value: float) -> int:
        if value != int(value) or not low <= value <= high:
            raise ValueError(f"{value} is not a whole number in {low}..{high}")
        return int(value)

    return validate


class Tuning(Component):
    """Installer parameters that shape how the unit cycles and what water it makes.

    Read-only here, except the two heating differentials (R04 and R05) and
    the pump interval (P02). These
    are the installer's settings, and a wrong value can short-cycle the
    compressor or leave the house short of heat, so change the rest at the
    unit. Absolute temperatures are signed tenths of a degree
    Celsius; differentials (unit ``K``) are tenths of a kelvin, the same size
    step as a degree Celsius.

    The manual gives the range of each parameter but not always the exact
    rule behind it; the docstrings say where the meaning is inferred.
    """

    shutdown_ambient_temperature = gauge(1037, 0.1, unit="°C")
    """A03, the outdoor temperature below which the unit stops."""

    antifreeze_temperature = gauge(1038, 0.1, unit="°C")
    """A04, the water temperature at which antifreeze protection starts."""

    antifreeze_difference = gauge(1039, 0.1, signed=False, unit="K")
    """A05, how far above ``antifreeze_temperature`` protection ends."""

    antifreeze_min_temperature = gauge(1053, 0.1, unit="°C")
    """A22, the lowest value ``antifreeze_temperature`` may be set to."""

    heating_restart_difference = gauge(
        1160, 0.1, signed=False, unit="K", writable=_difference_within(10.0)
    )
    """R04, the heating restart differential. Per the manual, a new call
    starts when the outlet water is below the target minus R04. While a call
    is held, the unit restarts once the outlet falls R04 below the inlet
    temperature it read when it last stopped. Writable, 0-10 K (the manual's
    0-18 °F); a wider value means fewer, longer runs."""

    heating_stop_difference = gauge(
        1161, 0.1, signed=False, unit="K", writable=_difference_within(10.0)
    )
    """R05, the manual's "constant temperature power-off difference" for
    heating: the unit stops when the outlet water reaches the target plus
    R05. Writable, 0-10 K."""

    outlet_overheat_difference = gauge(1166, 0.1, signed=False, unit="K")
    """R15, how far the outlet water may exceed the target before overheat
    protection acts."""

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

    pump_freeze_protection_ambient = gauge(1193, 0.1, unit="°C")
    """R40, the outdoor temperature below which the water pump runs to keep
    the loop from freezing."""

    pump_mode = enum(1197, PumpMode)
    """P01, how the water pump runs while the unit is idle."""

    pump_interval = integer(
        1198, signed=False, unit="min", writable=_whole_minutes(1, 120)
    )
    """P02, minutes between idle pump runs. The manual ties it to
    ``PumpMode.INTERVAL``, but a unit in ``PumpMode.ECONOMIC`` held on by its
    remote input was seen waking the pump about every P02 minutes and
    restarting the compressor on what it sampled. Writable, 1-120."""

    pump_run_time = integer(1199, signed=False, unit="min")
    """P03, minutes per idle pump run in ``PumpMode.INTERVAL``."""

    compressor_min_frequency = integer(1219, signed=False, unit="Hz")
    """C02."""

    compressor_max_frequency = integer(1220, signed=False, unit="Hz")
    """C03."""

    max_water_temperature = gauge(1228, 0.1, unit="°C")
    """R42, the highest water temperature the unit will make."""

    max_water_temperature_low_ambient = gauge(1229, 0.1, unit="°C")
    """R43, the cap on the water temperature at low outdoor temperatures. The
    manual does not give the outdoor temperature where it applies;
    ``Status.limited_target_temperature`` shows when it does."""

    max_water_temperature_high_ambient = gauge(1230, 0.1, unit="°C")
    """R44, the cap on the water temperature at high outdoor temperatures."""

    weather_compensation_slope = gauge(1234, 0.1, signed=False)
    """The weather compensation curve's slope (0 to 3.5)."""

    weather_compensation_offset = gauge(1235, 0.1, unit="°C")
    """The weather compensation curve's offset."""

    weather_compensation_enabled = boolean(1236)
    """Whether weather compensation adjusts the heating target. See
    ``Status.compensated_heating_target_temperature`` for the result."""
