"""Test setting up and tearing down the SpacePak ILAHP integration."""

# Written by Claude, guided by Chris.

from datetime import timedelta
from unittest.mock import patch

from freezegun.api import FrozenDateTimeFactory
from modbus_connection import (
    IllegalDataAddressError,
    ModbusConnectionError,
    ModbusTimeoutError,
)
from modbus_connection.mock import MockModbusConnection
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_fire_time_changed,
)

from custom_components.spacepak_ilahp.const import DEFAULT_NAME, DOMAIN
from homeassistant.config_entries import ConfigEntryState
from homeassistant.const import STATE_UNAVAILABLE
from homeassistant.core import HomeAssistant

from . import MOCK_UNIQUE_ID, MOCK_USER_INPUT

OUTLET = "sensor.spacepak_ilahp_outlet_water_temperature"
FAULT = "binary_sensor.spacepak_ilahp_fault"
POWER = "switch.spacepak_ilahp_power"


async def test_setup_and_unload(
    hass: HomeAssistant, init_integration: MockConfigEntry
) -> None:
    """The entry loads, creates entities, and unloads."""
    assert init_integration.state is ConfigEntryState.LOADED
    assert hass.states.get(OUTLET).state == "43.2"

    await hass.config_entries.async_unload(init_integration.entry_id)
    await hass.async_block_till_done()
    assert init_integration.state is ConfigEntryState.NOT_LOADED


async def test_setup_retries_when_unreachable(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_connection: MockModbusConnection,
) -> None:
    """A unit that answers nothing makes setup retry rather than fail."""
    mock_connection.for_unit(1).fail_requests(ModbusTimeoutError())
    mock_config_entry.add_to_hass(hass)
    with patch(
        "custom_components.spacepak_ilahp.async_get_unit",
        side_effect=lambda hass, entry, params, unit_id: mock_connection.for_unit(
            unit_id
        ),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.SETUP_RETRY


async def test_a_refused_component_only_hides_its_entities(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_connection: MockModbusConnection,
    freezer: FrozenDateTimeFactory,
) -> None:
    """A failed fault block marks the fault sensor unavailable, nothing else."""
    mock_connection.for_unit(1).fail_read(2081, IllegalDataAddressError())
    freezer.tick(timedelta(seconds=31))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    assert hass.states.get(FAULT).state == STATE_UNAVAILABLE
    assert hass.states.get(OUTLET).state == "43.2"


async def test_a_dead_link_recovers(
    hass: HomeAssistant,
    init_integration: MockConfigEntry,
    mock_connection: MockModbusConnection,
    freezer: FrozenDateTimeFactory,
) -> None:
    """A dropped link makes readings unavailable until the next good poll."""
    unit = mock_connection.for_unit(1)
    unit.fail_requests(ModbusConnectionError())
    freezer.tick(timedelta(seconds=31))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(OUTLET).state == STATE_UNAVAILABLE
    assert init_integration.state is ConfigEntryState.LOADED

    unit.fail_requests(None)
    freezer.tick(timedelta(seconds=31))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()
    assert hass.states.get(OUTLET).state == "43.2"


async def test_migrate_host_port_unique_id(
    hass: HomeAssistant, mock_connection: MockModbusConnection
) -> None:
    """A 1.1 entry keyed on host:port gains the unit ID in its unique ID."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        unique_id="192.0.2.10:502",
        data=MOCK_USER_INPUT,
        title=DEFAULT_NAME,
        version=1,
        minor_version=1,
    )
    entry.add_to_hass(hass)
    with patch(
        "custom_components.spacepak_ilahp.async_get_unit",
        side_effect=lambda hass, entry, params, unit_id: mock_connection.for_unit(
            unit_id
        ),
    ):
        await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    assert entry.state is ConfigEntryState.LOADED
    assert entry.unique_id == MOCK_UNIQUE_ID
    assert entry.minor_version == 2


async def test_future_version_does_not_load(hass: HomeAssistant) -> None:
    """An entry from a newer major version is refused."""
    entry = MockConfigEntry(
        domain=DOMAIN, unique_id=MOCK_UNIQUE_ID, data=MOCK_USER_INPUT, version=2
    )
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    assert entry.state is ConfigEntryState.MIGRATION_ERROR
