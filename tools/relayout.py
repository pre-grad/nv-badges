"""Re-lay FR Neon badges onto one line, keeping the original artwork.

Each original is cut into eyebrow / main word / separator / secondary rows
(see segment.py), then reassembled left to right so the main word fills the
tag height. Glyphs, gradients and sheen are the original pixels.
"""
import numpy as np
from PIL import Image

from segment import segment
from segment_icon import segment_icon
from PIL import ImageFilter

H, PAD, CAP = 160, 4, 134
DESC = H - 2 * PAD - CAP          # room under the baseline for p, g, y
STD_CAP = 146                      # cap height of standard-size Neon originals
SEC_BOOST = 1.35                   # secondary labels larger than original so they read on TV
EYEBROW_BOOST = 1.30
GAP = round(CAP * 0.30)
SIDE = 6


def _img(piece):
    return Image.fromarray(np.ascontiguousarray(piece))


def _resize(im, size):
    """Resize RGBA without dark fringes: premultiply, resize, unpremultiply."""
    a = np.asarray(im.convert("RGBA")).astype(np.float32)
    al = a[..., 3:4] / 255.0
    pm = Image.fromarray(np.concatenate([a[..., :3] * al, a[..., 3:4]], -1).clip(0, 255).astype(np.uint8))
    r = np.asarray(pm.resize(size, Image.LANCZOS)).astype(np.float32)
    al = r[..., 3:4]
    rgb = np.where(al > 0, r[..., :3] / np.maximum(al, 1) * 255.0, 0)
    return Image.fromarray(np.concatenate([rgb, al], -1).clip(0, 255).astype(np.uint8))


def _scaled(piece, s):
    im = _img(piece)
    return _resize(im, (max(1, round(im.width * s)), max(1, round(im.height * s))))


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
    if parts.get("icon") is not None:
        ic = parts["icon"]
        ih = H - 2 * PAD
        icon = _img(ic).resize((max(1, round(ic.shape[1] * ih / ic.shape[0])), ih), Image.LANCZOS)
        items.append((icon, PAD, round(CAP * 0.26)))
    if parts.get("eyebrow") is not None:
        eb = _scaled(parts["eyebrow"], base * EYEBROW_BOOST)
        items.append((eb, round(cap_mid - eb.height / 2), round(CAP * 0.14)))
    items.append((_scaled(main, s_main), PAD, GAP))
    if parts.get("sep") is None and parts.get("secondary"):
        parts["sep"] = separator_like(parts["secondary"][0])   # stacked label -> inline with a bar
    if parts.get("sep") is not None:
        sep = parts["sep"]
        sep_img = _resize(_img(sep), (max(3, round(sep.shape[1] * base)), H - 2 * PAD))
        items.append((sep_img, PAD, GAP))
        secs = parts["secondary"]
        for i, piece in enumerate(secs):
            s = parts.get("secondary_scale", base * SEC_BOOST)
            sc = _scaled(piece, s)
            items.append((sc, round(cap_mid - sc.height / 2), GAP if i < len(secs) - 1 else 0))

    W = SIDE * 2 + sum(im.width for im, _, _ in items) + sum(g for _, _, g in items[:-1])
    text = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    x = SIDE
    for i, (im, y, g) in enumerate(items):
        text.alpha_composite(im, (x, max(0, min(H - im.height, y))))
        x += im.width + (g if i < len(items) - 1 else 0)
    return backdrop(text)


# --- legibility over poster art -------------------------------------------
STYLE = "halo"            # "halo": dark glow + thin outline behind text; "pill": translucent dark pill
HALO_ALPHA = 0.85
HALO_BLUR = 5
OUTLINE_PX = 2
PILL_ALPHA = 0.62
PILL_PAD = 14


def backdrop(text):
    from PIL import ImageDraw, ImageFilter
    W, H = text.size
    alpha = text.getchannel("A")
    if STYLE == "pill":
        pw, ph = W + 2 * PILL_PAD, H + 2 * PILL_PAD
        out = Image.new("RGBA", (pw, ph), (0, 0, 0, 0))
        pill = Image.new("L", (pw, ph), 0)
        ImageDraw.ImageDraw(pill).rounded_rectangle((0, 0, pw - 1, ph - 1), radius=ph // 2 - 2, fill=int(255 * PILL_ALPHA))
        out.putalpha(pill)
        out = Image.alpha_composite(out, Image.alpha_composite(Image.new("RGBA", (pw, ph), (0, 0, 0, 0)),
                                        _pad(text, PILL_PAD)))
        return out
    # halo: hard outline (dilate) + soft shadow, both near-black
    outline = alpha.filter(ImageFilter.MaxFilter(2 * OUTLINE_PX + 1))
    soft = alpha.filter(ImageFilter.GaussianBlur(HALO_BLUR)).point(lambda a: min(255, int(a * 1.6)))
    halo_a = Image.fromarray(np.maximum(np.asarray(outline), np.asarray(soft)))
    halo = Image.new("RGBA", (W, H), (8, 8, 12, 0))
    halo.putalpha(halo_a.point(lambda a: int(a * HALO_ALPHA)))
    return Image.alpha_composite(halo, text)


def _pad(im, p):
    out = Image.new("RGBA", (im.width + 2 * p, im.height + 2 * p), (0, 0, 0, 0))
    out.alpha_composite(im, (p, p))
    return out


def parts_of(path):
    if "neon-icon" in str(path):
        p = segment_icon(path)
        return {"icon": p.get("icon"), "eyebrow": p.get("eyebrow"), "main": p["main"],
                "sep": p.get("sep"), "secondary": p.get("secondary", [])}
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
