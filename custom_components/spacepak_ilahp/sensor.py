# Written by Claude, guided by Chris.
"""Read-only telemetry sensors for the SpacePak ILAHP integration."""
from __future__ import annotations

from homeassistant.components.sensor import (
    SensorDeviceClass,
    SensorEntity,
    SensorStateClass,
)
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import (
    UnitOfElectricCurrent,
    UnitOfElectricPotential,
    UnitOfFrequency,
    UnitOfTemperature,
    UnitOfTime,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import DOMAIN
from .coordinator import IlahpCoordinator
from .entity import IlahpEntity

# Register 2012's documented values -- see device.py's REG_UNIT_MODE.
_UNIT_MODE_TEXT = {0: "cooling", 1: "heating", 2: "defrost", 3: "sterilize", 4: "hot_water"}


async def async_setup_entry(
    hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback
) -> None:
    coordinator: IlahpCoordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities(
        [
            OutletTempSensor(coordinator, entry),
            AmbientTempSensor(coordinator, entry),
            AcCurrentSensor(coordinator, entry),
            ModeRawSensor(coordinator, entry),
            # -- 2026-09-19 expansion --
            UnitModeSensor(coordinator, entry),
            InletTempSensor(coordinator, entry),
            DhwTankTempSensor(coordinator, entry),
            CoilTempSensor(coordinator, entry),
            SuctionTempSensor(coordinator, entry),
            DischargeTempSensor(coordinator, entry),
            RoomTempSensor(coordinator, entry),
            CompressorCurrentSensor(coordinator, entry),
            CompressorRuntimeSensor(coordinator, entry),
            DcLineVoltageSensor(coordinator, entry),
            AcInputVoltageSensor(coordinator, entry),
            CompressorFreqSettingSensor(coordinator, entry),
            CompressorFreqRunningSensor(coordinator, entry),
            WaterFlowSensor(coordinator, entry),
            OutputRelaysRawSensor(coordinator, entry),
            SwitchStatesRawSensor(coordinator, entry),
            Failure1Sensor(coordinator, entry),
            Failure2Sensor(coordinator, entry),
            Failure3Sensor(coordinator, entry),
            Failure4Sensor(coordinator, entry),
            Failure5Sensor(coordinator, entry),
            Failure6Sensor(coordinator, entry),
            Failure7Sensor(coordinator, entry),
            Failure8Sensor(coordinator, entry),
            Failure9Sensor(coordinator, entry),
        ]
    )


class _IlahpSensor(IlahpEntity, SensorEntity):
    _attr_state_class = SensorStateClass.MEASUREMENT


class OutletTempSensor(_IlahpSensor):
    _attr_translation_key = "outlet_temp"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_outlet_temp"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.outlet_temp


class AmbientTempSensor(_IlahpSensor):
    _attr_translation_key = "ambient_temp"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_ambient_temp"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.ambient_temp


class AcCurrentSensor(_IlahpSensor):
    _attr_translation_key = "ac_current"
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_ac_current"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.ac_current


# LoadPercentSensor ("Load %", register 2019) retired 2026-09-19 by
# Claude, guided by Chris -- see device.py's module docstring. Superseded
# by OutputRelaysRawSensor below, the same register under its correct
# identity.


class ModeRawSensor(_IlahpSensor):
    """Diagnostic only -- the mode register's integer-to-mode mapping was
    never confirmed this session (see device.py). Exposed as a raw number
    so it's visible/loggable, not hidden, but deliberately not a `select`
    entity until that mapping is verified -- writing a guessed value to a
    live unit's mode register is not a place to guess."""

    _attr_translation_key = "mode_raw"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = None

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_mode_raw"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.mode_raw


# -- 2026-09-19 expansion: additional read-only telemetry --


class UnitModeSensor(_IlahpSensor):
    """Register 2012 -- the unit's *actual current* operating mode, read-only
    status (distinct from register 1012's mode *setting*)."""

    _attr_translation_key = "unit_mode"
    _attr_device_class = SensorDeviceClass.ENUM
    _attr_options = list(_UNIT_MODE_TEXT.values())
    _attr_state_class = None

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_unit_mode"

    @property
    def native_value(self) -> str | None:
        return _UNIT_MODE_TEXT.get(self.coordinator.data.unit_mode_raw)


class InletTempSensor(_IlahpSensor):
    _attr_translation_key = "inlet_temp"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_inlet_temp"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.inlet_temp


class DhwTankTempSensor(_IlahpSensor):
    _attr_translation_key = "dhw_tank_temp"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_dhw_tank_temp"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.dhw_tank_temp


class CoilTempSensor(_IlahpSensor):
    _attr_translation_key = "coil_temp"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_coil_temp"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.coil_temp


class SuctionTempSensor(_IlahpSensor):
    _attr_translation_key = "suction_temp"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_suction_temp"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.suction_temp


class DischargeTempSensor(_IlahpSensor):
    _attr_translation_key = "discharge_temp"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_discharge_temp"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.discharge_temp


class RoomTempSensor(_IlahpSensor):
    _attr_translation_key = "room_temp"
    _attr_device_class = SensorDeviceClass.TEMPERATURE
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_room_temp"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.room_temp


class CompressorCurrentSensor(_IlahpSensor):
    _attr_translation_key = "compressor_current"
    _attr_device_class = SensorDeviceClass.CURRENT
    _attr_native_unit_of_measurement = UnitOfElectricCurrent.AMPERE
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_compressor_current"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.compressor_current


class CompressorRuntimeSensor(_IlahpSensor):
    _attr_translation_key = "compressor_runtime"
    _attr_device_class = SensorDeviceClass.DURATION
    _attr_native_unit_of_measurement = UnitOfTime.HOURS
    _attr_state_class = SensorStateClass.TOTAL_INCREASING
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_compressor_runtime"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.compressor_runtime_hours


class DcLineVoltageSensor(_IlahpSensor):
    _attr_translation_key = "dc_line_voltage"
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_dc_line_voltage"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.dc_line_voltage


class AcInputVoltageSensor(_IlahpSensor):
    _attr_translation_key = "ac_input_voltage"
    _attr_device_class = SensorDeviceClass.VOLTAGE
    _attr_native_unit_of_measurement = UnitOfElectricPotential.VOLT
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_ac_input_voltage"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.ac_input_voltage


class CompressorFreqSettingSensor(_IlahpSensor):
    _attr_translation_key = "compressor_freq_setting"
    _attr_device_class = SensorDeviceClass.FREQUENCY
    _attr_native_unit_of_measurement = UnitOfFrequency.HERTZ
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_compressor_freq_setting"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.compressor_freq_setting


class CompressorFreqRunningSensor(_IlahpSensor):
    _attr_translation_key = "compressor_freq_running"
    _attr_device_class = SensorDeviceClass.FREQUENCY
    _attr_native_unit_of_measurement = UnitOfFrequency.HERTZ

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_compressor_freq_running"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.compressor_freq_running


class WaterFlowSensor(_IlahpSensor):
    """Register 2077 -- unit unconfirmed (manual just says "DIGI9", no
    explicit gpm/lpm/m3h label). Left unitless rather than guessing."""

    _attr_translation_key = "water_flow"
    _attr_entity_category = EntityCategory.DIAGNOSTIC

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_water_flow"

    @property
    def native_value(self) -> float:
        return self.coordinator.data.water_flow


class OutputRelaysRawSensor(_IlahpSensor):
    """Register 2019 -- the same register as the existing (mislabeled, see
    device.py) `load_pct`, exposed here separately under its correct
    identity as a raw 16-bit output-relay bitmask. See device.py's
    `compressor_on`/`alarm_output` for the two bits actually decoded into
    their own binary_sensors."""

    _attr_translation_key = "output_relays_raw"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = None

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_output_relays_raw"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.output_relays_raw


class SwitchStatesRawSensor(_IlahpSensor):
    """Register 2034, the raw S01-S10 field input bitmask (1 = open).
    The useful bits are decoded into binary_sensors; see device.py."""

    _attr_translation_key = "switch_states_raw"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = None

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry)
        self._attr_unique_id = f"{entry.entry_id}_switch_states_raw"

    @property
    def native_value(self) -> int:
        return self.coordinator.data.switch_states_raw


class _FailureSensor(_IlahpSensor):
    """Base for the 9 raw Failure-register diagnostics -- see device.py's
    module docstring for why these aren't bit-decoded individually."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_state_class = None

    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry, n: int) -> None:
        super().__init__(coordinator, entry)
        self._n = n
        self._attr_translation_key = f"failure_{n}_raw"
        self._attr_unique_id = f"{entry.entry_id}_failure_{n}_raw"

    @property
    def native_value(self) -> int:
        return getattr(self.coordinator.data, f"failure_{self._n}_raw")


class Failure1Sensor(_FailureSensor):
    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, 1)


class Failure2Sensor(_FailureSensor):
    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, 2)


class Failure3Sensor(_FailureSensor):
    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, 3)


class Failure4Sensor(_FailureSensor):
    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, 4)


class Failure5Sensor(_FailureSensor):
    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, 5)


class Failure6Sensor(_FailureSensor):
    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, 6)


class Failure7Sensor(_FailureSensor):
    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, 7)


class Failure8Sensor(_FailureSensor):
    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, 8)


class Failure9Sensor(_FailureSensor):
    def __init__(self, coordinator: IlahpCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator, entry, 9)
