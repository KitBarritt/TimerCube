"""
16×16 LED matrix driver for Pimoroni Stellar Unicorn (Pico W / Pico 2 W).
Uses PicoGraphics + StellarUnicorn API (Pimoroni MicroPython firmware required).

Layout: (0,0) = top-left, x increases right, y increases down.

ROTATION — set to the clockwise angle the board is physically rotated inside
           its case (0, 90, 180, or 270).  Content is counter-rotated so it
           appears upright regardless of board orientation.

Colours are specified as (R, G, B) — PicoGraphics handles the WS2812B byte
order internally; no manual GRB swapping needed.
"""

from stellar import StellarUnicorn
from picographics import PicoGraphics, DISPLAY_STELLAR_UNICORN

MATRIX_SIZE = 16
ROTATION    = 0     # 0 / 90 / 180 / 270 degrees clockwise

# ── colours as (R, G, B) ────────────────────────────────────────────────────
BLACK     = (0,   0,   0)
WHITE     = (200, 200, 200)
DIM_WHITE = (60,  60,  60)
GREEN     = (0,   200, 0)
AMBER     = (255, 140, 0)
RED       = (220, 0,   0)
BLUE      = (0,   0,   200)

# ── 5×7 pixel font (5-bit rows, bit 4 = leftmost col) ───────────────────────
#
#  Decoding: for col in range(5), pixel_on = bool(bits & (1 << (4 - col)))
#  e.g. 0x0E = 0b01110 → cols 1, 2, 3 lit
#       0x11 = 0b10001 → cols 0 and 4 lit
#
_FONT = {
    '0': [0x0E, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E],
    '1': [0x04, 0x0C, 0x04, 0x04, 0x04, 0x04, 0x0E],
    '2': [0x0E, 0x11, 0x01, 0x02, 0x04, 0x08, 0x1F],
    '3': [0x0E, 0x01, 0x01, 0x0E, 0x01, 0x01, 0x0E],
    '4': [0x11, 0x11, 0x11, 0x1F, 0x01, 0x01, 0x01],
    '5': [0x1F, 0x10, 0x10, 0x1E, 0x01, 0x11, 0x0E],
    '6': [0x0E, 0x10, 0x10, 0x1E, 0x11, 0x11, 0x0E],
    '7': [0x1F, 0x01, 0x02, 0x04, 0x08, 0x08, 0x08],
    '8': [0x0E, 0x11, 0x11, 0x0E, 0x11, 0x11, 0x0E],
    '9': [0x0E, 0x11, 0x11, 0x0F, 0x01, 0x11, 0x0E],
    'A': [0x04, 0x0A, 0x11, 0x1F, 0x11, 0x11, 0x11],
    'B': [0x1E, 0x11, 0x11, 0x1E, 0x11, 0x11, 0x1E],
    'C': [0x0E, 0x11, 0x10, 0x10, 0x10, 0x11, 0x0E],
    'E': [0x1F, 0x10, 0x10, 0x1E, 0x10, 0x10, 0x1F],
    'I': [0x0E, 0x04, 0x04, 0x04, 0x04, 0x04, 0x0E],
    'P': [0x1E, 0x11, 0x11, 0x1E, 0x10, 0x10, 0x10],
    'G': [0x0E, 0x10, 0x10, 0x13, 0x11, 0x11, 0x0E],
    'R': [0x1E, 0x11, 0x11, 0x1E, 0x14, 0x12, 0x11],
    'S': [0x0E, 0x11, 0x10, 0x0E, 0x01, 0x11, 0x0E],
    'U': [0x11, 0x11, 0x11, 0x11, 0x11, 0x11, 0x0E],
    '-': [0x00, 0x00, 0x00, 0x1F, 0x00, 0x00, 0x00],
    ':': [0x00, 0x04, 0x04, 0x00, 0x04, 0x04, 0x00],
    '?': [0x0E, 0x11, 0x01, 0x06, 0x04, 0x00, 0x04],
}

_GLYPH_W = 5
_GLYPH_H = 7

