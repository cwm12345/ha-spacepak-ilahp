# Written by Claude, guided by Chris.
"""SpacePak Solstice Inverter Extreme (ILAHP) heat pump -- device model.

Standalone device library, per HA's own convention for the new Modbus
device model ("device libraries are meant as standalone libraries and
should not mention Home Assistant"). This file has no HA imports.

Register map confirmed from the unit's own IOM manual
(ILAHP_Installation_Manual.pdf, ILHP2-0423) and cross-checked against the
live production `modbus.yaml` config plus a live read/write test this
session (2026-09-17 -- nudged register 1158 on both HP1 and HP2 via HA's
own modbus.write_register service, confirmed the change took effect and
reverted it). NOT the full ~250-register map from the manual -- registers
1011-1270 are almost entirely installer-level setup/tuning parameters
(compressor frequency curves, EEV steps, defrost timing, weather
compensation, 7-day timers, etc.) deliberately NOT exposed here; writing
to those on a whim risks real HVAC misconfiguration, not just a wrong
HA reading. What IS exposed: the already-in-use control/status registers,
plus a 2026-09-19 expansion covering the 2011-2090 read-only telemetry
and fault/alarm block (Chris: "let's do the HP1/HP2 expansion now",
closing the gap first flagged 2026-09-18 -- "note the gap for now").

Units are Celsius raw off the wire (confirmed: raw register value 500 at
scale 0.1 = 50.0, which the existing "clean" template sensor converts to
122.0F -- 50C = 122F exactly). Modeled here as Celsius; let HA's own
sensor device_class + unit conversion handle F display, rather than
converting by hand.

⚠️ Real finding from the manual, 2026-09-19: register 2019 -- already in
production use since before this project as "Load %" (`sensor.hp1_load`
in templates.yaml, `load_pct` below) -- is documented as a 16-bit O01-O14
OUTPUT RELAY BITMASK (compressor/fans/pumps/valves/heaters/alarm output),
NOT a load percentage at all. This likely explains the "values like
6164% are meaningless" note already on file in Energy Analysis.md -- a
bitmask read as if it were a 0-100 percentage would produce exactly that
kind of nonsense number. `load_pct` is left as-is here (not renamed/
reinterpreted) to avoid breaking the existing entity's continuity without
Chris's explicit go-ahead -- flagged in the README and roadmap instead.
The correctly-decoded bitmask is added separately below as
`output_relays_raw` (diagnostic, raw integer) plus two of its
individually-decoded bits that are actually useful for monitoring:
`compressor_on` (bit0) and `alarm_output` (bit10).
"""
from __future__ import annotations

from modbus_connection.model import Component, boolean, gauge, integer

# --- Confirmed read/write, live-tested 2026-09-17 ---
REG_POWER_ON = 1011  # unit master on/off
REG_HEATING_TARGET_TEMP = 1158  # R02, scale 0.1, Celsius
REG_COOLING_TARGET_TEMP = 1159  # R03, scale 0.1, Celsius

# Mode register exists and is read/write per the manual ("hot water /
# heating / cooling / combinations"), but the EXACT integer-to-mode
# mapping was never confirmed this session -- do not guess it. Modeled
# below as a raw integer (diagnostic only) until that mapping is verified
# (re-read the manual's H-parameter table carefully, or test live against
# one unit) -- only then should this become a real `select` entity.
REG_MODE_RAW = 1012

# --- Confirmed read-only telemetry, already in production use via modbus.yaml ---
REG_UNIT_STATE = 2011  # running/idle
REG_OUTLET_TEMP = 2046  # T02, scale 0.1, Celsius
REG_AMBIENT_TEMP = 2048  # T04, scale 0.1, Celsius
REG_AC_CURRENT = 2057  # T35, scale 0.1, Amps
# REG_LOAD_PCT (2019, "Load %") retired 2026-09-19 by Claude, guided by
# Chris -- see "Real finding" note above. Same register as
# REG_OUTPUT_RELAYS_RAW below; keeping both was just two entities for one
# register, one of them wrong. Chris: "cleanup the load % thing...
# whichever gives us cleaner results, retire or rename" -- retire chosen,
# since a correctly-labeled entity for this exact register already
# exists (`output_relays_raw`), so renaming would still leave a
# duplicate.

# --- New 2026-09-19 expansion: read-only status/telemetry, 2011-2090 block ---
REG_UNIT_MODE = 2012  # 0=cooling/1=heating/2=defrost/3=sterilize/4=hot water
REG_OUTPUT_RELAYS_RAW = 2019  # same register as REG_LOAD_PCT -- see note above
REG_COMPRESSOR_RUNTIME_HOURS = 2032  # accumulative running time
REG_INLET_TEMP = 2045  # T01, scale 0.1, Celsius
REG_DHW_TANK_TEMP = 2047  # T08, scale 0.1, Celsius
REG_COIL_TEMP = 2049  # T03, scale 0.1, Celsius
REG_SUCTION_TEMP = 2051  # T05, scale 0.1, Celsius
REG_DISCHARGE_TEMP = 2053  # T12, scale 0.1, Celsius
REG_COMPRESSOR_CURRENT = 2042  # T36, scale 0.1, Amps (DIGI5 in the manual)
REG_DC_LINE_VOLTAGE = 2043  # T37, scale 1, Volts
REG_ROOM_TEMP = 2058  # T09, scale 0.1, Celsius
REG_AC_INPUT_VOLTAGE = 2062  # T34, scale 1, Volts
REG_COMPRESSOR_FREQ_SETTING = 2071  # T30, scale 1, Hz
REG_COMPRESSOR_FREQ_RUNNING = 2072  # T31, scale 1, Hz
REG_WATER_FLOW = 2077  # T39, scale 0.01 (DIGI9 in the manual)

