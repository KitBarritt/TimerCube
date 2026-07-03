"""
DDNS registration for TimerCube.

On WiFi connect, calls:
  https://timercubeip.kitbarritt.org/register?id=<device_id>&ip=<ip>

CloudFlare processes this to keep the per-device subdomain pointing at the
device's current LAN IP, so cubeusb.kitbarritt.org/<id> always resolves.
"""

def register(device_id, ip):
    try:
        import urequests
        url = 'https://timercubeip.kitbarritt.org/register?id=%s&ip=%s' % (device_id, ip)
        r = urequests.get(url, timeout=10)
        ok = r.status_code == 200
        r.close()
        print('DDNS: id=%s ip=%s status=%s' % (device_id, ip, r.status_code))
        return ok
    except Exception as e:
        print('DDNS: register failed:', e)
        return False
