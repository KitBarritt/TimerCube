import urequests

_REGISTRY = 'http://timercubeip.kitbarritt.org'

def register(ip):
    try:
        from id import UNIT_ID
    except ImportError:
        return
    try:
        r = urequests.get(f'{_REGISTRY}/register?id={UNIT_ID}&ip={ip}', timeout=5)
        print('Registering device:%s' % UNIT_ID)
        print(' to ddns: client ip=%s' % ip)
        r.close()
    except Exception:
        pass