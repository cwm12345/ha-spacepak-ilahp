<!-- Written by Claude, guided by Chris. -->

# SpacePak ILAHP for Home Assistant

A Home Assistant integration for SpacePak Solstice Inverter Extreme (ILAHP)
air-to-water heat pumps, over Modbus TCP. Each heat pump is one device, with
its temperatures, compressor data, faults, power switch and water setpoints as
entities.

It follows Home Assistant's
[Modbus device integration guide](https://developers.home-assistant.io/docs/modbus/introduction),
using the same layering as the built-in `sofar` integration:

1. **[spacepak-modbus](https://github.com/cwm12345/spacepak-modbus)**, a
   standalone device library built on
   [modbus-connection](https://github.com/home-assistant-libs/modbus-connection).
   It holds the register map and is tested without Home Assistant.
2. **[`core/`](core/)**, the integration in Home Assistant core's layout
   (`homeassistant/components/spacepak_ilahp` and its tests), ready to be
   proposed to core.
3. **[`custom_components/spacepak_ilahp`](custom_components/spacepak_ilahp/)**,
   the same integration with the library copied in, installable through HACS.
   [`scripts/vendor.py`](scripts/vendor.py) generates it from the first two.

## Status

This is a working reference pulled from one real installation, not an actively
maintained package. There's no commitment to triage issues or pull requests,
or to follow future Home Assistant changes. Forks are welcome. So is anyone
who wants to take it further, including toward Home Assistant core: `core/` is
the starting point for that.

## Requirements

- Home Assistant 2026.10 or newer. The integration gets its Modbus connection
  from Home Assistant's `modbus` integration, and needs the modbus-connection
  4.12 it ships from 2026.10. 2026.9 pins 4.10, which lacks the device model
  this is built on, and the integration fails to import there.
- A Modbus TCP gateway wired to the heat pump's RS-485 port (the unit speaks
  RTU at 9600 8N1). Two heat pumps can share a gateway, on separate ports or
  under different unit IDs.

## Installation

**HACS:** add this repository as a custom repository (category: Integration),
install **SpacePak ILAHP**, and restart Home Assistant.

**Manually:** copy `custom_components/spacepak_ilahp` into your
`config/custom_components/` folder and restart.

Then go to **Settings → Devices & services → Add integration → SpacePak
ILAHP** and enter:

- the gateway's host or IP address
- the gateway's TCP port for this heat pump
- the heat pump's Modbus unit ID (installer parameter H10, default 1)

Add one entry per heat pump.

## What you get

| Entity | Notes |
| :--- | :--- |
| Outlet, inlet, outdoor, room and hot water tank temperatures | °C, convert in the UI as you like |
| Coil, suction and discharge temperatures | Diagnostic |
| AC input current, compressor frequency | |
| Compressor current, voltages, target frequency, water flow | Diagnostic |
| Current mode | Cooling, heating, defrost, sterilize or hot water |
| Operating mode | The mode the unit is set to, read-only |
| Compressor running time | Keeps its last value while the unit is offline |
| Running, Compressor, Alarm output, Fault | Binary sensors |
| Power | Switch |
| Heating and cooling target temperature | Bounded by the unit's own configured limits (R08-R11) |
| Load outputs, failure registers 1-9 | Raw words, diagnostic, disabled by default |

The diagnostics download includes every register read, undecoded, and the
decoded list of active faults. Attach it to an issue about a wrong value.

## Upgrading from 0.1

- Config entries migrate on their own. The unique ID now includes the Modbus
  unit ID, so two heat pumps on one gateway port no longer collide.
- Entity unique IDs are unchanged, so history carries over.
- The raw "Mode" sensor is gone. The **Operating mode** sensor decodes the
  same register (1012). Delete the old entity once it shows as unavailable.
- Currents, voltages and running hours are now decoded as unsigned, per the
  manual. Values above 3276.7 A (or 32767 h) used to wrap negative.

## Known limitations

- Failure register 3 has no published bit table. A set bit there is reported
  as `failure_3_bit_<n>`.
- The mode and the installer parameters are not writable, on purpose.

## Development

```bash
scripts/setup      # install Home Assistant and the dev requirements
scripts/develop    # run Home Assistant with this integration
python -m pytest   # the custom integration's tests
scripts/lint
```

To change the integration, edit `core/` (and the library, in its own
repository), then regenerate the custom integration:

```bash
python scripts/vendor.py --library ../spacepak-modbus --version 0.2.0
scripts/lint
```

## License

[Unlicense](LICENSE): public domain.
