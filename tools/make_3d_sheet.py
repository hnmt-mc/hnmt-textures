#!/usr/bin/env python3
"""Blender のプレビュー（resourcepack-build/preview3d）を1枚の見本にまとめる。"""
import glob, os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
D = os.path.join(ROOT, "resourcepack-build")
ORDER = [("unagi", "ウナギ"), ("salmon", "サーモン"), ("kohada", "コハダ"), ("konoshiro", "コノシロ"),
         ("tai", "タイ"), ("hirame", "ヒラメ"), ("saba", "サバ"), ("hamachi", "ハマチ"),
         ("buri", "ブリ"), ("ika", "イカ"), ("kanpachi", "カンパチ"), ("maguro", "マグロ")]
fonts = glob.glob("/System/Library/Fonts/ヒラギノ角ゴシック*") + glob.glob("/System/Library/Fonts/*Hiragino*")
font = ImageFont.truetype(fonts[0], 19) if fonts else ImageFont.load_default()
T, pad, lab, cols = 300, 12, 30, 4
rows = 3
sheet = Image.new("RGB", (cols * (T + pad) + pad, rows * (T + lab + pad) + pad), (58, 62, 70))
d = ImageDraw.Draw(sheet)
for i, (fid, name) in enumerate(ORDER):
    x, y = pad + (i % cols) * (T + pad), pad + (i // cols) * (T + lab + pad)
    tile = Image.new("RGB", (T, T), (92, 100, 112))
    im = Image.open(os.path.join(D, "preview3d", fid + ".png")).convert("RGBA").resize((T, T), Image.LANCZOS)
    tile.paste(im, (0, 0), im)
    sheet.paste(tile, (x, y))
    d.text((x, y + T + 4), f"{name}  {fid}", font=font, fill=(240, 240, 240))
sheet.save(os.path.join(D, "contact_sheet_3d.png"))

# 釣竿の見本（preview3d/rod_<ID>.png がある場合）
RODS = [("bamboo", "竹竿"), ("keiryu_nami", "渓流竿(並)"), ("keiryu_jo", "渓流竿(上)"), ("iso_nami", "磯竿(並)"),
        ("iso_jo", "磯竿(上)"), ("fune_nami", "船竿(並)"), ("fune_jo", "船竿(上)")]
if os.path.exists(os.path.join(D, "preview3d", "rod_bamboo.png")):
    T2 = 260
    rs = Image.new("RGB", (4 * (T2 + pad) + pad, 2 * (T2 + lab + pad) + pad), (58, 62, 70))
    rd = ImageDraw.Draw(rs)
    for i, (rid, name) in enumerate(RODS):
        x, y = pad + (i % 4) * (T2 + pad), pad + (i // 4) * (T2 + lab + pad)
        tile = Image.new("RGB", (T2, T2), (92, 100, 112))
        im = Image.open(os.path.join(D, "preview3d", f"rod_{rid}.png")).convert("RGBA").resize((T2, T2), Image.LANCZOS)
        tile.paste(im, (0, 0), im)
        rs.paste(tile, (x, y))
        rd.text((x, y + T2 + 4), f"{name}  {rid}", font=font, fill=(240, 240, 240))
    rs.save(os.path.join(D, "rods_contact_sheet_3d.png"))
