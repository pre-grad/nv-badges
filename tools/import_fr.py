"""One-off importer: builds badges.source.json from FR-Badges (MIT, farizmohd70).

Takes FR's filter list and Neon colours, swaps in short single-line TV labels,
and applies the regex fixes. After this runs, badges.source.json is the only
file you edit; build.py renders everything from it.

usage: python3 -I tools/import_fr.py <fr-badges-dir> <neon_colors.json>
"""
import json
import sys
from pathlib import Path

FR = Path(sys.argv[1])
COLORS = json.loads(Path(sys.argv[2]).read_text())
OUT = Path(__file__).resolve().parent.parent / "badges.source.json"

fr = json.loads((FR / "badges.json").read_text())

# ---------------------------------------------------------------- labels
LABELS = {
    "hero-remux": "REMUX", "hero-4k": "4K", "hero-dolby-vision": "DOLBY VISION",
    "hero-dolby-atmos": "DOLBY ATMOS", "hero-cached": "CACHED",
    "edition-imax-enhanced": "IMAX ENHANCED", "edition-imax": "IMAX",
    "edition-open-matte": "OPEN MATTE", "edition-criterion": "CRITERION",
    "edition-directors-cut": "DIRECTOR'S CUT", "edition-extended": "EXTENDED",
    "edition-theatrical": "THEATRICAL", "edition-final-cut": "FINAL CUT",
    "edition-special": "SPECIAL EDITION", "edition-unrated": "UNRATED",
    "edition-hybrid": "HYBRID", "edition-remastered": "REMASTERED",
    "edition-proper": "PROPER", "edition-seadex": "SEADEX",
    "source-remux": "REMUX", "source-uhd-bluray": "UHD BLU-RAY",
    "source-bluray": "BLU-RAY", "source-webdl": "WEB-DL", "source-webrip": "WEBRIP",
    "source-hdtv": "HDTV", "source-dvd": "DVD", "source-tvrip": "TVRIP",
    "source-hdrip": "HDRIP", "source-hc-hdrip": "HC HDRIP", "source-scr": "SCREENER",
    "source-tc": "TELECINE", "source-ts": "TELESYNC", "source-cam": "CAM",
    "res-8k": "8K", "res-4k": "4K", "res-1440p": "1440P", "res-1080p": "1080P",
    "res-720p": "720P", "res-576p": "576P", "res-480p": "480P", "res-360p": "360P",
    "dr-dolby-vision": "DOLBY VISION", "dr-dv-p7": "DV P7", "dr-dv-p8": "DV P8",
    "dr-dv-hdr": "DV HDR10", "dr-dv-hdr10plus": "DV HDR10+", "dr-hdr10plus": "HDR10+",
    "dr-hdr10": "HDR10", "dr-hdr": "HDR", "dr-hlg": "HLG", "dr-12bit": "12-BIT",
    "dr-10bit": "10-BIT", "dr-8bit": "8-BIT", "dr-sdr": "SDR",
    "format-3d": "3D", "format-hfr": "HFR", "format-60fps": "60 FPS",
    "format-50fps": "50 FPS", "format-live": "LIVE", "format-interlaced": "INTERLACED",
    "acodec-truehd-atmos": "TRUEHD ATMOS", "acodec-ddp-atmos": "DD+ ATMOS",
    "acodec-atmos": "ATMOS", "acodec-truehd": "TRUEHD", "acodec-ddplus": "DD+",
    "acodec-dd": "DD", "acodec-ac4": "AC-4", "acodec-dtsx": "DTS:X",
    "acodec-dtshd-ma": "DTS-HD MA", "acodec-dtshd-hra": "DTS-HD HRA",
    "acodec-dtses": "DTS-ES", "acodec-dts": "DTS", "acodec-flac": "FLAC",
    "acodec-alac": "ALAC", "acodec-pcm": "PCM", "acodec-aac": "AAC",
    "acodec-opus": "OPUS", "acodec-vorbis": "VORBIS", "acodec-mp3": "MP3",
    "acodec-wma": "WMA",
    "codec-vvc": "VVC", "codec-av1": "AV1", "codec-hevc": "HEVC", "codec-avc": "AVC",
    "codec-prores": "PRORES", "codec-vp9": "VP9", "codec-vp8": "VP8",
    "codec-vc1": "VC-1", "codec-xvid": "XVID", "codec-divx": "DIVX",
    "container-mkv": "MKV", "container-mp4": "MP4", "container-ts": "M2TS",
    "container-avi": "AVI",
    "ch-7-1-4": "7.1.4", "ch-7-1-2": "7.1.2", "ch-5-1-4": "5.1.4", "ch-5-1-2": "5.1.2",
    "ch-7-1": "7.1", "ch-6-1": "6.1", "ch-5-1": "5.1", "ch-2-1": "2.1",
    "ch-2-0": "2.0", "ch-1-0": "MONO",
    "debrid-realdebrid": "REAL-DEBRID", "debrid-alldebrid": "ALLDEBRID",
    "debrid-premiumize": "PREMIUMIZE", "debrid-torbox": "TORBOX",
    "debrid-debridlink": "DEBRID-LINK",
    "flag-dual-audio": "DUAL AUDIO", "flag-multi-audio": "MULTI AUDIO",
    "flag-dubbed": "DUBBED", "flag-original-audio": "ORIGINAL AUDIO",
    "flag-multi-sub": "MULTI SUBS", "flag-subpack": "SUBPACK", "flag-cc": "CC",
    "flag-commentary": "COMMENTARY", "flag-audio-description": "AUDIO DESC",
}