# ── 16×16 custom bitmaps for large-letter mode ───────────────────────────────
#
#  Each entry is a list of 16 integers, one per row (top→bottom).
#  Each integer is 16 bits wide: bit 15 = col 0 (left), bit 0 = col 15 (right).
#  i.e. col x is lit when  row_value & (1 << (15 - x))  is non-zero.
#
_LARGE_FONT = {
    'G': [
        0x0000,  # row  0  ................
        0x07E0,  # row  1  .....######.....
        0x0FE0,  # row  2  ....#######.....
        0x1C00,  # row  3  ...###..........
        0x1800,  # row  4  ...##...........
        0x1870,  # row  5  ...##....###....
        0x1878,  # row  6  ...##....####...
        0x1818,  # row  7  ...##......##...
        0x1818,  # row  8  ...##......##...
        0x1818,  # row  9  ...##......##...
        0x1818,  # row 10  ...##......##...
        0x1818,  # row 11  ...##......##...
        0x1C38,  # row 12  ...###....###...
        0x0FF0,  # row 13  ....########....
        0x07E0,  # row 14  .....######.....
        0x0000,  # row 15  ................
    ],
    'A': [
        0x0000,  # row  0  ................
        0x0180,  # row  1  .......##.......
        0x03C0,  # row  2  ......####......
        0x0660,  # row  3  .....##..##.....
        0x0C30,  # row  4  ....##....##....
        0x1818,  # row  5  ...##......##...
        0x1818,  # row  6  ...##......##...
        0x1FF8,  # row  7  ...##########...
        0x1FF8,  # row  8  ...##########...
        0x1818,  # row  9  ...##......##...
        0x1818,  # row 10  ...##......##...
        0x1818,  # row 11  ...##......##...
        0x1818,  # row 12  ...##......##...
        0x1818,  # row 13  ...##......##...
        0x1818,  # row 14  ...##......##...
        0x0000,  # row 15  ................
    ],
    'R': [
        0x0000,  # row  0  ................
        0x1F80,  # row  1  ...######.......
        0x1FC0,  # row  2  ...#######......
        0x18C0,  # row  3  ...##...##......
        0x18C0,  # row  4  ...##...##......
        0x18C0,  # row  5  ...##...##......
        0x1F80,  # row  6  ...######.......
        0x1F00,  # row  7  ...#####........
        0x1B00,  # row  8  ...##.##........
        0x1980,  # row  9  ...##..##.......
        0x18C0,  # row 10  ...##...##......
        0x1860,  # row 11  ...##....##.....
        0x1830,  # row 12  ...##.....##....
        0x1830,  # row 13  ...##.....##....
        0x1830,  # row 14  ...##.....##....
        0x0000,  # row 15  ................
    ],
}

# Vertical centre offset so a 7-row glyph sits in the middle of 16 rows.
# (16 - 7) // 2 = 4  →  4 px top margin, 5 px bottom margin.
_GLYPH_Y = (MATRIX_SIZE - _GLYPH_H) // 2   # = 4


