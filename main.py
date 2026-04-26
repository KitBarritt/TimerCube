"""
TimerCube – ESP32-S3-Matrix entry point.
MicroPython asyncio: WiFi → HTTP+WS server → LED matrix loop.
"""

import asyncio
import network

from config       import load_config
from led_matrix   import Matrix
from timer_state  import Timer
from wifi_manager import connect_wifi
from web_server   import WebServer


async def main():
    # Set a friendly hostname (visible in DHCP & some mDNS clients)
    try:
        network.hostname('timercube')
    except Exception:
        pass

    config = load_config()
    matrix = Matrix()
    matrix.set_brightness(config['timer']['brightness'])
    matrix.clear()

    print('TimerCube starting…')

    # Connect to WiFi (or start AP hotspot)
    ip, mode, _iface = await connect_wifi(config, matrix)
    print(f'Network ready: mode={mode}  ip={ip}')
    print(f'  Open http://{ip}/ in a browser')

    timer  = Timer(config)
    server = WebServer(timer, config, matrix, ip, mode)
    await server.start()   # runs forever


asyncio.run(main())
