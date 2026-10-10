"""The SpacePak ILAHP heat pump integration."""

# Written by Claude, guided by Chris.

from __future__ import annotations

from datetime import timedelta
import logging

from modbus_connection import ModbusTcpParams

from homeassistant.components.modbus import async_get_unit
from homeassistant.const import CONF_HOST, CONF_PORT, Platform
from homeassistant.core import HomeAssistant

from .const import CONF_UNIT_ID, SCAN_INTERVAL, SETTINGS_SCAN_INTERVAL
from .coordinator import SpacePakConfigEntry, SpacePakCoordinator, SpacePakRuntimeData
from .spacepak_modbus import IlahpHeatPump

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [
    Platform.BINARY_SENSOR,
    Platform.NUMBER,
    Platform.SENSOR,
    Platform.SWITCH,
]


def unique_id_for(host: str, port: int, unit_id: int) -> str:
    """Return the config entry unique ID for one unit behind one gateway port."""
    return f"{host}:{port}:{unit_id}"


async def async_setup_entry(hass: HomeAssistant, entry: SpacePakConfigEntry) -> bool:
    """Set up a SpacePak ILAHP heat pump from a config entry."""
    unit = async_get_unit(
        hass,
        entry,
        ModbusTcpParams(host=entry.data[CONF_HOST], port=entry.data[CONF_PORT]),
        entry.data[CONF_UNIT_ID],
    )
    device = IlahpHeatPump(unit)

    readings = SpacePakCoordinator(
        hass,
        entry,
        device,
        device.async_update_readings,
        timedelta(seconds=SCAN_INTERVAL),
    )
    settings = SpacePakCoordinator(
        hass,
        entry,
        device,
        device.async_update_settings,
        timedelta(seconds=SETTINGS_SCAN_INTERVAL),
    )
    await readings.async_config_entry_first_refresh()
    await settings.async_config_entry_first_refresh()

    entry.runtime_data = SpacePakRuntimeData(readings, settings)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: SpacePakConfigEntry) -> bool:
    """Unload a config entry."""
    return await hass.config_entries.async_unload_platforms(entry, PLATFORMS)


async def async_migrate_entry(hass: HomeAssistant, entry: SpacePakConfigEntry) -> bool:
    """Migrate an old config entry."""
    if entry.version > 1:
        return False
    if entry.minor_version < 2:
        # 1.1 keyed the entry on host:port alone, so two units sharing one
        # gateway port under different unit IDs collided.
        hass.config_entries.async_update_entry(
            entry,
            unique_id=unique_id_for(
                entry.data[CONF_HOST], entry.data[CONF_PORT], entry.data[CONF_UNIT_ID]
            ),
            minor_version=2,
        )
        _LOGGER.debug("Migrated %s to version 1.2", entry.title)
    return True
