"""Binary sensors for SpacePak ILAHP heat pumps."""

# Written by Claude, guided by Chris.

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from spacepak_modbus import IlahpHeatPump, Outputs

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


def _output(*outputs: Outputs) -> Callable[[IlahpHeatPump], bool | None]:
    """Read whether any of the given load outputs is energized."""

    def value(device: IlahpHeatPump) -> bool | None:
        energized = device.status.outputs
        return None if energized is None else any(o in energized for o in outputs)

    return value


def _output_sensor(
    key: str, *outputs: Outputs, running: bool = True
) -> SpacePakBinarySensorDescription:
    return SpacePakBinarySensorDescription(
        key=key,
        translation_key=key,
        component="status",
        device_class=BinarySensorDeviceClass.RUNNING if running else None,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=_output(*outputs),
    )


def _input_sensor(
    key: str,
    value_fn: Callable[[IlahpHeatPump], bool | None],
    *,
    diagnostic: bool = False,
) -> SpacePakBinarySensorDescription:
    """Describe a field switch input; on means the contact is closed."""
    return SpacePakBinarySensorDescription(
        key=key,
        translation_key=key,
        component="status",
        entity_category=EntityCategory.DIAGNOSTIC if diagnostic else None,
        value_fn=value_fn,
    )


def _setting_sensor(
    key: str, component: str, value_fn: Callable[[IlahpHeatPump], bool | None]
) -> SpacePakBinarySensorDescription:
    """Describe an on/off installer parameter."""
    return SpacePakBinarySensorDescription(
        key=key,
        translation_key=key,
        component=component,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=value_fn,
    )


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
    _output_sensor("water_pump", Outputs.WATER_PUMP),
    _output_sensor("fan", Outputs.FAN_HIGH_SPEED, Outputs.FAN_LOW_SPEED),
    _output_sensor("reversing_valve", Outputs.FOUR_WAY_VALVE, running=False),
    _output_sensor("electric_heater_1", Outputs.ELECTRIC_HEATER_1),
    _output_sensor("electric_heater_2", Outputs.ELECTRIC_HEATER_2),
    _output_sensor("crankcase_heater", Outputs.CRANKCASE_HEATER),
    _input_sensor("remote_on_off", lambda d: d.status.remote_on_off_closed),
    _input_sensor("heat_cool_on_off", lambda d: d.status.heat_cool_on_off_closed),
    _input_sensor("remote_heat_selected", lambda d: d.status.heat_selected),
    _input_sensor(
        "flow_switch", lambda d: d.status.flow_switch_closed, diagnostic=True
    ),
    _setting_sensor(
        "weather_compensation",
        "tuning",
        lambda d: d.tuning.weather_compensation_enabled,
    ),
    _setting_sensor(
        "cooling_enabled", "controls", lambda d: d.controls.cooling_enabled
    ),
    _setting_sensor(
        "field_wired_control", "controls", lambda d: d.controls.field_wired_control
    ),
    _setting_sensor("silence_mode", "controls", lambda d: d.controls.silence_mode),
    _setting_sensor("auto_restart", "controls", lambda d: d.controls.auto_restart),
    _setting_sensor(
        "display_fahrenheit", "controls", lambda d: d.controls.display_fahrenheit
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
