"""Base entity for SpacePak ILAHP heat pumps."""

# Written by Claude, guided by Chris.

from __future__ import annotations

from dataclasses import dataclass

from homeassistant.helpers.entity import EntityDescription
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .coordinator import SpacePakConfigEntry, SpacePakCoordinator


@dataclass(frozen=True, kw_only=True)
class SpacePakEntityDescription(EntityDescription):
    """Describe a SpacePak entity."""

    component: str
    """The attribute on IlahpHeatPump this entity reads from."""


class SpacePakEntity(CoordinatorEntity[SpacePakCoordinator]):
    """An entity on one heat pump, reading one of its components."""

    _attr_has_entity_name = True
    entity_description: SpacePakEntityDescription

    def __init__(
        self, entry: SpacePakConfigEntry, description: SpacePakEntityDescription
    ) -> None:
        """Initialize the entity."""
        super().__init__(entry.runtime_data.coordinator_for(description.component))
        self.entity_description = description
        self._attr_unique_id = f"{entry.entry_id}_{description.key}"
        self._attr_device_info = self.coordinator.device_info

    @property
    def available(self) -> bool:
        """Whether this entity's component answered the latest poll."""
        return (
            super().available
            and self.entity_description.component not in self.coordinator.data.failed
        )
