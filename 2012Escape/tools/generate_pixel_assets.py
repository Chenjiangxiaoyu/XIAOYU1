"""Generate deterministic placeholder pixel-art assets for 2012Escape.

The project intentionally starts with simple local BMP files so it can build and
load assets on a plain Visual Studio + EasyX setup without requiring external
image tools.
"""

from __future__ import annotations

import os
import struct
from dataclasses import dataclass
from typing import Iterable, Tuple

Color = Tuple[int, int, int]


@dataclass
class Canvas:
    width: int
    height: int
    bg: Color

    def __post_init__(self) -> None:
        self.pixels = [[self.bg for _ in range(self.width)] for _ in range(self.height)]

    def rect(self, x: int, y: int, w: int, h: int, color: Color) -> None:
        for yy in range(max(0, y), min(self.height, y + h)):
            row = self.pixels[yy]
            for xx in range(max(0, x), min(self.width, x + w)):
                row[xx] = color

    def line(self, x0: int, y0: int, x1: int, y1: int, color: Color) -> None:
        dx = abs(x1 - x0)
        sx = 1 if x0 < x1 else -1
        dy = -abs(y1 - y0)
        sy = 1 if y0 < y1 else -1
        err = dx + dy
        while True:
            if 0 <= x0 < self.width and 0 <= y0 < self.height:
                self.pixels[y0][x0] = color
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 >= dy:
                err += dy
                x0 += sx
            if e2 <= dx:
                err += dx
                y0 += sy

    def polygon(self, points: Iterable[Tuple[int, int]], color: Color) -> None:
        pts = list(points)
        if not pts:
            return
        min_y = max(0, min(y for _, y in pts))
        max_y = min(self.height - 1, max(y for _, y in pts))
        for y in range(min_y, max_y + 1):
            nodes = []
            j = len(pts) - 1
            for i, (xi, yi) in enumerate(pts):
                xj, yj = pts[j]
                if (yi < y and yj >= y) or (yj < y and yi >= y):
                    nodes.append(int(xi + (y - yi) / (yj - yi) * (xj - xi)))
                j = i
            nodes.sort()
            for i in range(0, len(nodes), 2):
                if i + 1 >= len(nodes):
                    break
                self.rect(nodes[i], y, nodes[i + 1] - nodes[i] + 1, 1, color)

    def save_bmp(self, path: str) -> None:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        row_pad = (4 - (self.width * 3) % 4) % 4
        pixel_size = (self.width * 3 + row_pad) * self.height
        file_size = 54 + pixel_size
        with open(path, "wb") as f:
            f.write(b"BM")
            f.write(struct.pack("<IHHI", file_size, 0, 0, 54))
            f.write(struct.pack("<IiiHHIIiiII", 40, self.width, self.height, 1, 24, 0, pixel_size, 2835, 2835, 0, 0))
            for y in range(self.height - 1, -1, -1):
                for r, g, b in self.pixels[y]:
                    f.write(bytes((b, g, r)))
                f.write(b"\0" * row_pad)


