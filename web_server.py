"""
Async HTTP + WebSocket server for the Stellar Unicorn Toast Timer.
- Serves static files from /public/
- /ws  → WebSocket endpoint (timer commands & state broadcasts)
- /api/speakers, /api/config, /api/info, /api/version, /api/device-id → REST endpoints
- Captive-portal probe paths → redirect to /
"""

import asyncio
import gc
import hashlib
import binascii
import json
import os
import time

import battery as _batt
from timer_state import PRESETS

DIAG = False   # set True to enable heap reports and matrix loop lag warnings

_WS_MAGIC = b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'


def _state_msg(state):
    """Merge {'type':'state'} with state dict without ** unpacking (MicroPython)."""
    d = {'type': 'state'}
    d.update(state)
    return json.dumps(d)

_CHUNK    = 4096          # bytes per file-send chunk
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
        'Cache-Control: max-age=60\r\n'
        'Connection: close\r\n\r\n'
    ).encode()
    writer.write(hdr)
    with open(path, 'rb') as f:
        while True:
            chunk = f.read(_CHUNK)
            if not chunk:
                break
            writer.write(chunk)
    await writer.drain()   # single drain after all chunks — faster than per-chunk


async def _send_redirect(writer, url):
    writer.write(
        f'HTTP/1.1 302 Found\r\nLocation: {url}\r\nContent-Length: 0\r\nConnection: close\r\n\r\n'
        .encode()
    )
    await writer.drain()


