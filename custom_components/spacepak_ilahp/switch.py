# Written by Claude, guided by Chris.
"""Switch platform for the SpacePak ILAHP integration -- master power only."""
from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import IlahpCoordinator
from .entity import IlahpEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: IlahpCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([PowerSwitch(coordinator, entry)])


class PowerSwitch(IlahpEntity, SwitchEntity):
    _attr_translation_key = "power"

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_power"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.power_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        await self.coordinator.data.write("power_on", True)
        await self.coordinator.async_request_refresh()

    async def async_turn_off(self, **kwargs: Any) -> None:
        await self.coordinator.data.write("power_on", False)
        await self.coordinator.async_request_refresh()
