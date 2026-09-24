# Written by Claude, guided by Chris.
"""The top-level object for a SpacePak ILAHP heat pump."""

from __future__ import annotations

from collections.abc import Iterable
from typing import TYPE_CHECKING

from modbus_connection.model import Device, Raw, UpdateReport

from .controls import Controls
from .faults import Faults
from .measurements import Measurements
from .status import Status

if TYPE_CHECKING:
    from modbus_connection import ModbusUnit

__all__ = ["READINGS", "SETTINGS", "IlahpHeatPump"]

READINGS: tuple[str, ...] = ("status", "measurements", "faults")
"""Components that change on their own: what the unit measures and reports."""

SETTINGS: tuple[str, ...] = ("controls",)
"""Components that change when something writes them."""


class IlahpHeatPump(Device):
    """A SpacePak Solstice Inverter Extreme (ILAHP) air-to-water heat pump.

    Hand it a ``ModbusUnit``; it owns no connection. The unit answers Modbus
    RTU at 9600 8N1 on its RS-485 port, usually reached through a gateway.
    """

    def __init__(self, unit: ModbusUnit) -> None:
        super().__init__(unit)
        self.controls = Controls(unit)
        self.status = Status(unit)
        self.measurements = Measurements(unit)
        self.faults = Faults(unit)

    async def async_update_readings(self) -> UpdateReport:
        """Refresh status, measurements and faults."""
        return await self.async_poll(READINGS)

    async def async_update_settings(self) -> UpdateReport:
        """Refresh power, mode and setpoints. Run one after a write."""
        return await self.async_poll(SETTINGS)

    async def async_update(self) -> UpdateReport:
        """Refresh everything in one report."""
        return await self.async_poll((*READINGS, *SETTINGS))

    async def async_read_raw(self, names: Iterable[str] | None = None) -> Raw:
        """Every register this heat pump reads, undecoded, for diagnostics."""
        return await super().async_read_raw(
            (*READINGS, *SETTINGS) if names is None else names
        )
