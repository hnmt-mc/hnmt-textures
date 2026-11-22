"""ドット絵を、距離で塗るための小さな道具（刀・銃の64×64の絵で使う）。

形を、中心線からの距離で決める（曲がった刃・先細りの銃身など）。塗りは、ぼかさず、1ドットずつ（アンチエイリアスなし）。
"""
import math
import random
from PIL import Image


def rgba(color):
    if isinstance(color, tuple): return color if len(color) == 4 else color + (255,)
    return tuple(bytes.fromhex(color[1:])) + (255,)


def mix(a, b, t):
    """2色の間（t=0 で a、t=1 で b）。"""
    a, b = rgba(a), rgba(b)
    return tuple(int(round(a[i] + (b[i] - a[i]) * t)) for i in range(4))


class Canvas:
    def __init__(self, size):
        self.size = size
        self.image = Image.new('RGBA', (size, size))

    def put(self, x, y, color):
        x, y = int(x), int(y)
        if 0 <= x < self.size and 0 <= y < self.size: self.image.putpixel((x, y), rgba(color))

    def get(self, x, y):
        return self.image.getpixel((x, y)) if 0 <= x < self.size and 0 <= y < self.size else (0, 0, 0, 0)

    def line(self, a, b, color, width=1):
        """太さのある直線（ドットを並べる）。"""
        steps = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) * 2 + 1
        for i in range(steps + 1):
            t = i / steps
            x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
            for dx in range(width):
                for dy in range(width): self.put(x + dx - (width - 1) / 2 + 0.5, y + dy - (width - 1) / 2 + 0.5, color)

    def fill(self, shape, shader):
        """shape(x, y) が真の点を、shader(x, y) の色で塗る。x, y は、ドットの中心。"""
        for y in range(self.size):
            for x in range(self.size):
                if shape(x + 0.5, y + 0.5): self.put(x, y, shader(x + 0.5, y + 0.5))

    def outline(self, color):
        """絵の縁（透明に接している外側のドット）に、輪郭の色を付ける。"""
        source = self.image.copy()
        for y in range(self.size):
            for x in range(self.size):
                if source.getpixel((x, y))[3] != 0: continue
                if any(0 <= x + dx < self.size and 0 <= y + dy < self.size and source.getpixel((x + dx, y + dy))[3] != 0
                       for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))): self.put(x, y, color)


class Curve:
    """点の並びでできた中心線。ある点から見た、最も近い位置（0〜1）と、左右の距離（符号つき）を返す。"""

    def __init__(self, points, samples=300):
        self.points = []
        for i in range(samples + 1):
            t = i / samples
            self.points.append(self.at(points, t))
        self.length = sum(math.dist(self.points[i], self.points[i + 1]) for i in range(samples))
        self.samples = samples

    @staticmethod
    def at(points, t):
        """ベジェ曲線（点の数で次数が決まる）上の、位置 t の点。"""
        pts = list(points)
        while len(pts) > 1: pts = [(pts[i][0] + (pts[i + 1][0] - pts[i][0]) * t, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * t) for i in range(len(pts) - 1)]
        return pts[0]

    def locate(self, x, y):
        best, best_d, best_i = None, 1e9, 0
        for i, (px, py) in enumerate(self.points):
            d = (px - x) ** 2 + (py - y) ** 2
            if d < best_d: best, best_d, best_i = (px, py), d, i
        i = best_i
        j = min(i + 1, self.samples) if i < self.samples else i - 1
        k = i if j > i else j
        ax, ay = self.points[k]
        bx, by = self.points[k + 1]
        tx, ty = bx - ax, by - ay
        norm = math.hypot(tx, ty) or 1.0
        # 進む向きの左（画面では、反時計まわり）を正とする符号つきの距離
        u = ((x - best[0]) * -ty + (y - best[1]) * tx) / norm
        return i / self.samples, u

    def point(self, t): return self.points[int(max(0, min(1, t)) * self.samples)]


def noise(seed):
    return random.Random(seed)
