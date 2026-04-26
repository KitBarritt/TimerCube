"""
WiFi manager: connect to saved networks in priority order, fall back to AP.
In AP mode also starts a captive-portal DNS server that redirects all queries
to 192.168.4.1 so phones show the "sign in to network" prompt.
"""

import network
import asyncio
import socket
import struct
from led_matrix import BLUE, GREEN, AMBER

_AP_IP = '192.168.4.1'
_dns_running = False


# ── DNS captive-portal server ──────────────────────────────────────────────

def _dns_response(query, ip):
    """Build a minimal DNS A-record response pointing to *ip*."""
    # Transaction ID + flags (response, authoritative)
    resp = bytearray(query[:2]) + b'\x81\x80'
    resp += query[4:6]          # QDCOUNT  (echo questions count)
    resp += query[4:6]          # ANCOUNT  (same)
    resp += b'\x00\x00'         # NSCOUNT
    resp += b'\x00\x00'         # ARCOUNT
    resp += query[12:]          # original question section
    # Answer RR
    resp += b'\xc0\x0c'         # pointer to domain name at offset 12
    resp += b'\x00\x01'         # type A
    resp += b'\x00\x01'         # class IN
    resp += b'\x00\x00\x00\x3c' # TTL 60 s
    resp += b'\x00\x04'         # rdlength
    resp += bytes(int(x) for x in ip.split('.'))
    return bytes(resp)


async def _run_dns(ip):
    """Minimal async UDP DNS server – spoof every query to *ip*."""
    global _dns_running
    if _dns_running:
        return
    _dns_running = True
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind(('0.0.0.0', 53))
    sock.setblocking(False)
    print('DNS captive-portal running, all queries → ', ip)
    try:
        while True:
            try:
                data, addr = sock.recvfrom(512)
                sock.sendto(_dns_response(data, ip), addr)
            except OSError:
                pass
            await asyncio.sleep_ms(50)
    finally:
        _dns_running = False
        sock.close()


# ── WiFi connection ────────────────────────────────────────────────────────

async def connect_wifi(config, matrix):
    """
    Try each saved network in priority order.
    Returns (ip_str, mode_str, iface) where mode is 'client' or 'ap'.
    """
    networks = sorted(
        config['wifi'].get('networks', []),
        key=lambda n: n.get('priority', 99),
    )

    if networks:
        sta = network.WLAN(network.STA_IF)
        sta.active(True)
        print('WiFi: scanning for', len(networks), 'saved network(s)')

        for idx, net in enumerate(networks):
            ssid = net.get('ssid', '')
            pwd  = net.get('password', '')
            n    = str(min(idx + 1, 9))
            matrix.show_two_chars('S', n, BLUE, BLUE)
            print(f'  Trying "{ssid}" …')
            try:
                sta.connect(ssid, pwd)
            except Exception as e:
                print('  connect() error:', e)
                continue

            # Poll up to 15 s
            for _ in range(30):
                await asyncio.sleep(0.5)
                if sta.isconnected():
                    ip = sta.ifconfig()[0]
                    print(f'  Connected! IP={ip}')
                    matrix.show_two_chars('C', n, GREEN, GREEN)
                    await asyncio.sleep(2)
                    return ip, 'client', sta

            sta.disconnect()
            await asyncio.sleep(0.5)
            print('  Timed out.')

        sta.active(False)

    # ── AP fallback ────────────────────────────────────────────────────────
    return await _start_ap(config, matrix)


async def _start_ap(config, matrix):
    ap_ssid = config['wifi'].get('ap_ssid', 'TimerCube')
    ap_pass = config['wifi'].get('ap_password', 'toastmaster')

    ap = network.WLAN(network.AP_IF)
    ap.active(True)

    cfg = {'ssid': ap_ssid}
    if ap_pass:
        cfg['password'] = ap_pass
        cfg['authmode'] = network.AUTH_WPA_WPA2_PSK
    else:
        cfg['authmode'] = network.AUTH_OPEN

    ap.config(**cfg)

    # Wait for AP to be ready
    for _ in range(20):
        if ap.active():
            break
        await asyncio.sleep(0.2)

    ip = ap.ifconfig()[0]
    print(f'AP mode: SSID={ap_ssid}  IP={ip}')
    matrix.show_char('A', AMBER)

    # Start captive-portal DNS in background
    asyncio.create_task(_run_dns(ip))

    return ip, 'ap', ap