# --- New 2026-09-19 expansion: fault/alarm bitmask registers ---
# Exposed as raw diagnostic integers, NOT individually bit-decoded (each
# one packs up to 16 distinct fault conditions -- see the manual's own
# bit tables for the full per-bit meaning of each register). No live
# fault has occurred on either unit to verify behavior against, so this
# intentionally stops at "raw value visible" rather than guessing which
# bit is which in a `binary_sensor` -- same caution already applied to
# the boiler's blocking/lockout codes. `any_fault` below is the one
# computed exception: a simple "is ANY of these nonzero" summary, safe
# because it doesn't depend on knowing which specific bit fired.
REG_FAILURE_1 = 2085
REG_FAILURE_2 = 2086
REG_FAILURE_3 = 2087
REG_FAILURE_4 = 2088
REG_FAILURE_5 = 2089
REG_FAILURE_6 = 2090
REG_FAILURE_7 = 2081
REG_FAILURE_8 = 2082
REG_FAILURE_9 = 2083


class IlahpHeatPump(Component):
    """One SpacePak Solstice Inverter Extreme (ILAHP) unit.

    Uses Component, not Device -- this unit has one flat register set, no
    distinct sub-systems to group, and Component's API (async_update(),
    direct attribute reads, .write(field, value)) is the one demonstrated
    concretely in the library's own docs. Device's async_poll()-based
    pattern looked built for something with named sub-components, which
    this isn't.
    """

    power_on = boolean(REG_POWER_ON, writable=True)
    heating_target_temp = gauge(
        REG_HEATING_TARGET_TEMP, 0.1, writable=True, unit="C"
    )
    cooling_target_temp = gauge(
        REG_COOLING_TARGET_TEMP, 0.1, writable=True, unit="C"
    )
    mode_raw = integer(REG_MODE_RAW)  # read-only here on purpose -- see note above

    unit_running = boolean(REG_UNIT_STATE)
    outlet_temp = gauge(REG_OUTLET_TEMP, 0.1, unit="C")
    ambient_temp = gauge(REG_AMBIENT_TEMP, 0.1, unit="C")
    ac_current = gauge(REG_AC_CURRENT, 0.1, unit="A")

    # -- 2026-09-19 expansion --
    unit_mode_raw = integer(REG_UNIT_MODE)
    output_relays_raw = integer(REG_OUTPUT_RELAYS_RAW)
    compressor_runtime_hours = integer(REG_COMPRESSOR_RUNTIME_HOURS, unit="h")
    inlet_temp = gauge(REG_INLET_TEMP, 0.1, unit="C")
    dhw_tank_temp = gauge(REG_DHW_TANK_TEMP, 0.1, unit="C")
    coil_temp = gauge(REG_COIL_TEMP, 0.1, unit="C")
    suction_temp = gauge(REG_SUCTION_TEMP, 0.1, unit="C")
    discharge_temp = gauge(REG_DISCHARGE_TEMP, 0.1, unit="C")
    compressor_current = gauge(REG_COMPRESSOR_CURRENT, 0.1, unit="A")
    dc_line_voltage = integer(REG_DC_LINE_VOLTAGE, unit="V")
    room_temp = gauge(REG_ROOM_TEMP, 0.1, unit="C")
    ac_input_voltage = integer(REG_AC_INPUT_VOLTAGE, unit="V")
    compressor_freq_setting = integer(REG_COMPRESSOR_FREQ_SETTING, unit="Hz")
    compressor_freq_running = integer(REG_COMPRESSOR_FREQ_RUNNING, unit="Hz")
    water_flow = gauge(REG_WATER_FLOW, 0.01)

    failure_1_raw = integer(REG_FAILURE_1)
    failure_2_raw = integer(REG_FAILURE_2)
    failure_3_raw = integer(REG_FAILURE_3)
    failure_4_raw = integer(REG_FAILURE_4)
    failure_5_raw = integer(REG_FAILURE_5)
    failure_6_raw = integer(REG_FAILURE_6)
    failure_7_raw = integer(REG_FAILURE_7)
    failure_8_raw = integer(REG_FAILURE_8)
    failure_9_raw = integer(REG_FAILURE_9)

    @property
    def compressor_on(self) -> bool:
        """Output relay bit0 (O01 compressor output) from REG_OUTPUT_RELAYS_RAW."""
        return bool(self.output_relays_raw & 0x0001)

    @property
    def alarm_output(self) -> bool:
        """Output relay bit10 (O11 alarm output) from REG_OUTPUT_RELAYS_RAW."""
        return bool(self.output_relays_raw & 0x0400)

    @property
    def any_fault(self) -> bool:
        """True if any of the 9 Failure registers is nonzero. Deliberately
        not narrowed to "which fault" -- see class docstring."""
        return any(
            [
                self.failure_1_raw,
                self.failure_2_raw,
                self.failure_3_raw,
                self.failure_4_raw,
                self.failure_5_raw,
                self.failure_6_raw,
                self.failure_7_raw,
                self.failure_8_raw,
                self.failure_9_raw,
            ]
        )