# Languages: English names, since the Neon set's native scripts need fonts
# most TVs render poorly at tag size and Inter has no Indic/CJK glyphs.
LANG = {
    "en": "ENGLISH", "en-us": "ENGLISH US", "en-gb": "ENGLISH UK", "ml": "MALAYALAM",
    "ta": "TAMIL", "hi": "HINDI", "te": "TELUGU", "kn": "KANNADA", "bn": "BENGALI",
    "mr": "MARATHI", "gu": "GUJARATI", "pa": "PUNJABI", "ur": "URDU", "ja": "JAPANESE",
    "ko": "KOREAN", "zh": "CHINESE", "zh-tw": "CHINESE TW", "yue": "CANTONESE",
    "ar": "ARABIC", "es": "SPANISH", "es-419": "LATINO", "fr": "FRENCH", "de": "GERMAN",
    "it": "ITALIAN", "pt": "PORTUGUESE", "ru": "RUSSIAN", "tr": "TURKISH", "pl": "POLISH",
    "nl": "DUTCH", "sv": "SWEDISH", "no": "NORWEGIAN", "da": "DANISH", "fi": "FINNISH",
    "el": "GREEK", "fa": "PERSIAN", "th": "THAI", "vi": "VIETNAMESE", "id": "INDONESIAN",
    "ms": "MALAY", "tl": "FILIPINO", "uk": "UKRAINIAN", "cs": "CZECH", "hu": "HUNGARIAN",
    "ro": "ROMANIAN", "bg": "BULGARIAN", "hr": "CROATIAN", "sr": "SERBIAN", "sk": "SLOVAK",
    "sl": "SLOVENIAN", "lt": "LITHUANIAN", "lv": "LATVIAN", "et": "ESTONIAN",
    "ca": "CATALAN", "ka": "GEORGIAN", "hy": "ARMENIAN", "az": "AZERBAIJANI",
    "kk": "KAZAKH", "uz": "UZBEK", "mn": "MONGOLIAN", "si": "SINHALA", "my": "BURMESE",
    "km": "KHMER", "lo": "LAO", "ne": "NEPALI", "as": "ASSAMESE", "or": "ODIA",
    "sw": "SWAHILI", "bs": "BOSNIAN", "mk": "MACEDONIAN", "sq": "ALBANIAN",
    "be": "BELARUSIAN", "ht": "HAITIAN", "ku": "KURDISH", "ps": "PASHTO", "sd": "SINDHI",
    "bo": "TIBETAN", "ha": "HAUSA", "yo": "YORUBA",
}
SUB_SHORT = {"en": "ENG", "ml": "MAL", "ta": "TAMIL", "hi": "HINDI", "te": "TELUGU",
             "kn": "KANNADA", "ja": "JAP", "ko": "KOR", "es": "SPA", "fr": "FRE"}

