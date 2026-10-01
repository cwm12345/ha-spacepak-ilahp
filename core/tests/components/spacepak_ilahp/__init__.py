"""Tests for the SpacePak ILAHP integration."""

# Written by Claude, guided by Chris.

from modbus_connection.mock import MockModbusUnit

from homeassistant.const import CONF_HOST, CONF_PORT

MOCK_HOST = "192.0.2.10"
MOCK_USER_INPUT = {CONF_HOST: MOCK_HOST, CONF_PORT: 502, "unit_id": 1}
MOCK_UNIQUE_ID = f"{MOCK_HOST}:502:1"

# A unit heating on a cold day, compressor and water pump running.
HOLDING: dict[int, int] = {
    1011: 1,  # on
    1012: 1,  # operating mode: heating
    1021: 1,  # H05 cooling enabled
    1023: 1,  # H07 field-wired control
    1028: 0,  # H28 hot water function off
    1030: 0,  # H22 silence mode off
    1037: 0xFED4,  # A03 shutdown ambient -30.0 C
    1158: 450,  # heating target 45.0 C
    1159: 70,  # cooling target 7.0 C
    1162: 80,  # min cooling setpoint 8.0 C
    1163: 280,  # max cooling setpoint 28.0 C
    1164: 150,  # min heating setpoint 15.0 C
    1165: 500,  # max heating setpoint 50.0 C
    1160: 20,  # R04 heating restart difference 2.0 K
    1161: 20,  # R05 heating stop difference 2.0 K
    1167: 0xFF4E,  # R29 low-ambient compensation start -17.8 C
    1168: 0xFF17,  # R30 low-ambient compensation end -23.3 C
    1169: 406,  # R31 low-ambient heating target 40.6 C
    1174: 20,  # R06 cooling restart difference 2.0 K
    1175: 25,  # R07 cooling stop difference 2.5 K
    1192: 100,  # R39 heating restart ambient 10.0 C
    1197: 1,  # P01 pump mode economic
    1198: 30,  # P02 idle pump interval 30 min
    1199: 3,  # P03 idle pump run time 3 min
    1219: 30,  # C02 compressor min 30 Hz
    1220: 90,  # C03 compressor max 90 Hz
    1234: 10,  # weather compensation slope 1.0
    1235: 200,  # weather compensation offset 20.0 C
    1236: 0,  # weather compensation off
    2011: 1,  # running
    2012: 1,  # heating
    2013: 450,  # target after limits 45.0 C
    2014: 0,  # compensated target: 0 while compensation is off
    2019: 0x0011,  # compressor + water pump
    2032: 12345,  # compressor hours
    2034: 0x0000,  # every field input closed: enabled, heating, flow made
    2042: 105,  # compressor current 10.5 A
    2043: 380,  # DC bus 380 V
    2045: 380,  # inlet 38.0 C
    2046: 432,  # outlet 43.2 C
    2047: 0,  # tank 0.0 C
    2048: 0xFF9C,  # ambient -10.0 C
    2049: 0xFFB0,  # coil -8.0 C
    2051: 0xFFE2,  # suction -3.0 C
    2053: 715,  # discharge 71.5 C
    2057: 142,  # AC input 14.2 A
    2062: 238,  # AC input 238 V
    2071: 62,  # compressor target 62 Hz
    2072: 60,  # compressor running 60 Hz
    **dict.fromkeys(range(2081, 2091), 0),  # no faults
}


def seed_heat_pump(unit: MockModbusUnit) -> None:
    """Seed a mock unit as a heating ILAHP heat pump."""
    for address, value in HOLDING.items():
        unit.holding[address] = value
