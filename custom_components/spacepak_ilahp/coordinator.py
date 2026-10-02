"""Data update coordinator for SpacePak ILAHP heat pumps."""

# Written by Claude, guided by Chris.

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import timedelta
import logging

from modbus_connection import ModbusError
from modbus_connection.model import UpdateReport

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, MANUFACTURER, MODEL
from .spacepak_modbus import SETTINGS, IlahpHeatPump

_LOGGER = logging.getLogger(__name__)


@dataclass
class SpacePakRuntimeData:
    """The two coordinators polling one heat pump."""

    readings: SpacePakCoordinator
    settings: SpacePakCoordinator

    @property
    def device(self) -> IlahpHeatPump:
        """Return the heat pump both coordinators read."""
        return self.readings.device

    def coordinator_for(self, component: str) -> SpacePakCoordinator:
        """Return the coordinator that polls a component."""
        return self.settings if component in SETTINGS else self.readings


type SpacePakConfigEntry = ConfigEntry[SpacePakRuntimeData]


class SpacePakCoordinator(DataUpdateCoordinator[UpdateReport]):
    """Run one of the heat pump's update methods on its own interval."""

    config_entry: SpacePakConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        entry: SpacePakConfigEntry,
        device: IlahpHeatPump,
        poll: Callable[[], Awaitable[UpdateReport]],
        interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            config_entry=entry,
            name=entry.title,
            update_interval=interval,
        )
        self.device = device
        self._poll = poll
        self._failed: frozenset[str] = frozenset()
        # The unit has no serial number register; the config entry is its identity.
        self.device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )

    async def _async_update_data(self) -> UpdateReport:
        try:
            report = await self._poll()
        except ModbusError as err:
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="modbus_error",
                translation_placeholders={"error": str(err) or type(err).__name__},
            ) from err
        if not report.updated:
            errors = list(report.failed.values())
            raise UpdateFailed(
                translation_domain=DOMAIN,
                translation_key="no_component_answered",
            ) from ExceptionGroup("every component failed to refresh", errors)

        for name in sorted(report.failed.keys() - self._failed):
            _LOGGER.warning(
                "%s: %s failed to refresh: %s", self.name, name, report.failed[name]
            )
        for name in sorted(self._failed - report.failed.keys()):
            _LOGGER.info("%s: %s is available again", self.name, name)
        self._failed = frozenset(report.failed)
        return report
