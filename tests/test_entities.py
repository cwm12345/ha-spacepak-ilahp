"""Test the SpacePak ILAHP entities."""

# Written by Claude, guided by Chris.

from datetime import timedelta
from unittest.mock import patch

from freezegun.api import FrozenDateTimeFactory
from modbus_connection import IllegalDataValueError
from modbus_connection.mock import MockModbusConnection
import pytest
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)
from pytest_homeassistant_custom_component.components.diagnostics import (
    get_diagnostics_for_config_entry,
)
from pytest_homeassistant_custom_component.typing import ClientSessionGenerator

from homeassistant.components.number import (
    ATTR_MAX,
    ATTR_MIN,
    ATTR_VALUE,
    DOMAIN as NUMBER_DOMAIN,
    SERVICE_SET_VALUE,
)
from homeassistant.components.switch import (
    DOMAIN as SWITCH_DOMAIN,
    SERVICE_TURN_OFF,
    SERVICE_TURN_ON,
)
from homeassistant.const import ATTR_ENTITY_ID, STATE_OFF, STATE_ON
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers import entity_registry as er

HEATING_TARGET = "number.spacepak_ilahp_heating_target_temperature"
POWER = "switch.spacepak_ilahp_power"


@pytest.mark.parametrize(
    ("entity_id", "state"),
    [
        ("sensor.spacepak_ilahp_outlet_water_temperature", "43.2"),
        ("sensor.spacepak_ilahp_inlet_water_temperature", "38.0"),
        ("sensor.spacepak_ilahp_outdoor_temperature", "-10.0"),
        ("sensor.spacepak_ilahp_coil_temperature", "-8.0"),
        ("sensor.spacepak_ilahp_discharge_temperature", "71.5"),
        ("sensor.spacepak_ilahp_ac_input_current", "14.2"),
        ("sensor.spacepak_ilahp_compressor_frequency", "60"),
        ("sensor.spacepak_ilahp_current_mode", "heating"),
        ("sensor.spacepak_ilahp_operating_mode", "heating"),
        ("sensor.spacepak_ilahp_compressor_running_time", "12345"),
        ("binary_sensor.spacepak_ilahp_running", STATE_ON),
        ("binary_sensor.spacepak_ilahp_compressor", STATE_ON),
        ("binary_sensor.spacepak_ilahp_alarm_output", STATE_OFF),
        ("binary_sensor.spacepak_ilahp_fault", STATE_OFF),
        ("binary_sensor.spacepak_ilahp_water_pump", STATE_ON),
        ("binary_sensor.spacepak_ilahp_fan", STATE_OFF),
        ("binary_sensor.spacepak_ilahp_reversing_valve", STATE_OFF),
        ("binary_sensor.spacepak_ilahp_electric_heater_stage_1", STATE_OFF),
        ("binary_sensor.spacepak_ilahp_electric_heater_stage_2", STATE_OFF),
        ("binary_sensor.spacepak_ilahp_crankcase_heater", STATE_OFF),
        ("binary_sensor.spacepak_ilahp_remote_on_off_input", STATE_ON),
        ("binary_sensor.spacepak_ilahp_heating_cooling_on_off_input", STATE_ON),
        ("binary_sensor.spacepak_ilahp_heating_selected_input", STATE_ON),
        ("binary_sensor.spacepak_ilahp_flow_switch", STATE_ON),
        (POWER, STATE_ON),
        (HEATING_TARGET, "45.0"),
        ("number.spacepak_ilahp_cooling_target_temperature", "7.0"),
    ],
)
async def test_entity_states(
    hass: HomeAssistant, init_integration: MockConfigEntry, entity_id: str, state: str
) -> None:
    """Every entity decodes the seeded registers."""
    assert hass.states.get(entity_id).state == state


