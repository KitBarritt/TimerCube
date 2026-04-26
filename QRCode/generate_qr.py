"""
Generate printable QR code PNGs for the Toast Timer.
  qr_wifi.png  — joins the AP hotspot automatically
  qr_url.png   — opens http://toasttimer.local/ in a browser

Run once from the ESP32_timer folder:
    pip install qrcode[pil] pillow
    python generate_qr.py
"""

import json
import pathlib
import qrcode
from qrcode.image.styledpil import StyledPilImage
from qrcode.image.styles.moduledrawers import RoundedModuleDrawer

# ── Load AP credentials from config.json ─────────────────────────────────────
cfg_path = pathlib.Path(__file__).parent / 'config.json'
with open(cfg_path) as f:
    cfg = json.load(f)

ap_ssid = cfg['wifi'].get('ap_ssid', 'ToastTimer')
ap_pass = cfg['wifi'].get('ap_password', '')
auth    = 'WPA' if ap_pass else 'nopass'

# ── QR data strings ───────────────────────────────────────────────────────────
wifi_data = f'WIFI:T:{auth};S:{ap_ssid};P:{ap_pass};;' if ap_pass \
            else f'WIFI:T:nopass;S:{ap_ssid};;'
# url_data  = 'http://toasttimer.local/'
url_data  = 'http://192.168.4.1'

# ── Helper ────────────────────────────────────────────────────────────────────
def make_qr(data, filename, label):
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)

    img = qr.make_image(
        image_factory=StyledPilImage,
        module_drawer=RoundedModuleDrawer(),
    )

    # Add a text label below the QR code
    from PIL import Image, ImageDraw, ImageFont
    qr_img = img.convert('RGB')
    w, h   = qr_img.size

    # Try to use a system font; fall back to default
    try:
        font = ImageFont.truetype('arial.ttf', 18)
    except OSError:
        font = ImageFont.load_default()

    # Measure label
    tmp_draw = ImageDraw.Draw(qr_img)
    bbox     = tmp_draw.textbbox((0, 0), label, font=font)
    txt_w    = bbox[2] - bbox[0]
    pad      = 12
    new_h    = h + bbox[3] - bbox[1] + pad * 2

    canvas = Image.new('RGB', (w, new_h), 'white')
    canvas.paste(qr_img, (0, 0))
    draw = ImageDraw.Draw(canvas)
    draw.text(((w - txt_w) // 2, h + pad), label, fill='black', font=font)

    out = pathlib.Path(__file__).parent / filename
    canvas.save(out)
    print(f'  {out.name}  →  {data}')

# ── Generate ──────────────────────────────────────────────────────────────────
print('Generating QR codes…')
make_qr(wifi_data, 'qr_wifi.png',  f'WiFi: {ap_ssid}')
make_qr(url_data,  'qr_url.png',   url_data)
print('Done.')
