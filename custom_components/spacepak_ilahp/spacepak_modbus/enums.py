# Written by Claude, guided by Chris.
"""The coded values the heat pump reports, as enums and bit flags."""

from __future__ import annotations

from enum import IntEnum, IntFlag

__all__ = ["OpenInputs", "OperatingMode", "Outputs", "PumpMode", "UnitMode"]


class OperatingMode(IntEnum):
    """The mode the unit is set to run in (register 1012).

    With cooling disabled (installer parameter H05 = 0) the unit only accepts
    ``HOT_WATER``, ``HEATING`` and ``HOT_WATER_AND_HEATING``.
    """

    HOT_WATER = 0
    HEATING = 1
    COOLING = 2
    HOT_WATER_AND_HEATING = 3
    HOT_WATER_AND_COOLING = 4


class UnitMode(IntEnum):
    """What the unit is doing right now (register 2012)."""

    COOLING = 0
    HEATING = 1
    DEFROST = 2
    STERILIZE = 3
    HOT_WATER = 4


class PumpMode(IntEnum):
    """How the water pump runs while the unit is idle (P01, register 1197)."""

    NORMAL = 0
    """Runs continuously."""
    ECONOMIC = 1
    """Runs only around compressor operation."""
    INTERVAL = 2
    """Also runs for P03 minutes every P02 minutes while idle."""


class OpenInputs(IntFlag):
    """The field switch inputs that are open (register 2034, S01-S10).

    A set bit means that input's contact is open; clear means closed. The
    touchscreen shows the heating/cooling on/off input as S10.
    """

    HIGH_PRESSURE = 1 << 0
    """S01 high-pressure switch (closed in normal operation)."""
    LOW_PRESSURE = 1 << 1
    """S02 low-pressure switch (closed in normal operation)."""
    WATER_FLOW = 1 << 2
    """S03 water flow switch (closes once minimum flow is reached)."""
    HEATER_OVERHEAT = 1 << 3
    """S04 electric heater overheat switch."""
    REMOTE_ON_OFF = 1 << 4
    """S05 remote on/off, the master enable (must be closed to run)."""
    REMOTE_HEAT_COOL = 1 << 5
    """S06 remote heating/cooling select (closed = heat, open = cool)."""
    HOT_WATER = 1 << 6
    """S07 hot water enable."""
    HEAT_COOL_ON_OFF = 1 << 9
    """Heating/cooling on/off (S10 on the touchscreen)."""


class Outputs(IntFlag):
    """The load outputs the controller is driving (register 2019, O01-O23).

    Bit 1 is reserved and has no member; an unnamed bit is kept as-is.
    """

    COMPRESSOR = 1 << 0
    """O01 compressor."""
    FAN_HIGH_SPEED = 1 << 2
    """O03 fan, high speed."""
    FAN_LOW_SPEED = 1 << 3
    """O04 fan, low speed."""
    WATER_PUMP = 1 << 4
    """O05 water pump."""
    HOT_WATER_PUMP = 1 << 5
    """O06 hot water pump."""
    FOUR_WAY_VALVE = 1 << 6
    """O07 four-way (reversing) valve."""
    ELECTRIC_HEATER_1 = 1 << 7
    """O08 electric heater, stage 1."""
    ELECTRIC_HEATER_2 = 1 << 8
    """O09 electric heater, stage 2."""
    THREE_WAY_VALVE = 1 << 9
    """O10 three-way valve."""
    ALARM = 1 << 10
    """O11 alarm output."""
    CRANKCASE_HEATER = 1 << 11
    """O12 compressor crankcase heater."""
    PAN_HEATER = 1 << 12
    """O13 drain pan heater."""
    HEATING_WATER_PUMP = 1 << 13
    """O21 heating water pump."""
    LOOP_ELECTRIC_HEATER = 1 << 14
    """O22 hydraulic module water loop electric heater."""
    TANK_ELECTRIC_HEATER = 1 << 15
    """O23 hydraulic module hot water tank electric heater."""
