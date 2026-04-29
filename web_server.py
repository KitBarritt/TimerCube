"""
Async HTTP + WebSocket server for the ESP32 TimerCube.
- Serves static files from /public/
- /ws  → WebSocket endpoint (timer commands & state broadcasts)
- /api/speakers, /api/config, /api/info → REST endpoints
- Captive-portal probe paths → redirect to /
"""

import asyncio
import hashlib
import binascii
import json
import os

from timer_state import PRESETS

_WS_MAGIC = b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'


def _state_msg(state):
    """Merge {'type':'state'} with state dict without ** unpacking (MicroPython)."""
    d = {'type': 'state'}
    d.update(state)
    return json.dumps(d)
_CHUNK    = 1024          # bytes per file-send chunk
_SPEAKERS = '/data/speakers.json'


# ── WebSocket frame helpers ────────────────────────────────────────────────

def _ws_accept(key):
    digest = hashlib.sha1((key + '258EAFA5-E914-47DA-95CA-C5AB0DC85B11').encode()).digest()
    return binascii.b2a_base64(digest).decode().strip()


async def _ws_recv(reader):
    """Read one WebSocket frame; return (opcode, text_or_bytes)."""
    try:
        hdr = await reader.read(2)
        if len(hdr) < 2:
            return None, None
        opcode = hdr[0] & 0x0F
        masked = bool(hdr[1] & 0x80)
        length = hdr[1] & 0x7F
        if length == 126:
            ext = await reader.read(2)
            length = (ext[0] << 8) | ext[1]
        elif length == 127:
            return None, None   # too large for our purposes
        mask = await reader.read(4) if masked else None
        data = await reader.read(length)
        if masked and mask:
            data = bytes(data[i] ^ mask[i % 4] for i in range(len(data)))
        return opcode, (data.decode('utf-8') if opcode == 1 else data)
    except Exception:
        return None, None


async def _ws_send(writer, text):
    data = text.encode('utf-8') if isinstance(text, str) else text
    n = len(data)
    if n < 126:
        writer.write(bytes([0x81, n]))
    else:
        writer.write(bytes([0x81, 126, n >> 8, n & 0xFF]))
    writer.write(data)
    await writer.drain()


# ── HTTP helpers ───────────────────────────────────────────────────────────

def _ctype(path):
    if path.endswith('.html'): return 'text/html; charset=utf-8'
    if path.endswith('.css'):  return 'text/css'
    if path.endswith('.js'):   return 'application/javascript'
    if path.endswith('.json'): return 'application/json'
    return 'application/octet-stream'


async def _send_json(writer, obj, status=200):
    body = json.dumps(obj).encode()
    hdr  = (
        f'HTTP/1.1 {status} OK\r\n'
        'Content-Type: application/json\r\n'
        f'Content-Length: {len(body)}\r\n'
        'Connection: close\r\n\r\n'
    ).encode()
    writer.write(hdr + body)
    await writer.drain()


async def _send_file(writer, path):
    size = os.stat(path)[6]
    hdr  = (
        'HTTP/1.1 200 OK\r\n'
        f'Content-Type: {_ctype(path)}\r\n'
        f'Content-Length: {size}\r\n'
        'Cache-Control: max-age=3600\r\n'
        'Connection: close\r\n\r\n'
    ).encode()
    writer.write(hdr)
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(_CHUNK)
            if not chunk:
                break
            writer.write(chunk)
            await writer.drain()


async def _send_redirect(writer, url):
    writer.write(
        f'HTTP/1.1 302 Found\r\nLocation: {url}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n'
        .encode()
    )
    await writer.drain()


async def _send_404(writer):
    body = b'Not found'
    writer.write(
        b'HTTP/1.1 404 Not Found\r\nContent-Type: text/plain\r\nContent-Length: 9\r\nConnection: close\r\n\r\nNot found'
    )
    await writer.drain()


# ── Main server class ──────────────────────────────────────────────────────

