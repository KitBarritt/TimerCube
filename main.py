"""
Toast Timer – Pimoroni Stellar Unicorn entry point.
MicroPython asyncio: buttons (boot mode) → USB / BLE / WiFi → HTTP+WS server.

Hardware: Raspberry Pi Pico W + Pimoroni Stellar Unicorn (16×16 WS2812B).
Requires Pimoroni MicroPython firmware (includes stellar + picographics modules).

Boot mode is chosen by which button (if any) is held down at power-on:

  Button A held    → USB serial mode  (web/index.html via Web Serial)
  Button B held    → Bluetooth mode   (web/ble.html   via Web Bluetooth)
  no button held   → WiFi → AP hotspot

USB handshake protocol
  Browser → board : "HELLO\n"
  Board → browser : "READY_OK\n"  then initial-state JSON burst

This handshake is handled both here (first connection) and inside
UsbServer._command_loop (reconnection after page reload).
"""

import asyncio
import gc
import micropython
import sys

DIAG = False   # set True to enable heap/memory diagnostics in the REPL

from config      import load_config
from led_matrix  import Matrix
from timer_state import Timer
from web_server  import WebServer
from stellar     import StellarUnicorn


def _mem(label):
    if not DIAG:
        return
    gc.collect()
    print(f'[mem] {label}: free={gc.mem_free()}  alloc={gc.mem_alloc()}')


# ── boot ───────────────────────────────────────────────────────────────────

async def main():
    config = load_config()
    matrix = Matrix()
    matrix.set_brightness(config['timer']['brightness'])
    matrix.clear()

    print('Toast Timer starting…')
    _mem('after matrix init')

    su = matrix.unicorn
    if su.is_pressed(StellarUnicorn.SWITCH_A):
        # USB-only: wait indefinitely for browser HELLO
        if _usb_handshake(matrix):
            await _run_usb(config, matrix)
        return

    if su.is_pressed(StellarUnicorn.SWITCH_B):
        # BLE mode immediately
        await _run_ble(config, matrix)
        return

    # No button held: WiFi → AP
    _set_hostname()
    from wifi_manager import try_networks
    result = await try_networks(config, matrix)
    if result:
        ip, iface = result
        print('Network ready: mode=client  ip=%s' % ip)
        _ddns_register(ip)
        _mem('after WiFi')
        if DIAG:
            micropython.mem_info()   # full heap/stack breakdown
        timer  = Timer(config)
        server = WebServer(timer, config, matrix, ip, 'client')
        await server.start()
        return

    # WiFi unavailable — start AP hotspot
    await _run_ap(config, matrix)


# ── USB handshake (synchronous, called before asyncio tasks start) ─────────

def _usb_handshake(matrix):
    """
    Show U on the matrix, wait for "HELLO" from the browser, reply "READY_OK".
    Blocks indefinitely.  Returns True on success (always, unless an
    exception escapes).
    """
    from led_matrix import BLUE
    matrix.show_char('U', BLUE)
    while True:
        line = sys.stdin.readline().strip()
        if line == 'HELLO':
            sys.stdout.write('READY_OK\n')
            return True


# ── mode runners ───────────────────────────────────────────────────────────

async def _run_usb(config, matrix):
    from usb_server import UsbServer
    server = UsbServer(config, matrix)
    await server.run()


async def _run_ble(config, matrix):
    from led_matrix import BLUE
    matrix.show_char('B', BLUE)
    from ble_server import BleServer
    server = BleServer(config, matrix)
    await server.run()


async def _run_ap(config, matrix):
    _set_hostname()
    from wifi_manager import start_ap
    ip, iface = await start_ap(config, matrix)
    print('Network ready: mode=ap  ip=%s' % ip)
    timer  = Timer(config)
    server = WebServer(timer, config, matrix, ip, 'ap')
    await server.start()


def _ddns_register(ip):
    try:
        from config import read_device_id
        from ddns_client import register
        device_id = read_device_id()
        if device_id:
            register(device_id, ip)
    except Exception as e:
        print('DDNS setup error:', e)


def _set_hostname():
    try:
        import network
        network.hostname('toasttimer')
    except Exception:
        pass


asyncio.run(main())
