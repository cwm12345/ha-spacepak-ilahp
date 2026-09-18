# SpacePak ILAHP for Home Assistant

A `config_entry`-owned Home Assistant custom integration for SpacePak
Solstice Inverter Extreme (ILAHP) heat pumps over Modbus TCP, built on
Home Assistant's newer [Modbus device
model](https://developers.home-assistant.io/blog/2026/07/05/modernizing-modbus/)
(`modbus-connection` / `modbus_connection.model`) rather than a bespoke
Modbus client. Each heat pump shows up as a proper HA device with typed,
correctly-scaled entities, instead of a pile of raw, deviceless
`modbus:` YAML sensors.

## Status

This is a working reference implementation, pulled from my own running
Home Assistant deployment (two ILAHP units) and published as-is. **I am
not maintaining this as an ongoing package** — no commitment to triage
issues, accept PRs, or track future Home Assistant API changes. Feel free
to fork it, adapt it, or copy pieces of it into your own setup. If it's
useful, great; if you hit something that doesn't work on your hardware or
your HA version, you're welcome to open an issue, but I can't promise a
response.

If you're a more serious maintainer and see something here worth turning
into an official core Home Assistant integration, take it — this code is
public domain (Unlicense), no permission needed. It's already built on
HA's new `modbus-connection`/device-model library specifically so it'd be
a smaller step to core than a from-scratch rewrite, if anyone wants to
take it there.

## Hardware this was built and tested against

SpacePak Solstice Inverter Extreme (ILAHP) air-source heat pumps, Modbus
TCP (via a serial-to-TCP gateway in my deployment; a direct Modbus TCP
unit should work identically). Register addresses were taken from the
manufacturer's Modbus IOM manual and cross-checked against live reads —
see `device.py`'s module docstring for the full citation and any
discrepancies found along the way.

## What it does

One config entry per physical unit (if you have two sharing a gateway,
add two entries with different ports). Each entry creates one HA device
with:

- `switch.power` — master on/off.
- `number.heating_target_temp` / `number.cooling_target_temp` — writable
  setpoints, bounded 10–60°C.
- `binary_sensor.unit_running`, `binary_sensor.compressor_on`,
  `binary_sensor.alarm_output`, `binary_sensor.any_fault` — computed from
  the unit's status/output-relay/fault registers.
- Telemetry sensors: outlet/inlet/ambient/room/coil/suction/discharge/DHW
  tank temperatures, AC current, compressor current, compressor runtime,
  DC line voltage, AC input voltage, compressor frequency (setting and
  running), water flow, current operating mode, and 9 raw fault/alarm
  bitmask registers (diagnostic).
- Config flow validates against the live unit before creating the entry.
- Polls every 30s via a `DataUpdateCoordinator`.

**Deliberately not exposed:** the installer-level configuration/tuning
register block (compressor curves, EEV steps, defrost timing, weather
compensation, scheduling — roughly 260 registers). These are setup
parameters, not telemetry, and writing to them risks real HVAC
misconfiguration — this integration only exposes what's safe to read and
the two setpoints that are safe to write.

**Deliberately read-only:** the operating-mode register is exposed as a
raw diagnostic number, not a writable `select` entity — the manual
documents it as read/write, but the exact integer-to-mode mapping was
never confirmed against a live unit in my deployment. Don't wire up write
access to it on a guess; confirm the mapping against your own unit's
manual/behavior first.

## Real functional testing, not just syntax-checking

Because this integration is built on `modbus_connection.model`, it could
be tested against that library's own in-memory mock backend — seeding
fake register values, running a real `async_update()`, and confirming
both correct read-side scaling and correct write-side raw values land.
That's genuine behavioral confidence, not just "it compiles."

## Installation

**Via HACS (custom repository):** HACS → Integrations → ⋮ → Custom
repositories → add this repo's URL, category "Integration" → install
"SpacePak ILAHP" → restart HA.

**Manual:** copy `custom_components/spacepak_ilahp/` into your HA
config's `custom_components/` directory → restart HA.

Then: Settings → Devices & Services → Add Integration → "SpacePak
ILAHP". Enter the Modbus TCP gateway host/port and the unit's Modbus
slave ID.

**Before writing to `power`, `heating_target_temp`, or
`cooling_target_temp`:** these are live control points on real HVAC
equipment. Know what you're setting before you set it.

## Files

- `device.py` — the standalone device model (no HA imports, per HA's
  convention for this new Modbus device model). This is where the
  register map lives — read it before trusting it against your own unit.
- `manifest.json`, `const.py`, `config_flow.py`, `__init__.py`,
  `coordinator.py`, `entity.py` — integration scaffolding.
- `sensor.py`, `binary_sensor.py`, `switch.py`, `number.py` — entity
  platforms.
- `strings.json` / `translations/en.json` — config flow + entity text.

## Validation

All files pass `py_compile` / JSON validation, every module imports
cleanly against a real installed `homeassistant` package, config flow
self-registers correctly, and a mock-backend functional test exercises
every field's read-side scaling plus both writable setpoints. Deployed
and running against real hardware (two physical heat pumps) since
September 2026.
