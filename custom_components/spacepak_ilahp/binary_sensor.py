# Written by Claude, guided by Chris.
"""Binary sensor platform for the SpacePak ILAHP integration."""
from __future__ import annotations

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import IlahpCoordinator
from .entity import IlahpEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: IlahpCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            UnitRunningSensor(coordinator, entry),
            CompressorOnSensor(coordinator, entry),
            AlarmOutputSensor(coordinator, entry),
            AnyFaultSensor(coordinator, entry),
        ]
    )


class UnitRunningSensor(IlahpEntity, BinarySensorEntity):
    _attr_translation_key = "unit_running"
    _attr_device_class = BinarySensorDeviceClass.RUNNING

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_unit_running"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.unit_running


# -- 2026-09-19 expansion --


class CompressorOnSensor(IlahpEntity, BinarySensorEntity):
    """Output relay bit0 (O01), decoded from register 2019 -- see
    device.py's module docstring for the "Load %" mislabeling this
    register was previously used for."""

    _attr_translation_key = "compressor_on"
    _attr_device_class = BinarySensorDeviceClass.RUNNING
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_compressor_on"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.compressor_on


class AlarmOutputSensor(IlahpEntity, BinarySensorEntity):
    """Output relay bit10 (O11 alarm output), decoded from register 2019.
    Polarity per the manual's own labeling (0=OFF/1=ON for the physical
    alarm relay) -- not independently live-tested against a real fault."""

    _attr_translation_key = "alarm_output"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_alarm_output"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.alarm_output


class AnyFaultSensor(IlahpEntity, BinarySensorEntity):
    """True if any of the 9 raw Failure registers (2081-2090) is nonzero.
    Deliberately not narrowed to "which fault" -- see device.py."""

    _attr_translation_key = "any_fault"
    _attr_device_class = BinarySensorDeviceClass.PROBLEM

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_any_fault"

    @property
    def is_on(self) -> bool:
        return self.coordinator.data.any_fault
