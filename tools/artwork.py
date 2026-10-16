"""Shared pixel palette, item contract and review-sheet layout."""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
PACK = ROOT / "resourcepack"
BUILD = ROOT / "resourcepack-build"
TEXTURES = PACK / "assets/hnmt/textures/item"
OUTLINE = "#515767"
CREAM = "#fff0d8"
IVORY = "#fffbeb"
GOLD = "#e4b66e"
LEAF = "#86ae8b"
FISH = list(
    zip(
        "unagi salmon kohada konoshiro tai hirame saba hamachi buri ika kanpachi maguro".split(),
        "ウナギ サーモン コハダ コノシロ タイ ヒラメ サバ ハマチ ブリ イカ カンパチ マグロ".split(),
    )
)
RODS = list(
    zip(
        "bamboo keiryu_nami keiryu_jo iso_nami iso_jo fune_nami fune_jo".split(),
        "竹竿 渓流竿・並 渓流竿・上 磯竿・並 磯竿・上 船竿・並 船竿・上".split(),
    )
)
BAITS = list(
    zip(
        "mimizu ebi iwashi ika_no_mi".split(), "ミミズ エビ イワシ イカの切り身".split()
    )
)
SASHIMI = "salmon tai hirame hamachi buri ika kanpachi maguro saba".split()
NIGIRI = "kohada salmon tai hirame hamachi buri ika kanpachi maguro saba unagi".split()
SPECIAL = list(
    zip(
        "don_maguro don_salmon don_tai don_unagi don_ikura grill_salmon simmer_saba grill_buri grill_unagi simmer_hirame grill_konoshiro soup_tai".split(),
        "まぐろ丼 サーモン丼 鯛めし うな丼 いくら丼 鮭の塩焼き 鯖の味噌煮 鰤の照り焼き 鰻の蒲焼き ヒラメの煮付け コノシロの焼き魚 鯛のあら汁".split(),
    )
)
DISHES = (
    [(f"sashimi_{x}", dict(FISH)[x] + "の刺身") for x in SASHIMI]
    + [(f"nigiri_{x}", dict(FISH)[x] + "の握り") for x in NIGIRI]
    + SPECIAL
)
EXTRAS = [("rice", "米"), ("ikura", "いくら"), ("board", "まな板")]


class PixelDraw:
    """Logical 16-unit layout drawn directly onto a 32px pixel grid."""

    def __init__(self, image):
        self.draw = ImageDraw.Draw(image)

    @staticmethod
    def points(value):
        if isinstance(value, (tuple, list)):
            return tuple(PixelDraw.points(x) for x in value)
        return round(value * 2)

    def rectangle(self, xy, fill=None, outline=None, width=1):
        a, b, c, d = self.points(xy)
        self.draw.rectangle(
            (a, b, c + 1, d + 1), fill=fill, outline=outline, width=width * 2
        )

    def ellipse(self, xy, fill=None, outline=None, width=1):
        a, b, c, d = self.points(xy)
        self.draw.ellipse(
            (a, b, c + 1, d + 1), fill=fill, outline=outline, width=width * 2
        )

    def polygon(self, xy, fill=None, outline=None, width=1):
        self.draw.polygon(self.points(xy), fill=fill, outline=outline, width=width * 2)

    def line(self, xy, fill=None, width=1):
        self.draw.line(self.points(xy), fill=fill, width=width * 2)

    def point(self, xy, fill=None):
        x, y = self.points(xy)
        self.draw.rectangle((x, y, x + 1, y + 1), fill=fill)

    def arc(self, xy, start, end, fill=None, width=1):
        self.draw.arc(self.points(xy), start, end, fill=fill, width=width * 2)


def canvas():
    im = Image.new("RGBA", (32, 32))
    return im, PixelDraw(im)


def save(im, kind, name):
    p = TEXTURES / kind / (name + ".png")
    p.parent.mkdir(parents=True, exist_ok=True)
    im.save(p)


def font(n):
    for p in (
        "/System/Library/Fonts/ヒラギノ角ゴシック W3.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
    ):
        if Path(p).exists():
            return ImageFont.truetype(p, n)
    return ImageFont.load_default(size=n)


def sheet(entries, output, columns=4, tile=160):
    BUILD.mkdir(exist_ok=True)
    gap, label = 18, 48
    rows = (len(entries) + columns - 1) // columns
    out = Image.new(
        "RGB",
        (columns * (tile + gap) + gap, rows * (tile + label + gap) + gap),
        "#ece5d8",
    )
    d = ImageDraw.Draw(out)
    for i, (im, title, identifier) in enumerate(entries):
        x = gap + i % columns * (tile + gap)
        y = gap + i // columns * (tile + label + gap)
        for yy in range(0, tile, 10):
            for xx in range(0, tile, 10):
                d.rectangle(
                    (x + xx, y + yy, x + xx + 9, y + yy + 9),
                    fill="#d8d5cc" if (xx // 10 + yy // 10) % 2 else "#e4e1d8",
                )
        im = im.convert("RGBA").resize((tile, tile), Image.Resampling.NEAREST)
        out.paste(im, (x, y), im)
        d.text((x, y + tile + 7), title, font=font(16), fill="#414c59")
        d.text((x, y + tile + 28), identifier, font=font(11), fill="#65717c")
    out.save(BUILD / output)
