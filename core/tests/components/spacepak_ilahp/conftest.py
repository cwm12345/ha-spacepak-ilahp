"""Common fixtures for the SpacePak ILAHP tests."""

# Written by Claude, guided by Chris.

from collections.abc import Generator
from unittest.mock import AsyncMock, patch

from modbus_connection.mock import MockModbusConnection
import pytest
from tests.common import MockConfigEntry

from homeassistant.components.spacepak_ilahp.const import DEFAULT_NAME, DOMAIN
from homeassistant.core import HomeAssistant

from . import MOCK_UNIQUE_ID, MOCK_USER_INPUT, seed_heat_pump


@pytest.fixture
def mock_setup_entry() -> Generator[AsyncMock]:
    """Override async_setup_entry."""
    with patch(
        "homeassistant.components.spacepak_ilahp.async_setup_entry",
        new_callable=AsyncMock,
        return_value=True,
    ) as mock_setup_entry:
        yield mock_setup_entry


@pytest.fixture
def mock_connection() -> MockModbusConnection:
    """Return a fake Modbus TCP connection seeded as a heating heat pump."""
    connection = MockModbusConnection()
    seed_heat_pump(connection.for_unit(1))
    return connection


@pytest.fixture
def mock_config_entry() -> MockConfigEntry:
    """Return a SpacePak ILAHP config entry."""
    return MockConfigEntry(
        domain=DOMAIN,
        unique_id=MOCK_UNIQUE_ID,
        data=MOCK_USER_INPUT,
        title=DEFAULT_NAME,
        version=1,
        minor_version=2,
    )


@pytest.fixture
async def init_integration(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_connection: MockModbusConnection,
) -> MockConfigEntry:
    """Set up the integration against the mock connection."""
    mock_config_entry.add_to_hass(hass)
    with patch(
        "homeassistant.components.spacepak_ilahp.async_get_unit",
        side_effect=lambda hass, entry, params, unit_id: mock_connection.for_unit(
            unit_id
        ),
    ):
        await hass.config_entries.async_setup(mock_config_entry.entry_id)
        await hass.async_block_till_done(wait_background_tasks=True)
    return mock_config_entry
