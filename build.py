"""Build the Neon TV badge set for Nuvio from badges.source.json.

Uses the original FR-Badges Neon artwork, re-laid onto one line (eyebrow,
main word, separator, secondary label) so the main word fills the tag height
on a TV. Glyphs, gradients and sheen are the original pixels.

usage:
  python3 build.py --base-url https://<user>.github.io/<repo>
  python3 build.py --base-url https://cdn.jsdelivr.net/gh/<user>/<repo>@main

Writes badges/<id>.png, neon-tv.json (the manifest to paste into Nuvio) and
preview.png. Labels and regexes live in badges.source.json; artwork in sources/neon/.
"""
import argparse
import json
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "tools"))
from relayout import combo, relayout  # noqa: E402

ART = ROOT / "sources" / "neon"       # original FR Neon artwork (MIT)

# badges that don't exist in the original set, assembled from original pieces
COMBOS = {
    "acodec-truehd-atmos": ("acodec-truehd", "acodec-atmos"),
    "acodec-ddp-atmos": ("acodec-ddplus", "acodec-atmos"),
}


def render(badge_id):
    if badge_id in COMBOS:
        left, right = COMBOS[badge_id]
        return combo(ART / f"{left}.png", ART / f"{right}.png")
    src = ART / f"{badge_id}.png"
    if not src.exists():
        raise SystemExit(f"no artwork for {badge_id}: add sources/neon/{badge_id}.png or a COMBOS entry")
    return relayout(src)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", required=True, help="public URL where this folder is hosted")
    ap.add_argument("--only", nargs="*", help="render just these badge ids")
    args = ap.parse_args()
    base = args.base_url.rstrip("/")

    src = json.loads((ROOT / "badges.source.json").read_text())
    out_dir = ROOT / "badges"
    out_dir.mkdir(exist_ok=True)

    filters, images = [], []
    for b in src["badges"]:
        if args.only and b["id"] not in args.only:
            continue
        img = render(b["id"])
        # 256-colour palette PNG: about 4x smaller, visually identical
        img.quantize(colors=256, method=Image.Quantize.FASTOCTREE,
                     dither=Image.Dither.NONE).save(out_dir / f"{b['id']}.png", optimize=True)
        images.append(img)
        filters.append({
            "id": b["id"], "groupId": b["group"], "name": b["label"].title(),
            "pattern": b["pattern"], "imageURL": f"{base}/badges/{b['id']}.png",
            "tagColor": "#00000000", "borderColor": "#00000000", "textColor": "#00000000",
            "tagStyle": "filled and bordered", "isEnabled": b["enabled"], "type": "filter",
        })

    used = {f["groupId"] for f in filters}
    groups = [{"id": g["id"], "name": g["name"], "color": "#00000000",
               "borderColor": "#00000000", "isExpanded": g["id"] not in ("languages", "subtitles")}
              for g in src["groups"] if g["id"] in used]
    (ROOT / "neon-tv.json").write_text(json.dumps({"groups": groups, "filters": filters},
                                                  ensure_ascii=False, indent=1) + "\n")

    # contact sheet at roughly TV tag height
    th, gap, sheet_w = 34, 10, 1400
    rows, row, x = [], [], 0
    for im in images:
        im = im.resize((max(1, round(im.width * th / im.height)), th), Image.LANCZOS)
        if x + im.width > sheet_w - 20 and row:
            rows.append(row)
            row, x = [], 0
        row.append(im)
        x += im.width + gap
    rows.append(row)
    sheet = Image.new("RGB", (sheet_w, len(rows) * (th + gap) + 2 * gap), (16, 16, 18))
    yy = gap
    for r in rows:
        xx = gap
        for im in r:
            sheet.paste(im, (xx, yy), im)
            xx += im.width + gap
        yy += th + gap
    sheet.save(ROOT / "preview.png", optimize=True)
    print(f"built {len(filters)} badges -> badges/, neon-tv.json, preview.png")


if __name__ == "__main__":
    main()