async def test_unique_ids_keep_their_keys(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """Unique IDs are the entry ID plus a stable key."""
    entry = entity_registry.async_get(HEATING_TARGET)
    assert entry.unique_id == f"{init_integration.entry_id}_heating_target_temp"


async def test_raw_registers_are_disabled_by_default(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    entity_registry: er.EntityRegistry,
) -> None:
    """The raw failure registers exist but start disabled."""
    entry = entity_registry.async_get("sensor.spacepak_ilahp_failure_register_1")
    assert entry is not None
    assert entry.disabled_by is er.RegistryEntryDisabler.INTEGRATION


async def test_setpoint_limits_come_from_the_unit(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """The number's bounds are the unit's own R10/R11 limits."""
    state = hass.states.get(HEATING_TARGET)
    assert state.attributes[ATTR_MIN] == 15.0
    assert state.attributes[ATTR_MAX] == 50.0


async def test_set_heating_target(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_connection: MockModbusConnection,
) -> None:
    """Setting the number writes the scaled register and reads it back."""
    await hass.services.async_call(
        NUMBER_DOMAIN,
        SERVICE_SET_VALUE,
        {ATTR_ENTITY_ID: HEATING_TARGET, ATTR_VALUE: 47.5},
        blocking=True,
    )
    assert mock_connection.for_unit(1).holding[1158] == 475
    assert hass.states.get(HEATING_TARGET).state == "47.5"


async def test_setpoint_outside_the_units_limits_is_refused(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_connection: MockModbusConnection,
) -> None:
    """A value above R11 never reaches the unit."""
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            NUMBER_DOMAIN,
            SERVICE_SET_VALUE,
            {ATTR_ENTITY_ID: HEATING_TARGET, ATTR_VALUE: 55.0},
            blocking=True,
        )
    assert mock_connection.for_unit(1).holding[1158] == 450


async def test_power_switch(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_connection: MockModbusConnection,
) -> None:
    """The switch writes the power register and reads it back."""
    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: POWER}, blocking=True
    )
    assert mock_connection.for_unit(1).holding[1011] == 0
    assert hass.states.get(POWER).state == STATE_OFF

    await hass.services.async_call(
        SWITCH_DOMAIN, SERVICE_TURN_ON, {ATTR_ENTITY_ID: POWER}, blocking=True
    )
    assert mock_connection.for_unit(1).holding[1011] == 1


async def test_a_rejected_write_raises(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_connection: MockModbusConnection,
) -> None:
    """A write the unit refuses surfaces as a HomeAssistantError."""
    mock_connection.for_unit(1).fail_write(1011, IllegalDataValueError())
    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            SWITCH_DOMAIN, SERVICE_TURN_OFF, {ATTR_ENTITY_ID: POWER}, blocking=True
        )


async def test_fault_decoding(
    hass: HomeAssistant,
    mock_connection: MockModbusConnection,
    init_integration: MockConfigEntry,
    hass_client: ClientSessionGenerator,
) -> None:
    """Diagnostics carry the raw registers and the decoded faults."""
    mock_connection.for_unit(1).holding[2085] = 1 << 4  # high pressure
    diagnostics = await get_diagnostics_for_config_entry(
        hass, hass_client, init_integration
    )
    assert diagnostics["active_faults"] == ["high_pressure"]
    assert diagnostics["registers"]["holding"]["2046"] == 432
    assert "192.0.2.10" not in str(diagnostics)


async def test_cooling_outputs(
    hass: HomeAssistant,
    mock_connection: MockModbusConnection,
    init_integration: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Relay word 85 (seen live in cooling) lights compressor, fan, pump and valve."""
    mock_connection.for_unit(1).holding[2019] = 85
    freezer.tick(timedelta(seconds=31))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    for name in ("compressor", "fan", "water_pump", "reversing_valve"):
        assert hass.states.get(f"binary_sensor.spacepak_ilahp_{name}").state == STATE_ON
    assert (
        hass.states.get("binary_sensor.spacepak_ilahp_crankcase_heater").state
        == STATE_OFF
    )


async def test_tank_sensor_only_with_hot_water_enabled(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """With the hot water function off (H28 = 0) there is no tank sensor."""
    assert hass.states.get("sensor.spacepak_ilahp_hot_water_tank_temperature") is None
    assert hass.states.get("sensor.spacepak_ilahp_room_temperature") is None


async def test_tank_sensor_with_hot_water_enabled(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_connection: MockModbusConnection,
) -> None:
    """With the hot water function on, the tank sensor is created."""
    unit = mock_connection.for_unit(1)
    unit.holding[1028] = 1
    unit.holding[2047] = 480
    mock_config_entry.add_to_hass(hass)
    with patch(
        "custom_components.spacepak_ilahp.async_get_unit",
        side_effect=lambda hass, entry, params, unit_id: mock_connection.for_unit(
            unit_id
        ),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    state = hass.states.get("sensor.spacepak_ilahp_hot_water_tank_temperature")
    assert state is not None
    assert state.state == "48.0"


async def test_idle_field_inputs(
    hass: HomeAssistant,
    mock_connection: MockModbusConnection,
    init_integration: MockConfigEntry,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Input word 0x14 (seen live, idle) opens remote on/off and the flow switch."""
    mock_connection.for_unit(1).holding[2034] = 0x0014
    freezer.tick(timedelta(seconds=31))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    for name, state in (
        ("remote_on_off_input", STATE_OFF),
        ("flow_switch", STATE_OFF),
        ("heating_cooling_on_off_input", STATE_ON),
        ("heating_selected_input", STATE_ON),
    ):
        assert hass.states.get(f"binary_sensor.spacepak_ilahp_{name}").state == state
