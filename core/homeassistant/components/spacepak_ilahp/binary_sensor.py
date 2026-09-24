"""Binary sensors for SpacePak ILAHP heat pumps."""

# Written by Claude, guided by Chris.

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from spacepak_modbus import IlahpHeatPump

from homeassistant.components.binary_sensor import (
    BinarySensorDeviceClass,
    BinarySensorEntity,
    BinarySensorEntityDescription,
)
from homeassistant.const import EntityCategory
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .coordinator import SpacePakConfigEntry
from .entity import SpacePakEntity, SpacePakEntityDescription

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class SpacePakBinarySensorDescription(
    BinarySensorEntityDescription, SpacePakEntityDescription
):
    """Describe a SpacePak binary sensor."""

    value_fn: Callable[[IlahpHeatPump], bool | None]


BINARY_SENSOR_DESCRIPTIONS: tuple[SpacePakBinarySensorDescription, ...] = (
    SpacePakBinarySensorDescription(
        key="unit_running",
        translation_key="unit_running",
        component="status",
        device_class=BinarySensorDeviceClass.RUNNING,
        value_fn=lambda d: d.status.running,
    ),
    SpacePakBinarySensorDescription(
        key="compressor_on",
        translation_key="compressor_on",
        component="status",
        device_class=BinarySensorDeviceClass.RUNNING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.status.compressor_on,
    ),
    SpacePakBinarySensorDescription(
        key="alarm_output",
        translation_key="alarm_output",
        component="status",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: d.status.alarm_on,
    ),
    SpacePakBinarySensorDescription(
        key="any_fault",
        translation_key="any_fault",
        component="faults",
        device_class=BinarySensorDeviceClass.PROBLEM,
        value_fn=lambda d: d.faults.any_fault,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SpacePakConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up SpacePak binary sensors."""
    async_add_entities(
        SpacePakBinarySensor(entry, description)
        for description in BINARY_SENSOR_DESCRIPTIONS
    )


class SpacePakBinarySensor(SpacePakEntity, BinarySensorEntity):
    """A heat pump on/off state."""

    entity_description: SpacePakBinarySensorDescription

    @property
    def is_on(self) -> bool | None:
        """The state from the latest poll."""
        return self.entity_description.value_fn(self.coordinator.device)
