"""Sensors for SpacePak ILAHP heat pumps."""

# Written by Claude, guided by Chris.

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from spacepak_modbus import IlahpHeatPump, OperatingMode, PumpMode, UnitMode

from homeassistant.components.sensor import (
    RestoreSensor,
    SensorDeviceClass,
    SensorEntity,
    SensorEntityDescription,
    SensorStateClass,
)
from homeassistant.const import (
    EntityCategory,
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback
from homeassistant.helpers.typing import StateType

from .coordinator import SpacePakConfigEntry
from .entity import SpacePakEntity, SpacePakEntityDescription

PARALLEL_UPDATES = 0


@dataclass(frozen=True, kw_only=True)
class SpacePakSensorDescription(SensorEntityDescription, SpacePakEntityDescription):
    """Describe a SpacePak sensor."""

    value_fn: Callable[[IlahpHeatPump], StateType]
    exists_fn: Callable[[IlahpHeatPump], bool] = lambda _: True


def _temperature(
    key: str,
    value_fn: Callable[[IlahpHeatPump], StateType],
    *,
    diagnostic: bool = False,
) -> SpacePakSensorDescription:
    return SpacePakSensorDescription(
        key=key,
        translation_key=key,
        component="measurements",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC if diagnostic else None,
        value_fn=value_fn,
    )


def _setting(
    key: str,
    value_fn: Callable[[IlahpHeatPump], StateType],
    *,
    device_class: SensorDeviceClass | None = SensorDeviceClass.TEMPERATURE,
    unit: str | None = UnitOfTemperature.CELSIUS,
) -> SpacePakSensorDescription:
    """Describe a read-only installer parameter."""
    return SpacePakSensorDescription(
        key=key,
        translation_key=key,
        component="tuning",
        device_class=device_class,
        native_unit_of_measurement=unit,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=value_fn,
    )


def _difference(
    key: str, value_fn: Callable[[IlahpHeatPump], StateType]
) -> SpacePakSensorDescription:
    """Describe a temperature differential.

    Kelvin with no device class, so it is never converted as if it were an
    absolute temperature.
    """
    return _setting(key, value_fn, device_class=None, unit=UnitOfTemperature.KELVIN)


def _enum_name(value: OperatingMode | UnitMode | PumpMode | None) -> str | None:
    return None if value is None else value.name.lower()


def _compensated_target(device: IlahpHeatPump) -> StateType:
    """Return the weather-compensated target, only while compensation is on.

    With it off the register reads 0 on some units, which is not a target.
    """
    if not device.tuning.weather_compensation_enabled:
        return None
    return device.status.compensated_heating_target_temperature


# Keys are part of each entity's unique ID; keep them stable.
SENSOR_DESCRIPTIONS: tuple[SpacePakSensorDescription, ...] = (
    _temperature("outlet_temp", lambda d: d.measurements.outlet_temperature),
    _temperature("inlet_temp", lambda d: d.measurements.inlet_temperature),
    _temperature("ambient_temp", lambda d: d.measurements.ambient_temperature),
    SpacePakSensorDescription(
        key="dhw_tank_temp",
        translation_key="dhw_tank_temp",
        component="measurements",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.measurements.hot_water_tank_temperature,
        # The tank sensor is only wired when the unit's hot water function is on.
        exists_fn=lambda d: bool(d.controls.hot_water_enabled),
    ),
    _temperature(
        "coil_temp", lambda d: d.measurements.coil_temperature, diagnostic=True
    ),
    _temperature(
        "suction_temp", lambda d: d.measurements.suction_temperature, diagnostic=True
    ),
    _temperature(
        "discharge_temp",
        lambda d: d.measurements.discharge_temperature,
        diagnostic=True,
    ),
    SpacePakSensorDescription(
        key="ac_current",
        translation_key="ac_current",
        component="measurements",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.measurements.ac_input_current,
    ),
    SpacePakSensorDescription(
        key="compressor_current",
        translation_key="compressor_current",
        component="measurements",
        device_class=SensorDeviceClass.CURRENT,
        native_unit_of_measurement=UnitOfElectricCurrent.AMPERE,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.measurements.compressor_current,
    ),
    SpacePakSensorDescription(
        key="ac_input_voltage",
        translation_key="ac_input_voltage",
        component="measurements",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.measurements.ac_input_voltage,
    ),
    SpacePakSensorDescription(
        key="dc_line_voltage",
        translation_key="dc_line_voltage",
        component="measurements",
        device_class=SensorDeviceClass.VOLTAGE,
        native_unit_of_measurement=UnitOfElectricPotential.VOLT,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.measurements.dc_bus_voltage,
    ),
    SpacePakSensorDescription(
        key="compressor_freq_running",
        translation_key="compressor_freq_running",
        component="measurements",
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
        value_fn=lambda d: d.measurements.compressor_frequency,
    ),
    SpacePakSensorDescription(
        key="compressor_freq_setting",
        translation_key="compressor_freq_setting",
        component="measurements",
        device_class=SensorDeviceClass.FREQUENCY,
        native_unit_of_measurement=UnitOfFrequency.HERTZ,
        state_class=SensorStateClass.MEASUREMENT,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.measurements.compressor_frequency_target,
    ),
    SpacePakSensorDescription(
        key="unit_mode",
        translation_key="unit_mode",
        component="status",
        device_class=SensorDeviceClass.ENUM,
        options=[mode.name.lower() for mode in UnitMode],
        value_fn=lambda d: _enum_name(d.status.unit_mode),
    ),
    SpacePakSensorDescription(
        key="operating_mode",
        translation_key="operating_mode",
        component="controls",
        device_class=SensorDeviceClass.ENUM,
        options=[mode.name.lower() for mode in OperatingMode],
        value_fn=lambda d: _enum_name(d.controls.operating_mode),
    ),
    SpacePakSensorDescription(
        key="limited_target_temp",
        translation_key="limited_target_temp",
        component="status",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=lambda d: d.status.limited_target_temperature,
    ),
    SpacePakSensorDescription(
        key="compensated_heating_target_temp",
        translation_key="compensated_heating_target_temp",
        component="status",
        device_class=SensorDeviceClass.TEMPERATURE,
        native_unit_of_measurement=UnitOfTemperature.CELSIUS,
        value_fn=_compensated_target,
    ),
    _setting("shutdown_ambient_temp", lambda d: d.tuning.shutdown_ambient_temperature),
    _setting(
        "heating_restart_ambient_temp",
        lambda d: d.tuning.heating_restart_ambient_temperature,
    ),
    _difference(
        "heating_restart_difference", lambda d: d.tuning.heating_restart_difference
    ),
    _difference("heating_stop_difference", lambda d: d.tuning.heating_stop_difference),
    _difference(
        "cooling_restart_difference", lambda d: d.tuning.cooling_restart_difference
    ),
    _difference("cooling_stop_difference", lambda d: d.tuning.cooling_stop_difference),
    _setting(
        "low_ambient_compensation_start",
        lambda d: d.tuning.low_ambient_compensation_start,
    ),
    _setting(
        "low_ambient_compensation_end", lambda d: d.tuning.low_ambient_compensation_end
    ),
    _setting(
        "low_ambient_heating_target", lambda d: d.tuning.low_ambient_heating_target
    ),
    _setting(
        "weather_compensation_slope",
        lambda d: d.tuning.weather_compensation_slope,
        device_class=None,
        unit=None,
    ),
    _setting(
        "weather_compensation_offset", lambda d: d.tuning.weather_compensation_offset
    ),
    SpacePakSensorDescription(
        key="pump_mode",
        translation_key="pump_mode",
        component="tuning",
        device_class=SensorDeviceClass.ENUM,
        options=[mode.name.lower() for mode in PumpMode],
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: _enum_name(d.tuning.pump_mode),
    ),
    _setting(
        "pump_interval",
        lambda d: d.tuning.pump_interval,
        device_class=SensorDeviceClass.DURATION,
        unit=UnitOfTime.MINUTES,
    ),
    _setting(
        "pump_run_time",
        lambda d: d.tuning.pump_run_time,
        device_class=SensorDeviceClass.DURATION,
        unit=UnitOfTime.MINUTES,
    ),
    _setting(
        "compressor_min_freq",
        lambda d: d.tuning.compressor_min_frequency,
        device_class=SensorDeviceClass.FREQUENCY,
        unit=UnitOfFrequency.HERTZ,
    ),
    _setting(
        "compressor_max_freq",
        lambda d: d.tuning.compressor_max_frequency,
        device_class=SensorDeviceClass.FREQUENCY,
        unit=UnitOfFrequency.HERTZ,
    ),
    SpacePakSensorDescription(
        key="compressor_runtime",
        translation_key="compressor_runtime",
        component="status",
        device_class=SensorDeviceClass.DURATION,
        native_unit_of_measurement=UnitOfTime.HOURS,
        state_class=SensorStateClass.TOTAL_INCREASING,
        entity_category=EntityCategory.DIAGNOSTIC,
        value_fn=lambda d: d.status.compressor_hours,
    ),
    SpacePakSensorDescription(
        key="output_relays_raw",
        translation_key="output_relays_raw",
        component="status",
        entity_category=EntityCategory.DIAGNOSTIC,
        entity_registry_enabled_default=False,
        value_fn=lambda d: None if d.status.outputs is None else int(d.status.outputs),
    ),
    *(
        SpacePakSensorDescription(
            key=f"failure_{register}_raw",
            translation_key="failure_raw",
            translation_placeholders={"register": str(register)},
            component="faults",
            entity_category=EntityCategory.DIAGNOSTIC,
            entity_registry_enabled_default=False,
            value_fn=lambda d, register=register: d.faults.failure(register),
        )
        for register in range(1, 10)
    ),
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SpacePakConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up SpacePak sensors."""
    async_add_entities(
        (
            SpacePakTotalSensor
            if description.state_class is SensorStateClass.TOTAL_INCREASING
            else SpacePakSensor
        )(entry, description)
        for description in SENSOR_DESCRIPTIONS
        if description.exists_fn(entry.runtime_data.device)
    )


class SpacePakSensor(SpacePakEntity, SensorEntity):
    """A heat pump reading."""

    entity_description: SpacePakSensorDescription

    @property
    def native_value(self) -> StateType:
        """The value from the latest poll."""
        return self.entity_description.value_fn(self.coordinator.device)


class SpacePakTotalSensor(SpacePakEntity, RestoreSensor):
    """A running total that keeps its last value while the unit is unreachable."""

    entity_description: SpacePakSensorDescription

    @property
    def available(self) -> bool:
        """Always available, so long-term statistics keep their history."""
        return True

    async def async_added_to_hass(self) -> None:
        """Restore the last value, then take the current one if there is one."""
        await super().async_added_to_hass()
        if (last := await self.async_get_last_sensor_data()) is not None:
            self._attr_native_value = last.native_value
        self._process_data()

    @callback
    def _handle_coordinator_update(self) -> None:
        self._process_data()
        super()._handle_coordinator_update()

    def _process_data(self) -> None:
        if self.entity_description.component in self.coordinator.data.failed:
            return
        value = self.entity_description.value_fn(self.coordinator.device)
        if value is not None:
            self._attr_native_value = value