STREAM_SHORT = {
    "stream-prime-video": "PRIME VIDEO", "stream-apple-tv": "APPLE TV+",
    "stream-disney-plus": "DISNEY+", "stream-max": "MAX", "stream-paramount": "PARAMOUNT+",
    "stream-sonyliv": "SONYLIV", "stream-iplayer": "IPLAYER", "stream-ch4": "CHANNEL 4",
    "stream-canal": "CANAL+", "stream-movistar": "MOVISTAR+", "stream-criterion-ch": "CRITERION CH",
    "stream-pluto": "PLUTO TV", "stream-rakuten": "RAKUTEN TV", "stream-discovery-plus": "DISCOVERY+",
    "stream-curiositystream": "CURIOSITY", "stream-adultswim": "ADULT SWIM",
    "stream-sunnxt": "SUN NXT", "stream-wowtv": "WOW", "stream-jiohotstar": "JIOHOTSTAR",
    "stream-jiocinema": "JIOCINEMA",
}


def label_for(f):
    i = f["id"]
    if i in LABELS:
        return LABELS[i]
    if i.startswith("lang-"):
        return LANG[i[5:]]
    if i.startswith("sub-"):
        return SUB_SHORT[i[4:]] + " SUBS"
    if i.startswith("stream-"):
        return STREAM_SHORT.get(i, f["name"].upper())
    raise KeyError(i)


# ---------------------------------------------------------------- regex fixes
# Shared tokens. Lookarounds instead of \b so "DDP5.1", "AAC2.0", "DTS5.1" match.
TRUEHD = r"(?<![a-z0-9])true[\s._-]*hd(?![a-z])"
ATMOS = r"(?<![a-z0-9])(?:atmos|ddpa\d?)(?![a-z])"
DDP = r"(?<![a-z0-9])(?:ddpa|ddp|dd\+|dolby[\s._-]*digital[\s._-]*plus|e-?ac-?3)(?![a-z+])"
DD = r"(?<![a-z0-9])(?:dd|dolby[\s._-]*digital|ac-?3)(?![a-z+])"

AUDIO = {
    # Combos first so the common premium tracks always get one badge.
    "acodec-truehd-atmos": f"(?is)^(?=.*{TRUEHD})(?=.*{ATMOS})",
    "acodec-ddp-atmos": f"(?is)^(?=.*{DDP})(?=.*{ATMOS})(?!.*{TRUEHD})",
    "acodec-atmos": f"(?is)^(?=.*{ATMOS})(?!.*{TRUEHD})(?!.*{DDP})",
    "acodec-truehd": f"(?is)^(?=.*{TRUEHD})(?!.*{ATMOS})",
    "acodec-ddplus": f"(?is)^(?=.*{DDP})(?!.*{ATMOS})(?!.*{TRUEHD})",
    "acodec-dd": f"(?is)^(?=.*{DD})(?!.*{DDP})(?!.*{ATMOS})(?!.*{TRUEHD})",
    "acodec-dtses": r"(?i)(?<![a-z0-9])dts[\s._-]*es(?![a-z])",
    "acodec-dts": r"(?i)(?<![a-z0-9])dts(?![a-z])(?![\s._:-]*(?:hd|x|ma|es|hra)(?![a-z]))",
    "acodec-ac4": r"(?i)(?<![a-z0-9])ac-?4(?![a-z0-9])",
}
for name, tok in {"flac": "flac", "alac": "alac", "pcm": "l?pcm", "aac": "aac",
                  "opus": "opus", "vorbis": "(?:vorbis|ogg)", "mp3": "mp3", "wma": "wma"}.items():
    AUDIO[f"acodec-{name}"] = rf"(?i)(?<![a-z0-9]){tok}(?![a-z])"

