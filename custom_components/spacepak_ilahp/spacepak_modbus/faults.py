# Written by Claude, guided by Chris.
"""The nine failure registers, decoded into named faults."""

from __future__ import annotations

from dataclasses import dataclass

from modbus_connection.model import Component, raw_register

__all__ = ["FAULTS", "FAILURE_ADDRESSES", "Fault", "Faults"]

FAILURE_ADDRESSES: dict[int, int] = {
    1: 2085,
    2: 2086,
    3: 2087,
    4: 2088,
    5: 2089,
    6: 2090,
    7: 2081,
    8: 2082,
    9: 2083,
}
"""Failure register number to its address. The manual numbers them out of
address order: failures 7-9 sit below failures 1-6."""


@dataclass(frozen=True)
class Fault:
    """One fault bit."""

    register: int
    """The failure register number, 1-9."""
    bit: int
    key: str
    """A stable snake_case name."""
    description: str
    """The manual's wording, lightly cleaned up."""


def _faults(register: int, bits: dict[int, tuple[str, str]]) -> list[Fault]:
    return [Fault(register, bit, key, text) for bit, (key, text) in bits.items()]


FAULTS: tuple[Fault, ...] = tuple(
    [
        *_faults(
            1,
            {
                2: (
                    "heating_return_sensor",
                    "Heating return water temperature sensor failure",
                ),
                3: (
                    "heating_outlet_sensor",
                    "Heating outlet water temperature sensor failure",
                ),
                4: ("high_pressure", "High pressure protection"),
                6: ("low_pressure", "Low pressure protection"),
                8: ("water_flow", "Water flow protection"),
                9: ("electric_heater_overload", "Electric heater overload protection"),
                10: ("antifreeze_stage_1", "First-stage winter anti-freeze protection"),
                11: (
                    "antifreeze_stage_2",
                    "Second-stage winter anti-freeze protection",
                ),
                12: ("antifreeze", "Anti-freeze protection"),
                14: ("room_temperature", "Room temperature fault"),
            },
        ),
        *_faults(
            2,
            {
                0: ("discharge_overheat", "Discharge temperature overheat protection"),
                3: ("fan_1_speed_limit", "Fan 1 overload speed limit"),
                4: ("fan_2_speed_limit", "Fan 2 overload speed limit"),
                6: ("outlet_water_overheat", "Outlet water overheat"),
                7: (
                    "mixing_outlet_sensor",
                    "Mixing outlet water temperature sensor failure",
                ),
                8: (
                    "hot_water_return_sensor",
                    "Hot water return temperature sensor failure",
                ),
                9: (
                    "hot_water_outlet_sensor",
                    "Hot water outlet temperature sensor failure",
                ),
            },
        ),
        *_faults(
            4,
            {
                0: (
                    "discharge_overheat_lockout",
                    "Discharge overheat protection three times",
                ),
                4: (
                    "outlet_water_overheat_lockout",
                    "Outlet water overheat protection three times",
                ),
            },
        ),
        *_faults(
            5,
            {
                0: ("inlet_sensor", "Inlet water temperature sensor failure"),
                1: ("outlet_sensor", "Outlet water temperature sensor failure"),
                2: ("coil_sensor", "Coil temperature sensor failure"),
                3: ("ambient_sensor", "Ambient temperature sensor failure"),
                4: ("suction_sensor", "Suction temperature sensor failure"),
                5: ("antifreeze_sensor", "Anti-freeze temperature sensor failure"),
                9: ("evi_inlet_sensor", "EVI inlet temperature sensor failure"),
                10: ("evi_outlet_sensor", "EVI outlet temperature sensor failure"),
                11: ("discharge_sensor", "Discharge temperature sensor failure"),
                13: ("pressure_sensor", "System 1 pressure sensor failure"),
                14: ("low_ambient", "Low ambient temperature"),
            },
        ),
        *_faults(
            6,
            {
                8: ("hot_water_sensor", "Hot water temperature sensor failure"),
                11: ("fan_1", "Fan 1 failure"),
                12: ("fan_2", "Fan 2 failure"),
                13: (
                    "fan_1_communication",
                    "Main board to fan motor 1 module communication failure",
                ),
                15: (
                    "fan_2_communication",
                    "Main board to fan motor 2 module communication failure",
                ),
            },
        ),
        *_faults(
            7,
            {
                0: ("ipm_overheat", "IPM overheat"),
                1: ("compressor_start", "Compressor start failure"),
                2: ("compressor_overcurrent", "Compressor overcurrent"),
                3: ("input_phase_loss", "Input voltage phase loss"),
                4: ("ipm_current_sampling", "IPM current sampling fault"),
                5: ("drive_board_overheat", "Drive board overheat protection"),
                6: ("pfc", "PFC failure"),
                7: ("dc_bus_overvoltage", "DC bus overvoltage"),
                8: ("dc_bus_undervoltage", "DC bus undervoltage"),
                9: ("ac_input_undervoltage", "AC input undervoltage"),
                10: ("ac_input_overcurrent", "AC input overcurrent shutdown"),
                11: ("input_voltage_sampling", "Input voltage sampling fault"),
                12: ("dsp_pfc_communication", "DSP to PFC communication failure"),
                13: ("drive_board_temperature", "Drive board temperature fault"),
                14: (
                    "dsp_communication",
                    "DSP to communication board communication failure",
                ),
                15: ("mainboard_communication", "Main board communication failure"),
            },
        ),
        *_faults(
            8,
            {
                0: ("ipm_overheat_stop", "IPM overheat stop"),
                3: ("undervoltage_15v", "15 V DC undervoltage"),
            },
        ),
        *_faults(
            9,
            {
                0: (
                    "current_frequency_reduction",
                    "Current-limited frequency reduction alarm",
                ),
                1: ("field_weakening", "Compressor field-weakening protection alarm"),
                2: ("power_unit_overheat", "Power unit overheat alarm"),
                4: (
                    "ac_input_current_reduction",
                    "AC input current-limited reduction alarm",
                ),
                5: ("eeprom", "EEPROM failure warning"),
            },
        ),
    ]
)
"""Every fault bit the manual names. Failure register 3 has no published
bit table, so none of its bits are named."""

