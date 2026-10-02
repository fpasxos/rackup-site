"""Rebuilds assets/fonts from the OFL sources in github.com/google/fonts. Dev only:
pip install fonttools brotli && python tools/make_fonts.py
Latin faces are the app's (Space Grotesk, Hanken Grotesk); Commissioner supplies Greek for both.
"""
import tempfile
import urllib.request
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "assets" / "fonts"
SOURCE = "https://github.com/google/fonts/raw/main/ofl/"
LATIN = ("U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,"
         "U+2000-206F,U+20AC,U+2122,U+2190-2193,U+2212,U+2215,U+FEFF,U+FFFD")
GREEK = "U+0370-0377,U+037A-037F,U+0384-038A,U+038C,U+038E-03A1,U+03A3-03FF,U+1F00-1FFF"
FONTS = (
    ("spacegrotesk", "SpaceGrotesk[wght].ttf", "space-grotesk-latin.woff2", LATIN, {}, "SpaceGrotesk"),
    ("hankengrotesk", "HankenGrotesk[wght].ttf", "hanken-grotesk-latin.woff2", LATIN, {}, "HankenGrotesk"),
    ("commissioner", "Commissioner[FLAR,VOLM,slnt,wght].ttf", "commissioner-greek.woff2", GREEK,
     {"FLAR": 0, "VOLM": 0, "slnt": 0, "wght": (400, 800)}, "Commissioner"),
)


def fetch(url, dest):
    with urllib.request.urlopen(url) as response:
        dest.write_bytes(response.read())
    return dest


def ranges(spec):
    out = []
    for part in spec.split(","):
        lo, _, hi = part.replace("U+", "").partition("-")
        out.extend(range(int(lo, 16), int(hi or lo, 16) + 1))
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        for folder, name, target, unicodes, pins, licence in FONTS:
            src = fetch(SOURCE + folder + "/" + name.replace("[", "%5B").replace("]", "%5D"), Path(tmp, name))
            fetch(SOURCE + folder + "/OFL.txt", OUT / f"OFL-{licence}.txt")
            font = TTFont(src)
            if pins:
                font = instancer.instantiateVariableFont(font, pins)
            options = subset.Options()
            options.flavor = "woff2"
            options.layout_features = ["*"]
            options.name_IDs = ["*"]
            sub = subset.Subsetter(options)
            sub.populate(unicodes=ranges(unicodes))
            sub.subset(font)
            font.flavor = "woff2"
            font.save(OUT / target)
            print(f"{target}: {(OUT / target).stat().st_size // 1024} KB")


if __name__ == "__main__":
    main()
