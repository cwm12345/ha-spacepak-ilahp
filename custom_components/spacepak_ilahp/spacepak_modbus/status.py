# Written by Claude, guided by Chris.
"""Whether the unit is running, in what mode, and which outputs are driven."""

from __future__ import annotations

from modbus_connection.model import Component, boolean, enum, flags, integer

from .enums import Outputs, UnitMode

__all__ = ["Status"]


class Status(Component):
    """Run state, current mode, load outputs and compressor hours."""

    running = boolean(2011)
    """Unit state: on and running."""

    unit_mode = enum(2012, UnitMode)
    """What the unit is doing right now, defrost included."""

    outputs = flags(2019, Outputs)
    """The load outputs currently energized."""

    compressor_hours = integer(2032, signed=False, unit="h")
    """Accumulated compressor running time."""

    @property
    def compressor_on(self) -> bool | None:
        """Whether the compressor output is energized."""
        outputs = self.outputs
        return None if outputs is None else Outputs.COMPRESSOR in outputs

    @property
    def alarm_on(self) -> bool | None:
        """Whether the alarm output is energized."""
        outputs = self.outputs
        return None if outputs is None else Outputs.ALARM in outputs
