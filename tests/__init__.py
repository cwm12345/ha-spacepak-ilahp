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
    1028: 0,  # H28 hot water function off
    1158: 450,  # heating target 45.0 C
    1159: 70,  # cooling target 7.0 C
    1162: 80,  # min cooling setpoint 8.0 C
    1163: 280,  # max cooling setpoint 28.0 C
    1164: 150,  # min heating setpoint 15.0 C
    1165: 500,  # max heating setpoint 50.0 C
    2011: 1,  # running
    2012: 1,  # heating
    2019: 0x0011,  # compressor + water pump
    2032: 12345,  # compressor hours
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
