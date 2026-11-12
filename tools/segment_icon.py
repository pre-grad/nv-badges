"""Split an FR Neon Icon badge into icon, eyebrow, main word, separator, secondary rows."""
import numpy as np
from segment import runs, crop, A_TH

def segment_icon(path):
    from PIL import Image
    arr = np.asarray(Image.open(path).convert("RGBA"))
    H, W = arr.shape[:2]
    a = arr[..., 3] > A_TH
    spans = runs(a.sum(0), min_gap=int(H * 0.05))
    parts = {}
    # icon = first column span, roughly square and starting near the left edge
    s, e = spans[0]
    # an icon may split into several column spans (speaker + waves); take all that fit in a square
    while len(spans) > 1 and spans[1][1] - s <= H * 1.05:
        spans.pop(0); e = spans[0][1]
    if (e - s) < H * 1.15 and s < H * 0.4 and len(spans) > 1:
        parts["icon"] = crop(arr, (s, 0, e, H))[0]
        tx0 = e
    else:
        tx0 = 0
    # text block: look for a tall thin separator
    tspans = [sp for sp in spans if sp[0] >= tx0]
    sep = None
    for s2, e2 in tspans[1:]:
        ys = np.where(a[:, s2:e2].any(1))[0]
        if (e2 - s2) < H * 0.06 and ys.max() - ys.min() > H * 0.5:
            sep = (s2, e2); break
    left_x1 = sep[0] if sep else W
    rows = runs(a[:, tx0:left_x1].any(1).astype(int), min_gap=max(1, int(H * 0.012)))
    pieces = [crop(arr, (tx0, r0, left_x1, r1))[0] for r0, r1 in rows]
    if len(pieces) == 1:
        parts["main"] = pieces[0]
    else:
        mi = max(range(len(pieces)), key=lambda i: pieces[i].shape[0])
        parts["main"] = pieces[mi]
        above = pieces[:mi]; below = pieces[mi + 1:]
        if above: parts["eyebrow"] = above[-1]
        if below: parts["secondary"] = below
    if sep:
        parts["sep"] = crop(arr, (sep[0], 0, sep[1], H))[0]
        rrows = runs(a[:, sep[1]:].any(1).astype(int), min_gap=int(H * 0.03))
        parts["secondary"] = [crop(arr, (sep[1], r0, W, r1))[0] for r0, r1 in rrows]
    return parts