class WebServer:
    def __init__(self, timer, config, matrix, ip, mode):
        self.timer    = timer
        self.config   = config
        self.matrix   = matrix
        self.ip       = ip
        self.mode     = mode
        self._clients = set()          # active WebSocket StreamWriter objects
        self.speakers = self._load_speakers()

    # ── lifecycle ──────────────────────────────────────────────────────────

    async def start(self):
        asyncio.create_task(self._broadcast_loop())
        asyncio.create_task(self._matrix_loop())
        await asyncio.start_server(self._handle_conn, '0.0.0.0', 80)
        print(f'HTTP server listening on {self.ip}:80')
        while True:
            await asyncio.sleep(3600)

    # ── background tasks ───────────────────────────────────────────────────

    async def _broadcast_loop(self):
        """Push timer state to all WebSocket clients every 0.5 s."""
        while True:
            if self._clients:
                state = self.timer.get_state()
                msg   = _state_msg(state)
                dead  = set()
                for w in list(self._clients):
                    try:
                        await _ws_send(w, msg)
                    except Exception:
                        dead.add(w)
                self._clients -= dead
            await asyncio.sleep(0.5)

    async def _matrix_loop(self):
        """Update the LED matrix to reflect the current timer colour."""
        from led_matrix import GREEN, AMBER, RED, BLUE, WHITE
        flash_on = True
        ip_seq          = []   # IP scroll: list of chars + None (blank) entries
        ip_idx          = 0    # current position in ip_seq
        ip_tick         = 0    # 0.5 s ticks at current position (2 ticks = 1 s)
        last_ip         = ''   # detect IP/mode changes so sequence is rebuilt
        last_mode       = ''
        ip_brightness   = 0.15 # ← adjust this (0.0–1.0) to set IP scroll brightness
        no_client_ticks = 0    # ticks elapsed with no WS clients (debounce)

        while True:
            try:
                state  = self.timer.get_state()
                colour = state['colour']

                if self._clients:
                    no_client_ticks = 0
                else:
                    no_client_ticks += 1

                # Only show IP after 10 ticks (5 s) with no clients, so brief
                # page-navigation gaps don't trigger the animation.
                if colour == 'off' and not state['running'] and no_client_ticks >= 10 and self.mode in ('ap', 'client'):
                    # Idle animation: mode prefix + IP address scroll, one char per second.
                    # AP:     A  P  <IP digits with : between octets>  <2 s blank>
                    # Client: I  P  -  <IP digits>  <2 s blank>
                    if self.ip != last_ip or self.mode != last_mode:
                        last_ip   = self.ip
                        last_mode = self.mode
                        if self.mode == 'ap':
                            ip_seq = (['A', 'P']
                                      + list(self.ip.replace('.', ':'))
                                      + [None, None, None, None])
                        else:
                            ip_seq = (['I', 'P', '-']
                                      + list(self.ip.replace('.', ':'))
                                      + [None, None, None, None])
                        ip_idx  = 0
                        ip_tick = 0
                    if ip_seq:
                        ch = ip_seq[ip_idx]
                        if ch is None:
                            self.matrix.clear()
                        else:
                            _b = self.matrix.brightness
                            self.matrix.brightness = ip_brightness
                            col = AMBER if self.mode == 'ap' else WHITE
                            self.matrix.show_char(ch, col)
                            self.matrix.brightness = _b
                        ip_tick += 1
                        if ip_tick >= 2:        # advance after 1 s (2 × 0.5 s)
                            ip_tick = 0
                            ip_idx  = (ip_idx + 1) % len(ip_seq)

                else:
                    # Reset animation so it starts fresh next time
                    ip_idx   = 0
                    ip_tick  = 0

                    if colour == 'off':
                        if state['running']:
                            self.matrix.dot(BLUE)
                        else:
                            self.matrix.clear()
                    elif colour == 'green':
                        self.matrix.fill(GREEN)
                    elif colour == 'amber':
                        self.matrix.fill(AMBER)
                    elif colour == 'red':
                        self.matrix.fill(RED)
                    elif colour == 'flash':
                        flash_on = not flash_on
                        self.timer.flash_on = flash_on
                        self.matrix.fill(RED) if flash_on else self.matrix.clear()
            except Exception as e:
                print('Matrix loop error:', e)

            await asyncio.sleep(0.5)

    # ── connection handler ─────────────────────────────────────────────────

    async def _handle_conn(self, reader, writer):
        try:
            line = await reader.readline()
            if not line:
                return
            parts = line.decode().strip().split(' ')
            if len(parts) < 2:
                return
            method, path = parts[0], parts[1]

            headers = {}
            while True:
                hline = await reader.readline()
                hline = hline.decode().strip()
                if not hline:
                    break
                if ':' in hline:
                    k, v = hline.split(':', 1)
                    headers[k.strip().lower()] = v.strip()

            if headers.get('upgrade', '').lower() == 'websocket':
                await self._handle_ws(reader, writer, headers)
                return

            body = b''
            cl = int(headers.get('content-length', 0))
            if cl:
                body = await reader.read(cl)

            await self._handle_http(method, path, body, writer)
        except Exception as e:
            print('Connection error:', e)
        finally:
            try:
                writer.close()
                await writer.wait_closed()
            except Exception:
                pass

    # ── WebSocket ──────────────────────────────────────────────────────────

    async def _handle_ws(self, reader, writer, headers):
        key    = headers.get('sec-websocket-key', '')
        accept = _ws_accept(key)
        writer.write(
            ('HTTP/1.1 101 Switching Protocols\r\n'
             'Upgrade: websocket\r\nConnection: Upgrade\r\n'
             f'Sec-WebSocket-Accept: {accept}\r\n\r\n').encode()
        )
        await writer.drain()
        self._clients.add(writer)

        try:
            # Send initial snapshot
            state = self.timer.get_state()
            await _ws_send(writer, _state_msg(state))
            await _ws_send(writer, json.dumps({'type': 'speakers', 'speakers': self.speakers}))
            await _ws_send(writer, json.dumps({'type': 'config',   'config':   self.config}))
            await _ws_send(writer, json.dumps({'type': 'presets',  'presets':  PRESETS}))

            while True:
                opcode, data = await _ws_recv(reader)
                if opcode is None or opcode == 8:   # close
                    break
                if opcode == 1:
                    try:
                        await self._handle_ws_msg(json.loads(data), writer)
                    except Exception as e:
                        print('WS msg error:', e)
        except Exception:
            pass
        finally:
            self._clients.discard(writer)

    async def _handle_ws_msg(self, msg, writer):
        t = msg.get('type')

        if t == 'start':
            self.timer.start()
        elif t == 'stop':
            self.timer.stop()
            state = self.timer.get_state()
            if state['elapsed'] > 0 and state['speaker']:
                self._record_actual(state['speaker'], state['elapsed'])
        elif t == 'reset':
            self.timer.reset()
        elif t == 'set_colour':
            self.timer.set_colour(msg.get('colour', 'off'))
        elif t == 'set_thresholds':
            self.timer.set_thresholds(msg.get('thresholds', [0, 0, 0, 0]))
        elif t == 'set_speaker':
            self.timer.speaker = msg.get('speaker', '')
        elif t == 'set_brightness':
            b = float(msg.get('brightness', 0.6))
            self.timer.brightness = b
            self.matrix.set_brightness(b)
            self.config['timer']['brightness'] = b
            from config import save_config
            save_config(self.config)
        elif t == 'get_state':
            state = self.timer.get_state()
            await _ws_send(writer, _state_msg(state))
        elif t == 'get_speakers':
            await _ws_send(writer, json.dumps({'type': 'speakers', 'speakers': self.speakers}))
        elif t == 'save_speakers':
            self.speakers = msg.get('speakers', [])
            self._save_speakers()
        elif t == 'clear_actuals':
            for s in self.speakers:
                s['actual'] = None
            self._save_speakers()
        elif t == 'get_config':
            await _ws_send(writer, json.dumps({'type': 'config', 'config': self.config}))
        elif t == 'save_config':
            new_cfg = msg.get('config', {})
            wifi_changed = False
            for k in ('wifi', 'timer'):
                if k in new_cfg:
                    self.config[k].update(new_cfg[k])
                    if k == 'wifi':
                        wifi_changed = True
            if 'language' in new_cfg:
                self.config['language'] = new_cfg['language']
            from config import save_config
            save_config(self.config)
            await _ws_send(writer, json.dumps({'type': 'config_saved', 'ok': True}))
            # Only reconnect WiFi when WiFi settings actually changed
            if wifi_changed:
                asyncio.create_task(self._reconnect_wifi())
        elif t == 'reboot':
            await _ws_send(writer, json.dumps({'type': 'rebooting'}))
            await asyncio.sleep(0.8)
            import machine
            machine.reset()

    # ── HTTP ───────────────────────────────────────────────────────────────

    async def _handle_http(self, method, path, body, writer):
        # Strip query string
        path = path.split('?')[0]

        # ── REST API ───────────────────────────────────────────────────────

        if path == '/api/info':
            await _send_json(writer, {
                'ip':   self.ip,
                'mode': self.mode,
                'ap_ssid': self.config['wifi'].get('ap_ssid', 'TimerCube'),
                'url':  f'http://{self.ip}/',
            })
            return

        if path == '/api/speakers' and method == 'GET':
            await _send_json(writer, self.speakers)
            return

        if path == '/api/config' and method == 'GET':
            await _send_json(writer, self.config)
            return

        if path == '/api/wifi-scan' and method == 'GET':
            try:
                import network as _net
                sta = _net.WLAN(_net.STA_IF)
                was_active = sta.active()
                sta.active(True)
                raw = sta.scan()
                seen = set()
                nets = []
                for r in raw:
                    try:
                        ssid = r[0].decode('utf-8') if isinstance(r[0], bytes) else str(r[0])
                    except Exception:
                        ssid = ''
                    if ssid and ssid not in seen:
                        seen.add(ssid)
                        nets.append({'ssid': ssid, 'rssi': r[3], 'auth': r[4]})
                nets.sort(key=lambda x: -x['rssi'])
                if not was_active:
                    sta.active(False)
            except Exception as e:
                print('WiFi scan error:', e)
                nets = []
            await _send_json(writer, nets)
            return

        # ── Captive-portal probes ──────────────────────────────────────────
        if path in ('/hotspot-detect.html', '/generate_204',
                    '/connecttest.txt', '/ncsi.txt',
                    '/success.txt', '/redirect'):
            await _send_redirect(writer, f'http://{self.ip}/')
            return

        # ── Static files ───────────────────────────────────────────────────
        if path == '/':
            path = '/index.html'

        file_path = '/public' + path

        try:
            os.stat(file_path)
            await _send_file(writer, file_path)
        except OSError:
            await _send_404(writer)

    # ── helpers ────────────────────────────────────────────────────────────

    def _load_speakers(self):
        try:
            with open(_SPEAKERS) as f:
                return json.load(f)
        except Exception:
            return []

    def _save_speakers(self):
        try:
            os.mkdir('/data')
        except OSError:
            pass
        with open(_SPEAKERS, 'w') as f:
            json.dump(self.speakers, f)

    def _record_actual(self, name, elapsed):
        for s in self.speakers:
            if s.get('name') == name and s.get('actual') is None:
                s['actual'] = round(elapsed)
                self._save_speakers()
                return

    async def _reconnect_wifi(self):
        await asyncio.sleep(1)
        from wifi_manager import connect_wifi
        try:
            self.ip, self.mode, _ = await connect_wifi(self.config, self.matrix)
        except Exception as e:
            print('WiFi reconnect error:', e)
