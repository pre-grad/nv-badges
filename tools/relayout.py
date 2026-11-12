"""Re-lay FR Neon badges onto one line, keeping the original artwork.

Each original is cut into eyebrow / main word / separator / secondary rows
(see segment.py), then reassembled left to right so the main word fills the
tag height. Glyphs, gradients and sheen are the original pixels.
"""
import numpy as np
from PIL import Image

from segment import segment

H, PAD, CAP = 160, 8, 124
DESC = H - 2 * PAD - CAP          # room under the baseline for p, g, y
STD_CAP = 146                      # cap height of standard-size Neon originals
SEC_BOOST = 1.25                   # secondary labels larger than original so they read on TV
EYEBROW_BOOST = 1.30
GAP = round(CAP * 0.30)
SIDE = 6


def _img(piece):
    return Image.fromarray(np.ascontiguousarray(piece))


def _scaled(piece, s):
    im = _img(piece)
    return im.resize((max(1, round(im.width * s)), max(1, round(im.height * s))), Image.LANCZOS)


def separator_like(piece):
    """A separator bar coloured from another piece's vertical colour profile."""
    a = piece[..., 3] > 40
    rows = [piece[y, a[y], :3].mean(0) if a[y].any() else None for y in range(piece.shape[0])]
    rows = [r for r in rows if r is not None]
    h, w = 200, 9
    bar = np.zeros((h, w, 4), np.uint8)
    for y in range(h):
        c = rows[int(y / h * (len(rows) - 1))]
        bar[y, :, :3] = c
        bar[y, :, 3] = 255
    # round the ends
    for y in range(4):
        cut = 4 - y
        bar[y, :cut, 3] = bar[y, w - cut:, 3] = 0
        bar[h - 1 - y, :cut, 3] = bar[h - 1 - y, w - cut:, 3] = 0
    return bar


def compose(parts):
    main = parts["main"]
    mh = main.shape[0]
    cap_orig = mh if mh <= 150 else STD_CAP
    s_main = min(CAP / cap_orig, (CAP + DESC) / mh)
    base = CAP / STD_CAP
    cap_mid = PAD + CAP / 2

    items = []                                   # (image, y, gap after)
    if parts.get("eyebrow") is not None:
        eb = _scaled(parts["eyebrow"], base * EYEBROW_BOOST)
        items.append((eb, round(cap_mid - eb.height / 2), round(CAP * 0.14)))
    items.append((_scaled(main, s_main), PAD, GAP))
    if parts.get("sep") is not None:
        sep = parts["sep"]
        sep_img = _img(sep).resize((max(3, round(sep.shape[1] * base)), H - 2 * PAD), Image.LANCZOS)
        items.append((sep_img, PAD, GAP))
        secs = parts["secondary"]
        for i, piece in enumerate(secs):
            s = parts.get("secondary_scale", base * SEC_BOOST)
            sc = _scaled(piece, s)
            items.append((sc, round(cap_mid - sc.height / 2), GAP if i < len(secs) - 1 else 0))

    W = SIDE * 2 + sum(im.width for im, _, _ in items) + sum(g for _, _, g in items[:-1])
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x = SIDE
    for i, (im, y, g) in enumerate(items):
        out.alpha_composite(im, (x, max(0, min(H - im.height, y))))
        x += im.width + (g if i < len(items) - 1 else 0)
    return out


def parts_of(path):
    _, p = segment(path)
    return {
        "eyebrow": p["eyebrow"][0] if "eyebrow" in p else None,
        "main": p["main"][0],
        "sep": p["sep"][0] if "sep" in p else None,
        "secondary": [piece for piece, _ in p.get("secondary", [])],
    }


def relayout(path):
    return compose(parts_of(path))


def combo(left_path, right_path):
    """Left badge as-is, then a separator and the right badge's main word as the secondary."""
    left, right = parts_of(left_path), parts_of(right_path)
    left["sep"] = separator_like(right["main"])
    left["secondary"] = [right["main"]]
    # right main is full cap size; bring it down to secondary size
    left["secondary_scale"] = (CAP / STD_CAP) * SEC_BOOST * 0.56
    return compose(left)
