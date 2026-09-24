"""The power switch for SpacePak ILAHP heat pumps."""

# Written by Claude, guided by Chris.

from __future__ import annotations

from typing import Any

from modbus_connection import ModbusError

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from homeassistant.helpers.entity_platform import AddConfigEntryEntitiesCallback

from .const import DOMAIN
from .coordinator import SpacePakConfigEntry
from .entity import SpacePakEntity, SpacePakEntityDescription

PARALLEL_UPDATES = 1

POWER = SpacePakEntityDescription(
    key="power", translation_key="power", component="controls"
)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: SpacePakConfigEntry,
    async_add_entities: AddConfigEntryEntitiesCallback,
) -> None:
    """Set up the SpacePak power switch."""
    async_add_entities([SpacePakPowerSwitch(entry, POWER)])


class SpacePakPowerSwitch(SpacePakEntity, SwitchEntity):
    """Turn the heat pump on and off."""

    @property
    def is_on(self) -> bool | None:
        """Whether the unit is switched on."""
        return self.coordinator.device.controls.power_on

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Switch the unit on."""
        await self._async_write(True)

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Switch the unit off."""
        await self._async_write(False)

    async def _async_write(self, value: bool) -> None:
        try:
            await self.coordinator.device.controls.write("power_on", value)
        except ModbusError as err:
            raise HomeAssistantError(
                translation_domain=DOMAIN,
                translation_key="write_failed",
                translation_placeholders={"error": str(err) or type(err).__name__},
            ) from err
        await self.coordinator.async_request_refresh()