def sprite(path: str, pose: str, leg: int = 0) -> None:
    c = Canvas(32, 32, (255, 0, 255))
    outline = (39, 30, 43)
    skin = (238, 176, 116)
    hair = (71, 42, 28)
    jacket = (36, 92, 166)
    jeans = (40, 57, 97)
    shoe = (22, 22, 30)
    shirt = (242, 225, 117)
    c.rect(11, 3, 10, 3, outline); c.rect(10, 6, 12, 8, skin)
    c.rect(9, 5, 14, 4, hair); c.rect(13, 9, 2, 2, outline); c.rect(20, 9, 2, 2, outline)
    c.rect(11, 14, 11, 9, jacket); c.rect(14, 15, 5, 7, shirt)
    if pose == "jump":
        c.rect(7, 15, 4, 8, jacket); c.rect(22, 13, 4, 8, jacket)
        c.rect(11, 23, 5, 6, jeans); c.rect(19, 22, 5, 6, jeans)
        c.rect(9, 29, 6, 2, shoe); c.rect(22, 28, 6, 2, shoe)
    elif pose == "hurt":
        c.rect(7, 16, 5, 5, jacket); c.rect(22, 16, 5, 5, jacket)
        c.line(13, 10, 15, 12, outline); c.line(15, 10, 13, 12, outline)
        c.rect(12, 23, 5, 6, jeans); c.rect(18, 23, 5, 6, jeans)
    elif pose == "victory":
        c.rect(8, 9, 4, 8, jacket); c.rect(22, 7, 4, 10, jacket)
        c.rect(12, 23, 5, 6, jeans); c.rect(18, 23, 5, 6, jeans)
        c.rect(13, 29, 5, 2, shoe); c.rect(18, 29, 5, 2, shoe)
    else:
        c.rect(7, 15, 4, 8, jacket); c.rect(22, 15, 4, 8, jacket)
        offset = [-2, 0, 2, 0][leg % 4]
        c.rect(11 + offset, 23, 5, 6, jeans); c.rect(18 - offset, 23, 5, 6, jeans)
        c.rect(10 + offset, 29, 6, 2, shoe); c.rect(18 - offset, 29, 6, 2, shoe)
    c.save_bmp(path)


