#!/usr/bin/env python3
"""Compares a "before" and an "after" screenshot of the same screen.

Usage: screen-diff.py <before.png> <after.png> <diff.png>
Prints JSON: whether the sizes match, how many pixels changed (a channel moved by more than 24,
which ignores anti-aliasing noise), the percent, and the box around the changes. Writes diff.png:
the after image, faded, with changed pixels in red. A screen that the ticket did not mean to
change must show 0 changed pixels.
"""
import json, sys
from PIL import Image, ImageChops

before, after, out = sys.argv[1:4]
a = Image.open(before).convert("RGB")
b = Image.open(after).convert("RGB")
if a.size != b.size:
    print(json.dumps({"same_size": False, "before": a.size, "after": b.size}))
    sys.exit(0)
diff = ImageChops.difference(a, b).convert("L").point(lambda v: 255 if v > 24 else 0)
changed = sum(1 for v in diff.getdata() if v)
total = a.size[0] * a.size[1]
faded = Image.blend(b, Image.new("RGB", b.size, "white"), 0.7)
faded.paste(Image.new("RGB", b.size, (230, 0, 0)), mask=diff)
faded.save(out)
print(json.dumps({"same_size": True, "changed_pixels": changed,
                  "changed_percent": round(100 * changed / total, 3), "box": diff.getbbox()}))
