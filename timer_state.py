"""
Timer state machine – pure logic, no hardware dependencies.
Uses time.ticks_ms() / ticks_diff() for monotonic elapsed time.
"""

import time

PRESETS = [
    {'label': '1 Minute',       'times': [0,   0,    60,  600]},
    {'label': 'Table Topics',   'times': [60,  90,  120,  150]},
    {'label': 'Evaluations',    'times': [120, 150, 180,  210]},
    {'label': 'Icebreaker',     'times': [240, 300, 360,  390]},
    {'label': '5\u20137 Minutes',    'times': [300, 360, 420,  450]},
    {'label': '10 Minutes',     'times': [480, 540, 600,  630]},
    {'label': '12 Minutes',     'times': [600, 660, 720,  750]},
    {'label': '15 Minutes',     'times': [780, 840, 900,  930]},
    {'label': '20 Minutes',     'times': [960,1080,1200, 1230]},
    {'label': 'Manual',         'times': [0,   0,    0,    0]},
]


class Timer:
    def __init__(self, config):
        self.thresholds   = [0, 0, 0, 0]
        self.colour       = 'off'
        self.running      = False
        self.flash_on     = False
        self.speaker      = ''
        self.brightness   = float(config['timer']['brightness'])

        self._elapsed_ms  = 0
        self._start_ticks = None
        self._manual_colour = None

    # ── controls ───────────────────────────────────────────────────────────

    def start(self):
        if not self.running:
            self._start_ticks = time.ticks_ms()
            self.running = True

    def stop(self):
        if self.running:
            self._elapsed_ms += time.ticks_diff(time.ticks_ms(), self._start_ticks)
            self._start_ticks = None
            self.running = False

    def reset(self):
        self.running       = False
        self._elapsed_ms   = 0
        self._start_ticks  = None
        self.colour        = 'off'
        self._manual_colour = None

    # ── properties ────────────────────────────────────────────────────────

    @property
    def elapsed(self):
        ms = self._elapsed_ms
        if self.running and self._start_ticks is not None:
            ms += time.ticks_diff(time.ticks_ms(), self._start_ticks)
        return ms / 1000.0

    # ── setters ───────────────────────────────────────────────────────────

    def set_colour(self, colour):
        self._manual_colour = colour
        self.colour = colour

    def set_thresholds(self, thresholds):
        self.thresholds = list(thresholds)
        self._manual_colour = None

    # ── state snapshot ────────────────────────────────────────────────────

    def _colour_for_elapsed(self):
        if self._manual_colour is not None:
            return self._manual_colour
        t = self.thresholds
        if not any(t):
            return self.colour   # manual/free mode – keep whatever it is
        s = int(self.elapsed)
        if t[3] and s >= t[3]: return 'flash'
        if t[2] and s >= t[2]: return 'red'
        if t[1] and s >= t[1]: return 'amber'
        if t[0] and s >= t[0]: return 'green'
        return 'off'

    def get_state(self):
        self.colour = self._colour_for_elapsed()
        return {
            'colour':     self.colour,
            'elapsed':    round(self.elapsed, 1),
            'running':    self.running,
            'thresholds': self.thresholds,
            'speaker':    self.speaker,
            'flash_on':   self.flash_on,
            'manual':     self._manual_colour is not None,
        }
