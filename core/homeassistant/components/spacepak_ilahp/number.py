"""Water setpoints for SpacePak ILAHP heat pumps."""

# Written by Claude, guided by Chris.

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from modbus_connection import ModbusError
from spacepak_modbus import IlahpHeatPump

from homeassistant.components.number import (
    NumberDeviceClass,
    NumberEntity,
    NumberEntityDescription,
    NumberMode,
)
from homeassistant.const import UnitOfTemperature
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import (
    DEFAULT_MAX_COOLING_SETPOINT,
    DEFAULT_MAX_HEATING_SETPOINT,
    DEFAULT_MIN_COOLING_SETPOINT,
    DEFAULT_MIN_HEATING_SETPOINT,
    DOMAIN,
)
from .coordinator import SpacePakConfigEntry
from .entity import SpacePakEntity, SpacePakEntityDescription

PARALLEL_UPDATES = 1


@dataclass(frozen=True, kw_only=True)
class SpacePakNumberDescription(NumberEntityDescription, SpacePakEntityDescription):
    """Describe a SpacePak setpoint."""

    field: str
    """The Controls field this number writes."""
    value_fn: Callable[[IlahpHeatPump], float | None]
    min_fn: Callable[[IlahpHeatPump], float | None]
    max_fn: Callable[[IlahpHeatPump], float | None]
    default_min: float
    default_max: float


NUMBER_DESCRIPTIONS: tuple[SpacePakNumberDescription, ...] = (
    SpacePakNumberDescription(
        key="heating_target_temp",
        translation_key="heating_target_temp",
        component="controls",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_step=0.5,
        mode=NumberMode.BOX,
        field="heating_target_temperature",
        value_fn=lambda d: d.controls.heating_target_temperature,
        min_fn=lambda d: d.controls.min_heating_setpoint,
        max_fn=lambda d: d.controls.max_heating_setpoint,
        default_min=DEFAULT_MIN_HEATING_SETPOINT,
        default_max=DEFAULT_MAX_HEATING_SETPOINT,
    ),
    SpacePakNumberDescription(
        key="cooling_target_temp",
        translation_key="cooling_target_temp",
        component="controls",
        device_class=NumberDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        native_step=0.5,
        mode=NumberMode.BOX,
        field="cooling_target_temperature",
        value_fn=lambda d: d.controls.cooling_target_temperature,
        min_fn=lambda d: d.controls.min_cooling_setpoint,
        max_fn=lambda d: d.controls.max_cooling_setpoint,
        default_min=DEFAULT_MIN_COOLING_SETPOINT,
        default_max=DEFAULT_MAX_COOLING_SETPOINT,
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SpacePakConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up SpacePak setpoints."""
    async_add_entities(
        SpacePakNumber(entry, description) for description in NUMBER_DESCRIPTIONS
    )


class SpacePakNumber(SpacePakEntity, NumberEntity):
    """A water setpoint, bounded by the unit's own configured limits."""

    entity_description: SpacePakNumberDescription

    @property
    def native_value(self) -> float | None:
        """The setpoint from the latest poll."""
        return self.entity_description.value_fn(self.coordinator.device)

    @property
    def native_min_value(self) -> float:
        """The lowest setpoint the unit accepts."""
        value = self.entity_description.min_fn(self.coordinator.device)
        return self.entity_description.default_min if value is None else value

    @property
    def native_max_value(self) -> float:
        """The highest setpoint the unit accepts."""
        value = self.entity_description.max_fn(self.coordinator.device)
        return self.entity_description.default_max if value is None else value

    async def async_set_native_value(self, value: float) -> None:
        """Write a new setpoint and read it back."""
        try:
            await self.coordinator.device.controls.write(
                self.entity_description.field, value
            )
        except (ModbusError, ValueError) as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="write_failed",
                translation_placeholders={"error": str(err) or type(err).__name__},
            ) from err
        await self.coordinator.async_request_refresh()
