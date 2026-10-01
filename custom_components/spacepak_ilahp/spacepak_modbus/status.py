# Written by Claude, guided by Chris.
"""Whether the unit is running, in what mode, and which outputs are driven."""

from __future__ import annotations

from modbus_connection.model import Component, boolean, enum, flags, gauge, integer

from .enums import OpenInputs, Outputs, UnitMode

__all__ = ["Status"]


class Status(Component):
    """Run state, mode, effective targets, outputs, inputs and compressor hours."""

    running = boolean(2011)
    """Unit state: on and running."""

    unit_mode = enum(2012, UnitMode)
    """What the unit is doing right now, defrost included."""

    limited_target_temperature = gauge(2013, 0.1, unit="°C")
    """The water target after the unit's own limits are applied."""

    compensated_heating_target_temperature = gauge(2014, 0.1, unit="°C")
    """The heating water target after weather compensation. Only meaningful
    while ``Tuning.weather_compensation_enabled``; with it off some units
    report 0 here and others the plain target."""

    outputs = flags(2019, Outputs)
    """The load outputs currently energized."""

    compressor_hours = integer(2032, signed=False, unit="h")
    """Accumulated compressor running time."""

    open_inputs = flags(2034, OpenInputs)
    """The field switch inputs that are open."""

    def _closed(self, switch: OpenInputs) -> bool | None:
        open_inputs = self.open_inputs
        return None if open_inputs is None else switch not in open_inputs

    @property
    def remote_on_off_closed(self) -> bool | None:
        """Whether the remote on/off (master enable) input is closed."""
        return self._closed(OpenInputs.REMOTE_ON_OFF)

    @property
    def heat_cool_on_off_closed(self) -> bool | None:
        """Whether the heating/cooling on/off input is closed."""
        return self._closed(OpenInputs.HEAT_COOL_ON_OFF)

    @property
    def heat_selected(self) -> bool | None:
        """Whether the remote heating/cooling input selects heating."""
        return self._closed(OpenInputs.REMOTE_HEAT_COOL)

    @property
    def flow_switch_closed(self) -> bool | None:
        """Whether the water flow switch is closed."""
        return self._closed(OpenInputs.WATER_FLOW)

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
