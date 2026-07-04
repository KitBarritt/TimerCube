"""
LiPo battery voltage reader for Raspberry Pi Pico W / Pico 2 W.

VSYS is measured via ADC channel 3 (GPIO29), which sits behind a ÷3 voltage
divider on the Pico W hardware.  GPIO29 is shared with the CYW43 WiFi SPI
clock, so GPIO25 (SPI CS) must be briefly pulled high to disconnect the WiFi
chip from the bus before the ADC can read it.  The interruption is <2 ms and
safe to call while WiFi is active.

Typical LiPo thresholds used here:
  4.20 V  →  100 %   (fully charged)
  3.70 V  →   50 %   (nominal resting voltage)
  3.00 V  →    0 %   (treat as discharged — do not discharge further)
"""

import machine
import time

_FACTOR  = 3 * 3.3 / 65535   # ÷3 hardware divider, 3.3 V reference, 16-bit ADC
_FULL_V  = 4.2
_EMPTY_V = 3.0


def read_voltage():
    """Return VSYS voltage as a float (volts, 2 dp), or None on error.

    Briefly disables the CYW43 SPI bus by asserting GPIO25 high, takes the
    ADC reading, then restores GPIO25 to its WiFi alt-function.
    """
    try:
        # Pull GPIO25 (CYW43 SPI CS) high to park the WiFi SPI bus
        machine.Pin(25, machine.Pin.OUT, value=1)
        time.sleep_ms(1)
        v = machine.ADC(29).read_u16() * _FACTOR
        # Return GPIO25 to output-low (idle SPI CS state).
        # The CYW43 driver reconfigures it automatically on next WiFi transaction.
        machine.Pin(25, machine.Pin.OUT, value=0)
        return round(v, 2)
    except Exception as e:
        print('battery read error:', e)
        return None


def voltage_to_percent(v):
    """Convert a voltage reading to an integer percentage (0–100), clamped."""
    if v is None:
        return None
    pct = 100.0 * (v - _EMPTY_V) / (_FULL_V - _EMPTY_V)
    return max(0, min(100, round(pct)))


def status(v):
    """Return a dict with voltage, percent, and a colour hint for the UI."""
    pct = voltage_to_percent(v)
    if pct is None:
        colour = 'unknown'
    elif pct >= 50:
        colour = 'green'
    elif pct >= 20:
        colour = 'amber'
    else:
        colour = 'red'
    return {'voltage': v, 'percent': pct, 'colour': colour}