async def _send_404(writer):
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
        # Battery – take an initial reading at startup; refreshed every 60 s
        self._batt = _batt.status(_batt.read_voltage())

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
        """Push timer state to all WebSocket clients every 0.5 s.
        Refreshes battery reading every 60 s and broadcasts it to all clients.
        Sends a WebSocket ping every 30 s to keep mobile connections alive.
        Also prints a heap report every 10 s (20 ticks) when DIAG is enabled."""
        tick = 0
        while True:
            tick += 1
            if DIAG and tick % 20 == 0:
                gc.collect()
                print(f'[mem] heap free={gc.mem_free()}  alloc={gc.mem_alloc()}'
                      f'  ws_clients={len(self._clients)}')
            # WebSocket ping every 60 ticks (30 s) — keeps mobile connections
            # alive when the screen locks or the device enters power-save mode.
            if tick % 60 == 0 and self._clients:
                dead = set()
                for w in list(self._clients):
                    try:
                        w.write(b'\x89\x00')   # FIN=1, opcode=9 (ping), len=0
                        await w.drain()
                    except Exception:
                        dead.add(w)
                self._clients -= dead
                for w in dead:   # send TCP FIN so browser onclose fires immediately
                    try: w.close()
                    except Exception: pass
            # Refresh battery every 120 ticks (60 s)
            if tick % 120 == 0:
                v = _batt.read_voltage()
                self._batt = _batt.status(v)
                if self._clients:
                    msg = json.dumps({'type': 'battery', 'battery': self._batt})
                    for w in list(self._clients):
                        try:
                            await _ws_send(w, msg)
                        except Exception:
                            pass
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
                for w in dead:   # send TCP FIN so browser onclose fires immediately
                    try: w.close()
                    except Exception: pass
            await asyncio.sleep(0.5)

    async def _matrix_loop(self):
        """Update the LED matrix to reflect the current timer colour."""
        from led_matrix import GREEN, AMBER, RED, BLUE, WHITE
        flash_on  = True
        _last_tick = time.ticks_ms()
        ip_seq        = []   # idle scroll: list of strings + None (blank) entries
        ip_idx        = 0    # current position in ip_seq
        ip_tick       = 0    # 0.5 s ticks at current position (2 ticks = 1 s)
        last_ip       = ''   # detect IP/mode changes so sequence is rebuilt
        last_mode     = ''
        ip_brightness = 0.15 # dim brightness for idle scroll (0.0–1.0)
        # Grace period: after the last client disconnects, keep showing the
        # timer colour for this many ms before falling back to the idle scroll.
        _GRACE_MS        = 60_000
        _last_had_client = time.ticks_ms() - _GRACE_MS - 1  # expired at boot

        while True:
            try:
                # Lag detector: warn if the loop fires >40% late (>700 ms)
                now        = time.ticks_ms()
                lag        = time.ticks_diff(now, _last_tick)
                _last_tick = now
                if DIAG and lag > 700:
                    print(f'[warn] matrix loop lag {lag} ms')

                # Keep track of the last time a client was connected so that a
                # brief disconnect (phone screen lock, momentary network blip)
                # doesn't immediately flip back to the idle animation.
                if self._clients:
                    _last_had_client = now
                _grace_expired = time.ticks_diff(now, _last_had_client) > _GRACE_MS

                state  = self.timer.get_state()
                colour = state['colour']

                # Idle conditions: AP always shows when colour is off/stopped;
                # client mode waits for grace period to expire first.
                idle_ap     = (self.mode == 'ap'     and colour == 'off' and not state['running'])
                idle_client = (self.mode == 'client' and colour == 'off' and not state['running']
                               and not self._clients and _grace_expired)

                if idle_ap or idle_client:
                    # Rebuild sequence when IP or mode changes.
                    # AP:     AP · octet1 · octet2 · octet3 · octet4 · blank · blank
                    # Client: IP · octet1 · octet2 · octet3 · octet4 · blank · blank
                    if self.ip != last_ip or self.mode != last_mode:
                        last_ip   = self.ip
                        last_mode = self.mode
                        octets    = self.ip.split('.')
                        prefix    = 'AP' if self.mode == 'ap' else 'IP'
                        ip_seq    = [prefix] + octets + [None, None]
                        ip_idx    = 0
                        ip_tick   = 0
                    if ip_seq:
                        item = ip_seq[ip_idx]
                        if item is None:
                            self.matrix.clear()
                        else:
                            _b = self.matrix.brightness
                            self.matrix.brightness = ip_brightness
                            col = AMBER if self.mode == 'ap' else WHITE
                            self.matrix.show_string(item, col)
                            self.matrix.brightness = _b
                        ip_tick += 1
                        if ip_tick >= 2:        # advance after 1 s (2 × 0.5 s)
                            ip_tick = 0
                            ip_idx  = (ip_idx + 1) % len(ip_seq)

                else:
                    # Reset animation so it starts fresh next time
                    ip_idx  = 0
                    ip_tick = 0

                    letter_mode = self.config['timer'].get('letter_mode', False)

                    if colour == 'off':
                        if state['running']:
                            self.matrix.dot(BLUE)
                        else:
                            self.matrix.clear()
                    elif colour == 'green':
                        self.matrix.show_large_char('G', GREEN) if letter_mode else self.matrix.fill(GREEN)
                    elif colour == 'amber':
                        self.matrix.show_large_char('A', AMBER) if letter_mode else self.matrix.fill(AMBER)
                    elif colour == 'red':
                        self.matrix.show_large_char('R', RED) if letter_mode else self.matrix.fill(RED)
                    elif colour == 'flash':
                        flash_on = not flash_on
                        self.timer.flash_on = flash_on
                        if flash_on:
                            self.matrix.show_large_char('R', RED) if letter_mode else self.matrix.fill(RED)
                        else:
                            self.matrix.clear()
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
            await _ws_send(writer, json.dumps({'type': 'battery',  'battery':  self._batt}))

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

    async def _broadcast(self, text):
        dead = set()
        for w in list(self._clients):
            try:
                await _ws_send(w, text)
            except Exception:
                dead.add(w)
        self._clients -= dead

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
            b = float(msg.get('brightness', 0.5))
            self.timer.brightness = b
            self.matrix.set_brightness(b)
            self.config['timer']['brightness'] = b
            from config import save_config
            save_config(self.config)
        elif t == 'set_letter_mode':
            self.config['timer']['letter_mode'] = bool(msg.get('enabled', False))
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
        elif t == 'save_device_id':
            from config import save_device_id
            ok = save_device_id(msg.get('id', ''))
            await _ws_send(writer, json.dumps({'type': 'device_id_saved', 'ok': ok}))
        elif t == 'reboot':
            await _ws_send(writer, json.dumps({'type': 'rebooting'}))
            await asyncio.sleep(0.8)
            import machine
            machine.reset()
        elif t == 'check_update':
            asyncio.create_task(self._check_update_task(writer))
        elif t == 'do_update':
            asyncio.create_task(self._do_update_task())

    # ── OTA tasks ──────────────────────────────────────────────────────────

    async def _check_update_task(self, writer):
        try:
            from version import VERSION, GITHUB_REPO, GITHUB_BRANCH
            import ota_updater
            remote, is_newer = ota_updater.is_update_available(GITHUB_REPO, GITHUB_BRANCH)
            await _ws_send(writer, json.dumps({
                'type': 'update_status',
                'current': VERSION,
                'remote': remote,
                'is_newer': is_newer,
            }))
        except Exception as e:
            await _ws_send(writer, json.dumps({'type': 'ota_error', 'message': str(e)}))

    async def _do_update_task(self):
        async def progress(**kwargs):
            kwargs['type'] = 'ota_progress'
            await self._broadcast(json.dumps(kwargs))
            await asyncio.sleep(0)   # yield so WebSocket frame is sent

        downloaded = []
        try:
            from version import GITHUB_REPO, GITHUB_BRANCH
            import ota_updater

            await progress(phase='fetch_manifest', message='Fetching file list…')
            files = ota_updater.fetch_manifest(GITHUB_REPO, GITHUB_BRANCH)
            total = len(files)

            for i, rel_path in enumerate(files):
                await progress(phase='download', file=rel_path, n=i + 1, total=total)
                dev_path = ota_updater.download_file(GITHUB_REPO, GITHUB_BRANCH, rel_path)
                downloaded.append(dev_path)

            await progress(phase='install', message='Installing update…')
            backed_up = ota_updater.install_files(downloaded)

            await progress(phase='cleanup', message='Cleaning up…')
            ota_updater.cleanup_backups(backed_up)

            await progress(phase='done', message='Update complete. Rebooting…')
            await asyncio.sleep(2)
            import machine
            machine.reset()

        except Exception as e:
            ota_updater.abort_download(downloaded)
            await self._broadcast(json.dumps({'type': 'ota_error', 'message': str(e)}))

    # ── HTTP ───────────────────────────────────────────────────────────────

    async def _handle_http(self, method, path, body, writer):
        # Strip query string
        path = path.split('?')[0]

        # ── REST API ───────────────────────────────────────────────────────

        if path == '/api/version':
            from version import VERSION, VERSION_DATE
            await _send_json(writer, {'version': VERSION, 'date': VERSION_DATE})
            return

        if path == '/api/device-id':
            from config import read_device_id
            if method == 'GET':
                await _send_json(writer, {'id': read_device_id()})
            return

        if path == '/api/info':
            await _send_json(writer, {
                'ip':      self.ip,
                'mode':    self.mode,
                'ap_ssid': self.config['wifi'].get('ap_ssid', 'ToastTimer'),
                'url':     f'http://{self.ip}/',
                'battery': self._batt,
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
