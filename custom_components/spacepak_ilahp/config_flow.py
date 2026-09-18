# Written by Claude, guided by Chris.
"""Config flow for the SpacePak ILAHP integration.

Validates against the live unit before creating the entry -- same reasoning
as the sibling tripplite_pdu integration: a bad host/port should show an
error in the form, not silently create a broken entry.
"""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT
from homeassistant.data_entry_flow import FlowResult
from modbus_connection import ModbusConnectionError, ModbusTcpParams
from modbus_connection.pymodbus import ModbusConnection

from .const import CONF_UNIT_ID, DEFAULT_GATEWAY_HOST, DEFAULT_UNIT_ID, DOMAIN
from .device import IlahpHeatPump

_LOGGER = logging.getLogger(__name__)

STEP_USER_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_HOST, default=DEFAULT_GATEWAY_HOST): str,
        vol.Required(CONF_PORT): int,
        vol.Required(CONF_UNIT_ID, default=DEFAULT_UNIT_ID): int,
    }
)


class SpacepakIlahpConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """One config entry per physical heat pump (HP1 = port 10001, HP2 = port 10002)."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        errors: dict[str, str] = {}
        if user_input is not None:
            unique_id = f"{user_input[CONF_HOST]}:{user_input[CONF_PORT]}"
            await self.async_set_unique_id(unique_id)
            self._abort_if_unique_id_configured()

            connection = ModbusConnection(
                ModbusTcpParams(host=user_input[CONF_HOST], port=user_input[CONF_PORT])
            )
            try:
                device = IlahpHeatPump(connection.for_unit(user_input[CONF_UNIT_ID]))
                await device.async_update()
            except ModbusConnectionError:
                _LOGGER.exception(
                    "Failed to validate ILAHP unit at %s", unique_id
                )
                errors["base"] = "cannot_connect"
            else:
                _LOGGER.debug(
                    "Validated ILAHP unit %s: power_on=%s outlet_temp=%.1fC",
                    unique_id, device.power_on, device.outlet_temp,
                )
                # Friendly title/device-name instead of the raw host:port --
                # port 10001/10002 are the confirmed HP1/HP2 convention on
                # the shared gateway; anything else falls back to the raw
                # unique_id rather than guessing a number.
                friendly = {10001: "SpacePak HP1", 10002: "SpacePak HP2"}.get(
                    user_input[CONF_PORT], unique_id
                )
                return self.async_create_entry(title=friendly, data=user_input)
            finally:
                await connection.close()

        return self.async_show_form(
            step_id="user", data_schema=STEP_USER_SCHEMA, errors=errors
        )
