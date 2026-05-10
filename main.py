"""
TimerCube – ESP32-S3-Matrix entry point.

Boot mode is determined by reading the QMI8658 accelerometer at power-on:

  vertical (or unknown)
      → try saved WiFi networks
      → if WiFi fails: show U, wait 5 s for USB HELLO
      → if USB times out: fall back to AP hotspot

  left side down
      → USB-only mode (wait indefinitely for browser HELLO)

  right side down
      → AP hotspot mode immediately (skip WiFi and USB)

USB handshake protocol
  Browser → board : "HELLO\n"
  Board → browser : "READY_OK\n"  then initial-state JSON burst

This handshake is handled both here (first connection) and inside
UsbServer._command_loop (reconnection after page reload).
"""

import asyncio
import sys
import time

from config      import load_config
from led_matrix  import Matrix
from timer_state import Timer
from web_server  import WebServer


# ── boot ───────────────────────────────────────────────────────────────────

async def main():
    config = load_config()
    matrix = Matrix()
    matrix.set_brightness(config['timer']['brightness'])
    matrix.clear()

    print('TimerCube starting…')

    from imu import get_orientation
    orientation = get_orientation()
    print('Orientation:', orientation)

    if orientation == 'left':
        # USB-only: wait indefinitely for browser HELLO
        if _usb_handshake(matrix, timeout_s=None):
            await _run_usb(config, matrix)
        else:
            await _run_ap(config, matrix)   # shouldn't reach here with None timeout

    elif orientation == 'right':
        # AP mode immediately
        await _run_ap(config, matrix)

    else:
        # Vertical / unknown: WiFi → USB (5 s) → AP
        _set_hostname()
        from wifi_manager import try_networks
        result = await try_networks(config, matrix)
        if result:
            ip, iface = result
            print('Network ready: mode=client  ip=%s' % ip)
            timer  = Timer(config)
            server = WebServer(timer, config, matrix, ip, 'client')
            await server.start()
            return

        # WiFi unavailable — try USB for 5 s
        if _usb_handshake(matrix, timeout_s=5):
            await _run_usb(config, matrix)
            return

        # Neither WiFi nor USB — start AP hotspot
        await _run_ap(config, matrix)


# ── USB handshake (synchronous, called before asyncio tasks start) ─────────

def _usb_handshake(matrix, timeout_s):
    """
    Show U on LEDs, wait for "HELLO" from browser, reply "READY_OK".
    timeout_s=None waits forever (left-side USB-only mode).
    Returns True on success, False on timeout.
    """
    from led_matrix import BLUE
    matrix.show_char('U', BLUE)

    if timeout_s is None:
        # Blocking wait — fine for left-side dedicated USB mode
        while True:
            line = sys.stdin.readline().strip()
            if line == 'HELLO':
                sys.stdout.write('READY_OK\n')
                return True
        # unreachable
        return False

    # ── Timeout case (vertical orientation, 5 s window) ──────────────────
    # readline() blocks the calling thread, so we run it in a MicroPython
    # thread and poll the result from the main thread.
    result = [None]

    def _reader():
        while True:
            try:
                ln = sys.stdin.readline().strip()
                if ln == 'HELLO':
                    result[0] = 'HELLO'
                    return
            except Exception:
                return

    import _thread
    _thread.start_new_thread(_reader, ())

    deadline = time.ticks_add(time.ticks_ms(), int(timeout_s * 1000))
    while result[0] is None:
        if time.ticks_diff(deadline, time.ticks_ms()) <= 0:
            return False
        time.sleep_ms(100)

    sys.stdout.write('READY_OK\n')
    return True


# ── mode runners ───────────────────────────────────────────────────────────

async def _run_usb(config, matrix):
    from usb_server import UsbServer
    server = UsbServer(config, matrix)
    await server.run()


async def _run_ap(config, matrix):
    _set_hostname()
    from wifi_manager import start_ap
    ip, iface = await start_ap(config, matrix)
    print('Network ready: mode=ap  ip=%s' % ip)
    timer  = Timer(config)
    server = WebServer(timer, config, matrix, ip, 'ap')
    await server.start()


def _set_hostname():
    try:
        import network
        network.hostname('timercube')
    except Exception:
        pass


asyncio.run(main())
