"""Split an FR Neon badge into its parts: eyebrow, main word, separator, secondary rows."""
import numpy as np
from PIL import Image

A_TH = 40

def runs(profile, min_gap):
    """Return [start, end) spans where profile>0, merging gaps shorter than min_gap."""
    on = np.where(profile > 0)[0]
    if len(on) == 0:
        return []
    spans, s, prev = [], on[0], on[0]
    for x in on[1:]:
        if x - prev > min_gap:
            spans.append((s, prev + 1)); s = x
        prev = x
    spans.append((s, prev + 1))
    return spans

def crop(arr, box):
    x0, y0, x1, y1 = box
    sub = arr[y0:y1, x0:x1]
    a = sub[..., 3] > A_TH
    ys, xs = np.where(a)
    if len(xs) == 0:
        return None, None
    bb = (x0 + xs.min(), y0 + ys.min(), x0 + xs.max() + 1, y0 + ys.max() + 1)
    return arr[bb[1]:bb[3], bb[0]:bb[2]], bb

def segment(path):
    arr = np.asarray(Image.open(path).convert("RGBA"))
    H, W = arr.shape[:2]
    a = arr[..., 3] > A_TH
    col = a.sum(0)
    # column spans separated by real gaps (word spacing inside a label is smaller)
    spans = runs(col, min_gap=int(H * 0.06))
    sep = None
    for s, e in spans:
        w = e - s
        ys = np.where(a[:, s:e].any(1))[0]
        tall = ys.max() - ys.min()
        if w < H * 0.06 and tall > H * 0.55 and s > W * 0.1:
            sep = (s, e); break
    parts = {}
    if sep:
        left = (0, 0, sep[0], H); right = (sep[1], 0, W, H)
        parts["sep"] = crop(arr, (sep[0], 0, sep[1], H))
    else:
        left = (0, 0, W, H); right = None
    # left: eyebrow above main?
    lx0, _, lx1, _ = left
    rows = runs(a[:, lx0:lx1].any(1).astype(int), min_gap=int(H * 0.03))
    if len(rows) >= 2:
        parts["eyebrow"] = crop(arr, (lx0, rows[0][0], lx1, rows[0][1]))
        parts["main"] = crop(arr, (lx0, rows[1][0], lx1, rows[-1][1]))
    else:
        parts["main"] = crop(arr, left)
    if right:
        rx0, _, rx1, _ = right
        rrows = runs(a[:, rx0:rx1].any(1).astype(int), min_gap=int(H * 0.03))
        parts["secondary"] = [crop(arr, (rx0, r0, rx1, r1)) for r0, r1 in rrows]
    return arr, parts
