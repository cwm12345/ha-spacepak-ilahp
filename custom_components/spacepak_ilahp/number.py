# Written by Claude, guided by Chris.
"""Number platform for the SpacePak ILAHP integration -- writable setpoints.

These write directly to a live heat pump's target-temperature registers.
Bounded to MIN/MAX_TARGET_TEMP_C from const.py rather than left open-ended.
"""
from __future__ import annotations

from homeassistant.components.number import NumberDeviceClass, NumberEntity, NumberMode
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN, MAX_TARGET_TEMP_C, MIN_TARGET_TEMP_C
from .coordinator import IlahpCoordinator
from .entity import IlahpEntity


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: IlahpCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            HeatingTargetTempNumber(coordinator, entry),
            CoolingTargetTempNumber(coordinator, entry),
        ]
    )


class _TargetTempNumber(IlahpEntity, NumberEntity):
    _attr_device_class = NumberDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_native_min_value = MIN_TARGET_TEMP_C
    _attr_native_max_value = MAX_TARGET_TEMP_C
    _attr_native_step = 0.5
    _attr_mode = NumberMode.BOX


class HeatingTargetTempNumber(_TargetTempNumber):
    _attr_translation_key = "heating_target_temp"

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_heating_target_temp"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.heating_target_temp

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.data.write("heating_target_temp", value)
        await self.coordinator.async_request_refresh()


class CoolingTargetTempNumber(_TargetTempNumber):
    _attr_translation_key = "cooling_target_temp"

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_cooling_target_temp"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.cooling_target_temp

    async def async_set_native_value(self, value: float) -> None:
        await self.coordinator.data.write("cooling_target_temp", value)
        await self.coordinator.async_request_refresh()
