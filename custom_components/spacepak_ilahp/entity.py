# Written by Claude, guided by Chris.
"""Shared entity base for the SpacePak ILAHP integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, MANUFACTURER, MODEL
from .coordinator import IlahpCoordinator


class IlahpEntity(CoordinatorEntity[IlahpCoordinator]):
    """Base class -- every entity type shares the same device_info."""

    _attr_has_entity_name = True

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name=entry.title,
            manufacturer=MANUFACTURER,
            model=MODEL,
        )
