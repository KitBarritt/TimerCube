# TimerCube

A Toastmasters speech timer built on the [Waveshare ESP32-S3-Matrix](https://www.waveshare.com/esp32-s3-matrix.htm) — an ESP32-S3 development board with a built-in 8×8 WS2812B RGB LED matrix.

The device runs a web server you connect to from any phone or laptop on the same network. No app required.

![Green amber red LED matrix stages]

---

## Features

- **Traffic-light timing** — matrix fills green → amber → red → flashing red as each speech stage elapses
- **Speaker list** — enter speakers with their individual time targets; the timer picks up the right thresholds automatically
- **Timing report** — colour-coded summary of every speaker's result for the evening
- **Multi-language UI** — English, Français, Deutsch, Español
- **WiFi fallback** — if no saved network is in range the device starts its own access point (hotspot)
- **Over-the-air updates** — update the firmware from the Settings page without touching a USB cable
- **Captive portal** — connecting to the AP hotspot opens the timer page automatically on most devices

---

## Hardware

| Part | Notes |
|---|---|
| Waveshare ESP32-S3-Matrix | The 8×8 version. Available directly from Waveshare or via distributors. |
| USB-C cable + power supply | Any 5 V / 1 A USB supply works. A phone charger is ideal for table use. |
| Optional: 3D-printed case | STL and SCAD files are in the [`Case/`](Case/) folder. |

---

## Initial Setup

### 1 — Flash MicroPython

If the board doesn't already have MicroPython on it:

1. Download the latest ESP32-S3 MicroPython firmware from [micropython.org/download/ESP32_GENERIC_S3](https://micropython.org/download/ESP32_GENERIC_S3/)
2. Install [esptool](https://github.com/espressif/esptool): `pip install esptool`
3. Erase and flash:

```bash
esptool.py --chip esp32s3 erase_flash
esptool.py --chip esp32s3 --baud 460800 write_flash -z 0 ESP32_GENERIC_S3-*.bin
```

### 2 — Upload the TimerCube files

Use [Thonny](https://thonny.org) (easiest), [mpremote](https://pypi.org/project/mpremote/), or any MicroPython IDE.

Upload these files and folders to the **root** of the device filesystem:

```
main.py
web_server.py
timer_state.py
config.py
wifi_manager.py
led_matrix.py
ddns.py
ota_updater.py
version.py
manifest.json
public/          (upload the whole folder)
```

Do **not** upload `config.json` — it will be created automatically on first boot.

### 3 — Connect and configure

1. Power the device. After a few seconds the LED matrix scrolls `AP` followed by an IP address — this is the fallback hotspot.
2. On your phone or laptop, connect to the WiFi network **TimerCube** (password: `toastmaster`).
3. A browser should open automatically (captive portal). If not, navigate to the IP address shown on the matrix.
4. Go to **Settings → WiFi Networks**, add your home or club WiFi, and tap **Save & Connect**.
5. The device will connect and the matrix will scroll `IP` followed by its new address.

---

## Using the Timer

Open the device's IP address in any browser on the same network.

| Page | Purpose |
|---|---|
| **Timer** | Start / stop / reset, colour override, speaker select |
| **Speakers** | Add speakers with their green / amber / red time thresholds |
| **Report** | Post-meeting timing summary with colour badges |
| **Settings** | WiFi, brightness, language, firmware update |

The LED matrix mirrors the current timer colour in real time, visible from across the room.

---

## Updating the Firmware (OTA)

Once the device is connected to WiFi you can update it without a USB cable:

1. Open **Settings** in the browser.
2. Scroll to **Firmware Update** and tap **Check for Update**.
3. If a newer version is available, tap **Update…** and read the warning.
4. Tap **Update Now** — keep the device powered. Progress is shown line by line.
5. The device reboots automatically when the update is complete.

> **Keep the device powered throughout.** A power loss mid-update can leave the firmware in a partially-updated state.

---

## Project Structure

```
TimerCube/
├── main.py              Entry point — WiFi, timer, web server
├── web_server.py        Async HTTP + WebSocket server
├── timer_state.py       Timer state machine and colour thresholds
├── config.py            Config load / save (config.json)
├── wifi_manager.py      WiFi connect with captive-portal DNS
├── led_matrix.py        WS2812B 8×8 matrix driver
├── ddns.py              DDNS registration via Cloudflare Worker
├── ota_updater.py       OTA update helpers
├── version.py           Version number and GitHub repo config
├── manifest.json        List of files included in OTA updates
├── public/              Web UI (HTML, JS, favicon)
├── Case/                3D-printable enclosure (STL + OpenSCAD)
├── Documentation/       Printable user guides (EN/FR/DE)
└── QRCode/              QR codes for quick device access
```

---

## Releasing a New Version

1. Make and test your changes locally.
2. Bump `VERSION` in `version.py` (e.g. `"1.4"` → `"1.5"`).
3. If you added or removed any files, update `manifest.json`.
4. Commit and push to the `main` branch.

Devices will detect the new version the next time a user taps **Check for Update** on the Settings page.

---

## Licence

MIT — do what you like, attribution appreciated.
