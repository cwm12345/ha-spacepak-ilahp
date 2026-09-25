# Written by Claude, guided by Chris.
"""Temperatures, electrical readings, compressor speed and water flow."""

from __future__ import annotations

from modbus_connection.model import Component, gauge, integer

__all__ = ["Measurements"]


class Measurements(Component):
    """The unit's live sensor readings.

    Temperatures are signed tenths of a degree Celsius. Currents, voltages
    and frequencies are unsigned. The manual lists T09 (room temperature, 2058)
    and T39 (water flow, 2077) as not used on this unit, so they are left out.
    """

    compressor_current = gauge(2042, 0.1, signed=False, unit="A")
    """T36."""

    dc_bus_voltage = integer(2043, signed=False, unit="V")
    """T37, the inverter's DC line voltage."""

    inlet_temperature = gauge(2045, 0.1, unit="°C")
    """T01, water entering the unit."""

    outlet_temperature = gauge(2046, 0.1, unit="°C")
    """T02, water leaving the unit."""

    hot_water_tank_temperature = gauge(2047, 0.1, unit="°C")
    """T08. Only wired when the unit's hot water function is enabled; see
    ``Controls.hot_water_enabled``."""

    ambient_temperature = gauge(2048, 0.1, unit="°C")
    """T04, outdoor air."""

    coil_temperature = gauge(2049, 0.1, unit="°C")
    """T03, outdoor coil."""

    suction_temperature = gauge(2051, 0.1, unit="°C")
    """T05."""

    discharge_temperature = gauge(2053, 0.1, unit="°C")
    """T12."""

    ac_input_current = gauge(2057, 0.1, signed=False, unit="A")
    """T35."""

    ac_input_voltage = integer(2062, signed=False, unit="V")
    """T34."""

    compressor_frequency_target = integer(2071, signed=False, unit="Hz")
    """T30, the frequency the compressor is asked to run at."""

    compressor_frequency = integer(2072, signed=False, unit="Hz")
    """T31, the frequency the compressor is running at."""
