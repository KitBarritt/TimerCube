import json

CONFIG_FILE = '/config.json'

_DEFAULTS = {
    'wifi': {
        'networks': [],
        'ap_ssid': 'TimerCube',
        'ap_password': 'toastmaster',
    },
    'timer': {
        'brightness': 0.6,
    },
    'language': 'en',
}


def _merge(target, defaults):
    for key, val in defaults.items():
        if key not in target:
            target[key] = val
        elif isinstance(val, dict) and isinstance(target.get(key), dict):
            _merge(target[key], val)


def load_config():
    try:
        with open(CONFIG_FILE) as f:
            data = json.load(f)
        _merge(data, _DEFAULTS)
        return data
    except Exception:
        import json as _j
        return _j.loads(_j.dumps(_DEFAULTS))  # deep copy of defaults


def save_config(config):
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)