def level1() -> None:
    sky = Canvas(800, 450, (109, 167, 204))
    for y in range(450):
        col = (109 - y // 12, 167 - y // 18, 204 - y // 22)
        sky.rect(0, y, 800, 1, col)
    sky.rect(0, 330, 800, 120, (101, 93, 91)); sky.save_bmp("images/level1/sky.bmp")
    far = Canvas(800, 220, (255, 0, 255))
    for x, h in [(15,80),(75,120),(145,95),(230,140),(330,100),(420,130),(535,90),(635,125),(720,105)]:
        far.rect(x, 220-h, 48, h, (70, 83, 102)); far.rect(x+8, 220-h+12, 8, h-22, (98, 117, 139))
    far.save_bmp("images/level1/far_buildings.bmp")
    near = Canvas(800, 260, (255, 0, 255))
    for x, h in [(0,165),(92,125),(185,190),(315,145),(455,205),(610,150),(715,185)]:
        near.rect(x, 260-h, 78, h, (45, 49, 60))
        for wx in range(x+12, x+65, 20):
            for wy in range(260-h+18, 245, 28): near.rect(wx, wy, 8, 10, (212, 192, 101))
    near.save_bmp("images/level1/near_buildings.bmp")
    ground = Canvas(800, 96, (74, 72, 72)); ground.rect(0,0,800,10,(118,113,105));
    for x in range(0,800,32): ground.rect(x,14,16,3,(92,89,86))
    ground.save_bmp("images/level1/ground.bmp")
    crack = Canvas(64,64,(255,0,255)); crack.rect(0,42,64,16,(79,74,72)); crack.polygon([(16,36),(31,62),(43,36),(38,62)],(20,19,22)); crack.line(30,39,20,28,(20,19,22)); crack.save_bmp("images/level1/crack.bmp")
    rock = Canvas(48,48,(255,0,255)); rock.polygon([(8,34),(16,14),(33,8),(42,27),(33,40),(14,41)],(107,105,101)); rock.line(16,14,33,40,(75,72,70)); rock.save_bmp("images/level1/rock.bmp")
    block = Canvas(96,64,(255,0,255)); block.polygon([(8,48),(22,16),(82,10),(90,44),(60,56)],(126,117,106)); block.line(16,34,84,24,(81,78,75)); block.save_bmp("images/level1/collapsed_building.bmp")


def level2() -> None:
    sky = Canvas(800,450,(190,83,50))
    for y in range(450): sky.rect(0,y,800,1,(190-y//6,83-y//12,50-y//20))
    sky.rect(0,338,800,112,(52,32,25)); sky.save_bmp("images/level2/sky.bmp")
    volcano = Canvas(800,300,(255,0,255)); volcano.polygon([(170,300),(400,40),(640,300)],(84,64,61)); volcano.polygon([(360,40),(440,40),(405,92)],(243,92,25)); volcano.line(399,90,360,300,(241,83,24)); volcano.line(425,92,500,300,(229,72,25)); volcano.save_bmp("images/level2/volcano.bmp")
    forest = Canvas(800,220,(255,0,255))
    for x in range(0,800,42): forest.polygon([(x,220),(x+18,82),(x+38,220)],(31,74,45)); forest.rect(x+16,160,8,60,(76,48,29))
    forest.save_bmp("images/level2/forest.bmp")
    lava = Canvas(800,80,(91,32,20));
    for x in range(0,800,40): lava.rect(x,20+(x//40)%3*6,30,8,(255,136,24)); lava.rect(x+8,38,22,5,(247,198,47))
    lava.save_bmp("images/level2/lava_ground.bmp")
    for i, h in enumerate([48,58,44]):
        fire = Canvas(48,64,(255,0,255)); fire.polygon([(24,60),(8,30),(18,34),(22,8),(30,34),(40,28)],(230,55,23)); fire.polygon([(24,58),(16,38),(24,20),(32,38)],(255,177,35)); fire.polygon([(24,56),(20,42),(25,31),(30,43)],(255,230,93)); fire.save_bmp(f"images/level2/fire_{i+1}.bmp")
    tree = Canvas(80,64,(255,0,255)); tree.rect(8,34,64,18,(45,25,20)); tree.rect(10,36,60,12,(183,82,35)); tree.rect(14,39,54,7,(236,139,45)); tree.polygon([(14,34),(25,18),(32,36)],(96,45,28)); tree.polygon([(57,35),(68,20),(72,39)],(112,48,27)); tree.line(8,33,72,52,(255,207,72)); tree.save_bmp("images/level2/fallen_tree.bmp")
    plane = Canvas(160,80,(255,0,255)); plane.rect(30,34,92,16,(205,214,218)); plane.polygon([(110,28),(150,42),(110,50)],(205,214,218)); plane.polygon([(58,33),(86,12),(96,34)],(168,179,188)); plane.polygon([(60,50),(100,66),(92,49)],(168,179,188)); plane.rect(48,38,8,5,(68,129,172)); plane.rect(64,38,8,5,(68,129,172)); plane.save_bmp("images/level2/plane.bmp")


def ui_and_ending() -> None:
    heart = Canvas(24,24,(255,0,255)); heart.rect(6,4,5,5,(215,42,67)); heart.rect(13,4,5,5,(215,42,67)); heart.rect(4,8,16,6,(215,42,67)); heart.rect(7,14,10,4,(215,42,67)); heart.rect(10,18,4,3,(215,42,67)); heart.save_bmp("images/ui/heart.bmp")
    panel = Canvas(320,96,(38,36,45)); panel.rect(8,8,304,80,(60,57,71)); panel.rect(12,12,296,72,(29,27,36)); panel.save_bmp("images/ui/menu_panel.bmp")
    ending = Canvas(800,450,(119,188,225))
    ending.polygon([(0,350),(160,170),(305,350)],(232,238,244)); ending.polygon([(220,350),(430,100),(690,350)],(245,248,251)); ending.polygon([(500,350),(680,150),(800,350)],(230,236,242)); ending.rect(0,350,800,100,(214,229,236)); ending.rect(470,278,230,42,(99,113,130)); ending.rect(500,245,140,36,(124,139,158)); ending.rect(530,218,80,30,(150,164,180)); ending.save_bmp("images/ending/tibet_ark_base.bmp")


def main() -> None:
    sprite("images/player/player_idle.bmp", "idle")
    for i in range(4): sprite(f"images/player/player_run_{i+1}.bmp", "run", i)
    sprite("images/player/player_jump.bmp", "jump")
    sprite("images/player/player_hurt.bmp", "hurt")
    sprite("images/player/player_victory.bmp", "victory")
    level1(); level2(); ui_and_ending()

if __name__ == "__main__":
    main()
