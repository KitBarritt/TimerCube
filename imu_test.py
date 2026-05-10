"""
QMI8658 live orientation test — SDA=11, SCL=12, addr=0x6B.

Run this in the Thonny REPL (Ctrl-C to stop).
Hold the cube in each position and note what is printed:
  • Upright (vertical)       — should print  orientation=vertical
  • Left side down           — should print  orientation=left
  • Right side down          — should print  orientation=right

If 'left' and 'right' are swapped, edit imu.py and swap the
return values on the line:
    return 'left' if ax < 0 else 'right'
"""

import machine
import time

_SDA  = 11
_SCL  = 12
_ADDR = 0x6B

_CTRL1   = 0x02
_CTRL2   = 0x03
_CTRL7   = 0x08
_STATUS0 = 0x2E
_AX_L    = 0x35

AXIS_THRESHOLD = 600   # ≈ 0.56 g  (1 g ≈ 1060 counts on this board)


def _s16(lo, hi):
    v = (hi << 8) | lo
    return v - 65536 if v >= 32768 else v


def _orientation(ax, ay, az):
    aax, aay, aaz = abs(ax), abs(ay), abs(az)
    dominant = max(aax, aay, aaz)
    if dominant < AXIS_THRESHOLD:
        return 'unknown (near 45° — tilt more)'
    if aay >= aax and aay >= aaz:
        # Y axis runs left/right on this board
        return 'left' if ay < 0 else 'right'
    return 'vertical'   # X or Z dominant → upright


i2c = machine.SoftI2C(sda=machine.Pin(_SDA),
                       scl=machine.Pin(_SCL),
                       freq=400_000)

# Initialise sensor
i2c.writeto_mem(_ADDR, _CTRL1, b'\x40')   # address auto-increment
i2c.writeto_mem(_ADDR, _CTRL2, b'\x60')   # 1 kHz ODR, ±2 g
i2c.writeto_mem(_ADDR, _CTRL7, b'\x03')   # accel + gyro on (both needed)
time.sleep_ms(10)

print('QMI8658 orientation test — hold cube still, Ctrl-C to stop')
print('  1 g ≈ 1060 counts   threshold=%d' % AXIS_THRESHOLD)
print()

while True:
    # Wait for data-ready
    deadline = time.ticks_add(time.ticks_ms(), 200)
    while not (i2c.readfrom_mem(_ADDR, _STATUS0, 1)[0] & 0x01):
        if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
            print('timeout waiting for data-ready')
            break
        time.sleep_ms(2)

    raw = i2c.readfrom_mem(_ADDR, _AX_L, 6)
    ax = _s16(raw[0], raw[1])
    ay = _s16(raw[2], raw[3])
    az = _s16(raw[4], raw[5])

    o = _orientation(ax, ay, az)
    print('ax=%6d  ay=%6d  az=%6d   orientation=%s' % (ax, ay, az, o))

    time.sleep_ms(500)
