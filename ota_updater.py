"""
OTA update helpers – all functions are synchronous (urequests is blocking).
The async orchestration lives in web_server.py so the event loop can yield
progress updates between each file download.
"""

import os
import json


def _raw_url(repo, branch, path):
    return "https://raw.githubusercontent.com/" + repo + "/" + branch + "/" + path


def _version_tuple(v):
    try:
        return tuple(int(x) for x in v.split('.'))
    except Exception:
        return (0,)


def _parse_version(text):
    for line in text.split('\n'):
        line = line.strip()
        if line.startswith('VERSION') and '=' in line:
            val = line.split('=', 1)[1].strip().strip('"\'')
            return val
    return None


def fetch_remote_version(repo, branch):
    """Fetch version.py from GitHub and return the VERSION string."""
    import urequests
    url = _raw_url(repo, branch, "version.py")
    resp = urequests.get(url)
    if resp.status_code != 200:
        code = resp.status_code
        resp.close()
        raise RuntimeError("version.py not found in repo (HTTP " + str(code) + ")")
    text = resp.text
    resp.close()
    v = _parse_version(text)
    if v is None:
        raise RuntimeError("Cannot parse VERSION in remote version.py")
    return v


def is_update_available(repo, branch):
    """Return (remote_version, is_newer)."""
    from version import VERSION
    remote = fetch_remote_version(repo, branch)
    newer = _version_tuple(remote) > _version_tuple(VERSION)
    return remote, newer


def fetch_manifest(repo, branch):
    """Return list of repo-relative file paths to update."""
    import urequests
    url = _raw_url(repo, branch, "manifest.json")
    resp = urequests.get(url)
    data = json.loads(resp.text)
    resp.close()
    return data['files']


def download_file(repo, branch, rel_path):
    """
    Download one file to <device_path>.new.
    Returns the device path (without .new) on success.
    Raises on any error so the caller can abort cleanly.
    """
    import urequests
    dev_path = '/' + rel_path

    # Ensure parent directory exists
    if '/' in rel_path:
        parent = dev_path.rsplit('/', 1)[0]
        try:
            os.mkdir(parent)
        except OSError:
            pass

    url = _raw_url(repo, branch, rel_path)
    resp = urequests.get(url)
    if resp.status_code != 200:
        resp.close()
        raise RuntimeError("HTTP " + str(resp.status_code) + " for " + rel_path)

    data = resp.content
    resp.close()

    with open(dev_path + '.new', 'wb') as f:
        f.write(data)

    return dev_path


def install_files(dev_paths):
    """
    Atomic rename phase (fast – no network):
      1. Rename existing <path> → <path>.bak
      2. Rename <path>.new  → <path>
    Returns list of (dev_path, bak_path) for cleanup.
    """
    backed_up = []
    for dev_path in dev_paths:
        bak = dev_path + '.bak'
        try:
            os.rename(dev_path, bak)
            backed_up.append((dev_path, bak))
        except OSError:
            pass  # file didn't exist yet – fine
        os.rename(dev_path + '.new', dev_path)
    return backed_up


def cleanup_backups(backed_up):
    """Delete all .bak files left from a completed install."""
    for _, bak in backed_up:
        try:
            os.remove(bak)
        except OSError:
            pass


def abort_download(downloaded):
    """Remove .new files when a download run fails part-way through."""
    for dev_path in downloaded:
        try:
            os.remove(dev_path + '.new')
        except OSError:
            pass