# Channels: allow a codec glued in front ("DDP5.1") and a dot ("TrueHD.7.1"),
# but not a version number ("v2.0", "1.2.0"). Only treat a following single 2/4 as
# Atmos height ("7.1.4"), so "5.1 2160p" and "7.1 2024" still match.
PRE = r"(?<![0-9v])(?<![0-9]\.)"
HEIGHT = r"(?![\s._-][24](?![0-9]))"
CH = {
    "ch-7-1-4": rf"(?i){PRE}7[\s._-]1[\s._-]4(?![0-9])",
    "ch-7-1-2": rf"(?i){PRE}7[\s._-]1[\s._-]2(?![0-9])",
    "ch-5-1-4": rf"(?i){PRE}5[\s._-]1[\s._-]4(?![0-9])",
    "ch-5-1-2": rf"(?i){PRE}5[\s._-]1[\s._-]2(?![0-9])",
    "ch-7-1": rf"(?i){PRE}(?:7[\s._-]1|8ch)(?![0-9]){HEIGHT}",
    "ch-6-1": rf"(?i){PRE}(?:6[\s._-]1|7ch)(?![0-9])",
    "ch-5-1": rf"(?i){PRE}(?:5[\s._-]1|6ch)(?![0-9]){HEIGHT}",
    "ch-2-1": rf"(?i){PRE}(?:2[\s._-]1|3ch)(?![0-9])",
    "ch-2-0": rf"(?i)(?:{PRE}(?:2[\s._-]0|2ch)(?![0-9])|\bstereo\b)",
    "ch-1-0": rf"(?i)(?:{PRE}(?:1[\s._-]0|1ch)(?![0-9])|\bmono\b)",
}

OVERRIDES = {**AUDIO, **CH}

# ---------------------------------------------------------------- assemble
src_filters = list(fr["filters"])
# insert the two Atmos combos before plain Atmos
at = next(i for i, f in enumerate(src_filters) if f["id"] == "acodec-atmos")
src_filters[at:at] = [
    {"id": "acodec-truehd-atmos", "groupId": "audio-codec", "isEnabled": True, "pattern": ""},
    {"id": "acodec-ddp-atmos", "groupId": "audio-codec", "isEnabled": True, "pattern": ""},
]


def colors_for(i):
    c = COLORS.get(i)
    if c:
        return c["accent"]
    if i == "acodec-truehd-atmos":
        return COLORS["acodec-truehd"]["accent"]
    if i == "acodec-ddp-atmos":
        return COLORS["acodec-ddplus"]["accent"]
    raise KeyError(i)


badges = []
for f in src_filters:
    pat = OVERRIDES.get(f["id"], f["pattern"])
    if f["groupId"] == "video-codec":
        pat = pat.replace(r"h\.?26", r"h[\s.]?26")  # also match "H 264"
    badges.append({
        "id": f["id"],
        "group": f["groupId"],
        "label": label_for(f),
        "accent": colors_for(f["id"]),
        "enabled": f["isEnabled"],
        "pattern": pat,
    })

source = {
    "name": "Neon TV",
    "credit": "Patterns and colours derived from FR-Badges by farizmohd70 (MIT)",
    "groups": [{"id": g["id"], "name": g["name"]} for g in fr["groups"]],
    "badges": badges,
}
OUT.write_text(json.dumps(source, ensure_ascii=False, indent=1) + "\n")
print(f"wrote {OUT} with {len(badges)} badges")
