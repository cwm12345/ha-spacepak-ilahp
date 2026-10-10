"""Test the SpacePak ILAHP config flow."""

# Written by Claude, guided by Chris.

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, _patch, patch

from modbus_connection import ModbusTcpParams, ModbusTimeoutError
from modbus_connection.mock import MockModbusConnection, MockModbusUnit
import pytest
from tests.common import MockConfigEntry

from homeassistant import config_entries
from homeassistant.components.spacepak_ilahp.const import DEFAULT_NAME, DOMAIN
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from homeassistant.exceptions import HomeAssistantError

from . import MOCK_UNIQUE_ID, MOCK_USER_INPUT, seed_heat_pump


def _patch_temporary_unit(connection: MockModbusConnection) -> _patch:
    """Stand in for async_get_temporary_unit, handing out a unit on connection."""

    @asynccontextmanager
    async def _get_temporary_unit(
        hass: HomeAssistant, params: ModbusTcpParams, unit_id: int
    ) -> AsyncIterator[MockModbusUnit]:
        yield connection.for_unit(unit_id)

    return patch(
        "homeassistant.components.spacepak_ilahp.config_flow.async_get_temporary_unit",
        side_effect=_get_temporary_unit,
    )


async def test_user_step_shows_form(hass: HomeAssistant) -> None:
    """The form renders with no errors before any input."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}


async def test_user_step_success(
    hass: HomeAssistant, mock_setup_entry: AsyncMock
) -> None:
    """A heat pump that answers creates an entry keyed on host, port and unit."""
    connection = MockModbusConnection()
    seed_heat_pump(connection.for_unit(1))

    with _patch_temporary_unit(connection):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=MOCK_USER_INPUT,
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_NAME
    assert result["data"] == MOCK_USER_INPUT
    assert result["result"].unique_id == MOCK_UNIQUE_ID
    assert len(mock_setup_entry.mock_calls) == 1


@pytest.mark.parametrize(
    "error", [ModbusTimeoutError("stuck"), HomeAssistantError("in use")]
)
async def test_user_step_cannot_connect_then_recovers(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, error: Exception
) -> None:
    """An unreachable unit shows cannot_connect, and a retry succeeds."""
    connection = MockModbusConnection()
    seed_heat_pump(connection.for_unit(1))
    connection.for_unit(1).fail_requests(error)

    with _patch_temporary_unit(connection):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data=MOCK_USER_INPUT,
        )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": "cannot_connect"}

    connection.for_unit(1).fail_requests(None)
    with _patch_temporary_unit(connection):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], MOCK_USER_INPUT
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY


async def test_a_second_unit_on_the_same_port_is_its_own_entry(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Two units behind one gateway port differ by unit ID, and both configure."""
    mock_config_entry.add_to_hass(hass)
    connection = MockModbusConnection()
    seed_heat_pump(connection.for_unit(2))

    with _patch_temporary_unit(connection):
        result = await hass.config_entries.flow.async_init(
            DOMAIN,
            context={"source": config_entries.SOURCE_USER},
            data={**MOCK_USER_INPUT, "unit_id": 2},
        )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == "192.0.2.10:502:2"


async def test_already_configured(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """The same host, port and unit ID aborts."""
    mock_config_entry.add_to_hass(hass)
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_USER},
        data=MOCK_USER_INPUT,
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