_BY_BIT: dict[tuple[int, int], Fault] = {
    (fault.register, fault.bit): fault for fault in FAULTS
}


class Faults(Component):
    """The failure registers, 2081-2090.

    ``active_faults`` names every bit that is set. A set bit the manual does
    not name is still reported, under a ``failure_<n>_bit_<b>`` key, so no
    fault is hidden.
    """

    failure_7 = raw_register(2081)
    failure_8 = raw_register(2082)
    failure_9 = raw_register(2083)
    failure_1 = raw_register(2085)
    failure_2 = raw_register(2086)
    failure_3 = raw_register(2087)
    failure_4 = raw_register(2088)
    failure_5 = raw_register(2089)
    failure_6 = raw_register(2090)

    def failure(self, register: int) -> int | None:
        """The raw word of failure register ``register`` (1-9)."""
        value: int | None = getattr(self, f"failure_{register}")
        return value

    @property
    def active_faults(self) -> tuple[Fault, ...]:
        """Every fault currently set, in register then bit order."""
        active: list[Fault] = []
        for register in range(1, 10):
            word = self.failure(register)
            if not word:
                continue
            for bit in range(16):
                if word & (1 << bit):
                    active.append(
                        _BY_BIT.get(
                            (register, bit),
                            Fault(
                                register,
                                bit,
                                f"failure_{register}_bit_{bit}",
                                "Undocumented fault bit",
                            ),
                        )
                    )
        return tuple(active)

    @property
    def any_fault(self) -> bool | None:
        """Whether any failure register has a bit set; ``None`` before a read."""
        words = [self.failure(register) for register in range(1, 10)]
        if any(word is None for word in words):
            return None
        return any(words)
