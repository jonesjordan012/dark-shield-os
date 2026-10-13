#!/usr/bin/env python3
# Dark Shield OS
# Copyright (C) 2026 Jordan Jones
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

"""
DARK SHIELD 0.1 - first light, LESSON TWO (answer key)
======================================================
This is the solved version of lesson two. Try the change yourself first --
the lesson is in the typing, not the reading. If you get stuck, compare
your collect_stars with this one.

Lesson two: RECURSION. The sky used to be flat -- it only saw files in ONE
folder. Now it dives into subfolders too, up to max_depth deep.
A function calling itself to solve a smaller version of the same problem.
"""

import hashlib   # gives every filename a stable "address" in the sky
import math      # lets star brightness grow gently with file size
import os        # lets us walk directories and read /proc
import sys       # lets us read the directory you typed on the command line

# ---------------------------------------------------------------------------
# 1. The sky: a fixed grid of characters. WIDTH x HEIGHT "parsecs".
# ---------------------------------------------------------------------------
WIDTH, HEIGHT = 72, 18

# Stars burn brighter as files get bigger. Five magnitudes, dim -> bright.
# (If your terminal can't show these, we fall back to plain ASCII below.)
STAR_GLYPHS = "·*✦✶✹"
PULSAR_GLYPH = "◉"

# Every decorative character lives in one place, so the ASCII fallback
# can swap the whole sky at once.
DOT, SPARK = "·", "✦"
HLINE, VLINE, TL, TR, BL, BR = "─", "│", "┌", "┐", "└", "┘"
TIMES = "×"

# Colors, used only when the terminal supports them.
USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None
BLUE = "\033[94m" if USE_COLOR else ""
YELLOW = "\033[93m" if USE_COLOR else ""
DIM = "\033[2m" if USE_COLOR else ""
RESET = "\033[0m" if USE_COLOR else ""


# ---------------------------------------------------------------------------
# 2. Functions: small named machines. Each one does exactly one thing.
# ---------------------------------------------------------------------------
def sky_address(name):
    """Turn a filename into a stable (x, y) position in the sky.

    The same name always lands on the same star - your universe does
    not rearrange itself between runs. This is a hash, Dark Shield's
    future 'star://' identity scheme in miniature."""
    digest = hashlib.sha256(name.encode("utf-8", "replace")).digest()
    x = int.from_bytes(digest[0:2], "big") % WIDTH
    y = int.from_bytes(digest[2:4], "big") % HEIGHT
    return x, y


def magnitude(size_bytes):
    """A file 10x bigger burns one step brighter. Log scale, like real stars."""
    if size_bytes <= 0:
        return 0
    return min(len(STAR_GLYPHS) - 1, int(math.log10(size_bytes + 1)))


def collect_stars(root, max_depth=2):
    """Walk a directory AND its subfolders (up to max_depth deep) and
    return a list of (name, size) for every file found.

    Lesson two: recursion. walk() calls itself for each subfolder, going
    one level deeper each time, until it reaches the depth limit. Symlinks
    are skipped so the dive can never loop forever."""
    stars = []

    def walk(path, depth):
        if depth > max_depth:
            return
        try:
            entries = sorted(os.listdir(path))
        except OSError:
            return
        for name in entries:
            full = os.path.join(path, name)
            try:
                if os.path.isfile(full) and not os.path.islink(full):
                    # The star's name is its path relative to the root,
                    # so the same file always gets the same sky address.
                    stars.append((os.path.relpath(full, root), os.path.getsize(full)))
                elif os.path.isdir(full) and not os.path.islink(full):
                    walk(full, depth + 1)
            except OSError:
                continue  # a star we cannot weigh still counts as dark matter

    walk(root, 0)
    return stars


def collect_pulsars(limit=8):
    """Read /proc - Linux's window into living processes - and return the
    most numerous process names. Each one is a pulsar: active computation."""
    counts = {}
    try:
        pids = [p for p in os.listdir("/proc") if p.isdigit()]
    except OSError:
        return []
    for pid in pids:
        try:
            with open(f"/proc/{pid}/comm", encoding="utf-8") as f:
                name = f.read().strip()
            counts[name] = counts.get(name, 0) + 1
        except OSError:
            continue  # processes are born and die constantly; skip the ghosts
    return sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:limit]


def render(root):
    """Build the sky and print it."""
    stars = collect_stars(root)[:250]  # even the sky has a fire code
    pulsars = collect_pulsars()

    # An empty grid of spaces; we will hang stars on it.
    grid = [[" " for _ in range(WIDTH)] for _ in range(HEIGHT)]
    occupied = set()

    for name, size in stars:
        x, y = sky_address(name)
        # Collisions: two stars, one address. Nudge downward until free.
        while (x, y) in occupied:
            y = (y + 1) % HEIGHT
        occupied.add((x, y))
        grid[y][x] = BLUE + STAR_GLYPHS[magnitude(size)] + RESET

    # Pulsars get the front row of the sky, left to right.
    for i, (pname, count) in enumerate(pulsars):
        x, y = i * 3 % WIDTH, 0
        if (x, y) not in occupied:
            grid[y][x] = YELLOW + PULSAR_GLYPH + RESET

    total_bytes = sum(size for _, size in stars)
    bar = TL + HLINE * WIDTH + TR
    print(DIM + "DARK SHIELD 0.1 " + DOT + " first light " + DOT + " " + root + RESET)
    print(DIM + bar + RESET)
    for row in grid:
        print(DIM + VLINE + RESET + "".join(row) + DIM + VLINE + RESET)
    print(DIM + BL + HLINE * WIDTH + BR + RESET)
    print(f"{DIM}{SPARK} {len(stars)} stars {DOT} {total_bytes:,} bytes of matter"
          f" {DOT} {PULSAR_GLYPH} {len(pulsars)} pulsars burning{RESET}")
    if pulsars:
        loud = ", ".join(f"{n}{TIMES}{c}" for n, c in pulsars[:5])
        print(f"{DIM}  loudest pulsars: {loud}{RESET}")


# ---------------------------------------------------------------------------
# 3. The ignition: this runs only when you execute the file directly.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "."
    if not os.path.isdir(target):
        print(f"no such directory: {target}")
        sys.exit(1)
    # Module scope: plain assignment rebinds the globals above.
    try:
        "".join(STAR_GLYPHS).encode(sys.stdout.encoding or "utf-8")
    except (UnicodeEncodeError, LookupError):
        STAR_GLYPHS = ".,*oO"  # ASCII sky for older terminals
        PULSAR_GLYPH = "@"
        DOT, SPARK = ".", "*"
        HLINE, VLINE, TL, TR, BL, BR = "-", "|", "+", "+", "+", "+"
        TIMES = "x"
    render(os.path.abspath(target))
