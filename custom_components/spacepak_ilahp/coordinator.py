# Written by Claude, guided by Chris.
"""DataUpdateCoordinator for the SpacePak ILAHP integration."""
from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from modbus_connection import ModbusConnectionError, ModbusTcpParams
from modbus_connection.pymodbus import ModbusConnection

from .const import DEFAULT_SCAN_INTERVAL
from .device import IlahpHeatPump

_LOGGER = logging.getLogger(__name__)


class IlahpCoordinator(DataUpdateCoordinator[IlahpHeatPump]):
    """Owns the Modbus connection for one heat pump and polls it on an interval.

    Returns the live IlahpHeatPump instance itself (not a plain dataclass) --
    entities read its attributes directly and call .write() on it for
    setpoint/on-off changes, going back through this same connection.
    """

    def __init__(self, hass: HomeAssistant, host: str, port: int, unit_id: int) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"spacepak_ilahp_{host}_{port}",
            update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL),
        )
        self._connection = ModbusConnection(ModbusTcpParams(host=host, port=port))
        self.device = IlahpHeatPump(self._connection.for_unit(unit_id))

    async def _async_update_data(self) -> IlahpHeatPump:
        try:
            await self.device.async_update()
        except ModbusConnectionError as err:
            raise UpdateFailed(str(err)) from err
        return self.device

    async def async_close(self) -> None:
        await self._connection.close()
