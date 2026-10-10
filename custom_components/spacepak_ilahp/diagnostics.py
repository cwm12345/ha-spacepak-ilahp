"""Diagnostics for SpacePak ILAHP heat pumps."""

# Written by Claude, guided by Chris.

from __future__ import annotations

from typing import Any

from modbus_connection import ModbusError

from homeassistant.core import HomeAssistant

from .coordinator import SpacePakConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: SpacePakConfigEntry
) -> dict[str, Any]:
    """Return the raw register map and the latest poll's outcome.

    The unit holds no serial number or other personal information, so nothing
    needs redacting from the registers. The gateway address is left out.
    """
    runtime = entry.runtime_data
    device = runtime.device
    try:
        registers: dict[str, Any] = await device.async_read_raw()
    except ModbusError as err:
        registers = {"error": str(err) or type(err).__name__}
    return {
        "readings": {
            "updated": sorted(runtime.readings.data.updated),
            "failed": {k: str(v) for k, v in runtime.readings.data.failed.items()},
        },
        "settings": {
            "updated": sorted(runtime.settings.data.updated),
            "failed": {k: str(v) for k, v in runtime.settings.data.failed.items()},
        },
        "active_faults": [fault.key for fault in device.faults.active_faults],
        "registers": registers,
    }