class Matrix:
    def __init__(self):
        self._su = StellarUnicorn()
        self._g  = PicoGraphics(display=DISPLAY_STELLAR_UNICORN)
        self._brightness = 0.6
        self._su.set_brightness(self._brightness)
        self._extra_rot = None   # per-call rotation override for show_char

    # ── brightness ─────────────────────────────────────────────────────────

    @property
    def brightness(self):
        return self._brightness

    @brightness.setter
    def brightness(self, value):
        self._brightness = max(0.0, min(1.0, float(value)))
        self._su.set_brightness(self._brightness)

    def set_brightness(self, value):
        self.brightness = value

    # ── button access (used by main.py for boot-mode selection) ────────────

    @property
    def unicorn(self):
        """Expose the underlying StellarUnicorn instance for button reads."""
        return self._su

    # ── coordinate helpers ─────────────────────────────────────────────────

    def _rotate(self, x, y):
        """
        Counter-rotate (x, y) to compensate for physical board rotation.
        Uses _extra_rot if set (per-call override), else the module ROTATION constant.
        """
        S = MATRIX_SIZE - 1
        r = self._extra_rot if self._extra_rot is not None else ROTATION
        if r == 90:   return S - y, x
        if r == 180:  return S - x, S - y
        if r == 270:  return y, S - x
        return x, y

    def _px(self, x, y, r, g, b):
        """Set one logical pixel, applying rotation, skipping out-of-bounds."""
        rx, ry = self._rotate(x, y)
        if 0 <= rx < MATRIX_SIZE and 0 <= ry < MATRIX_SIZE:
            self._g.set_pen(self._g.create_pen(r, g, b))
            self._g.pixel(rx, ry)

    # ── public API ─────────────────────────────────────────────────────────

    def clear(self):
        self._g.set_pen(self._g.create_pen(0, 0, 0))
        self._g.clear()
        self._su.update(self._g)

    def fill(self, colour):
        self._g.set_pen(self._g.create_pen(*colour))
        self._g.clear()
        self._su.update(self._g)

    def dot(self, colour):
        """Single centre pixel – subtle running indicator."""
        self._g.set_pen(self._g.create_pen(0, 0, 0))
        self._g.clear()
        self._px(7, 7, *colour)
        self._su.update(self._g)

    def _draw_char(self, char, colour, x_offset, y_offset):
        """Render a 5×7 glyph at (x_offset, y_offset) without calling update."""
        glyph = _FONT.get(char, _FONT['?'])
        cr, cg, cb = colour
        for row, bits in enumerate(glyph):
            y = y_offset + row
            for col in range(_GLYPH_W):
                x = x_offset + col
                if bits & (1 << (_GLYPH_W - 1 - col)):
                    self._px(x, y, cr, cg, cb)
                else:
                    self._px(x, y, 0, 0, 0)

    def show_char(self, char, colour, rotation=None):
        """Show a single character centred on the 16×16 grid.

        Horizontal centre: (16 - 5) // 2 = 5  → cols 5–9.
        Vertical centre:   (16 - 7) // 2 = 4  → rows 4–10.

        rotation overrides the global ROTATION for this call only — use when
        a mode-indicator glyph must be pre-rotated so it reads correctly from
        the viewer's angle (e.g. while a button is held at boot for USB/BLE
        mode selection). Swap 90⇄270 if the glyph appears upside-down on
        hardware.
        """
        self._extra_rot = rotation
        self._g.set_pen(self._g.create_pen(0, 0, 0))
        self._g.clear()
        self._draw_char(char, colour, x_offset=5, y_offset=_GLYPH_Y)
        self._su.update(self._g)
        self._extra_rot = None

    def show_large_char(self, char, colour):
        """Show a single character large on the 16×16 grid.

        If *char* has an entry in _LARGE_FONT, the custom 16×16 bitmap is used
        directly (each row is a 16-bit integer, bit 15 = col 0).
        Otherwise falls back to the 5×7 _FONT rendered at 2× scale (10×14 px,
        centred with 3 px left margin and 1 px top margin).
        """
        self._g.set_pen(self._g.create_pen(0, 0, 0))
        self._g.clear()
        cr, cg, cb = colour

        if char in _LARGE_FONT:
            bitmap = _LARGE_FONT[char]
            for y, bits in enumerate(bitmap):
                for x in range(MATRIX_SIZE):
                    if bits & (1 << (MATRIX_SIZE - 1 - x)):
                        self._px(x, y, cr, cg, cb)
        else:
            # 2× scaled fallback
            glyph = _FONT.get(char, _FONT['?'])
            x_off = (MATRIX_SIZE - _GLYPH_W * 2) // 2   # = 3
            y_off = (MATRIX_SIZE - _GLYPH_H * 2) // 2   # = 1
            for row, bits in enumerate(glyph):
                for col in range(_GLYPH_W):
                    if bits & (1 << (_GLYPH_W - 1 - col)):
                        for dy in range(2):
                            for dx in range(2):
                                self._px(x_off + col * 2 + dx, y_off + row * 2 + dy, cr, cg, cb)

        self._su.update(self._g)

    def show_two_chars(self, c1, c2, colour1, colour2):
        """Show two 5×7 characters side by side on the 16×16 grid.

        Layout (16 wide):  2 px pad | char1 (5) | 2 px gap | char2 (5) | 2 px pad
          char1 x_offset = 2  → cols 2–6
          char2 x_offset = 9  → cols 9–13
        Both glyphs share the same vertical centre (_GLYPH_Y = 4).
        """
        self._g.set_pen(self._g.create_pen(0, 0, 0))
        self._g.clear()
        self._draw_char(c1, colour1, x_offset=2, y_offset=_GLYPH_Y)
        self._draw_char(c2, colour2, x_offset=9, y_offset=_GLYPH_Y)
        self._su.update(self._g)

    def show_string(self, s, colour):
        """Show a 1–3 character string centred on the 16×16 grid.

        1 char  → delegates to show_char (centred at col 5).
        2 chars → delegates to show_two_chars (cols 2 and 9).
        3 chars → tight-packed: 3×5 = 15 px, x offsets 0, 5, 10.
        """
        n = len(s)
        if n == 1:
            self.show_char(s[0], colour)
            return
        if n == 2:
            self.show_two_chars(s[0], s[1], colour, colour)
            return
        # 3 chars: (16 - 3×5) // 2 = 0 → x offsets 0, 5, 10
        x_off = (MATRIX_SIZE - _GLYPH_W * n) // 2
        self._g.set_pen(self._g.create_pen(0, 0, 0))
        self._g.clear()
        for i, ch in enumerate(s):
            self._draw_char(ch, colour, x_offset=x_off + i * _GLYPH_W, y_offset=_GLYPH_Y)
        self._su.update(self._g)
