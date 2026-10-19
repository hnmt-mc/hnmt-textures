"""保冷箱の寸法・面・UV・パレットと、パックの参照先を検査する。"""

import json
from pathlib import Path
import struct
import tempfile
import unittest
import zlib
from zipfile import ZipFile

import blender_coolers as coolers


class CoolerTests(unittest.TestCase):
    def test_body_and_lid_dimensions(self):
        for variant, dimensions in coolers.SIZES.items():
            with self.subTest(variant=variant):
                parts = coolers.model(variant)["elements"]
                size = lambda part: tuple(b - a for a, b in zip(part["from"], part["to"]))
                self.assertEqual(size(parts[0]), dimensions)
                self.assertEqual(size(parts[1]), (dimensions[0], 2, dimensions[2]))
                self.assertEqual(parts[1]["from"][1] - parts[0]["to"][1], 0.25)

    def test_all_geometry_stays_inside_one_block(self):
        for variant in coolers.SIZES:
            data = coolers.model(variant)
            for part in data["elements"]:
                for low, high in zip(part["from"], part["to"]):
                    self.assertLess(low, high)
                    self.assertGreaterEqual(low, 0)
                    self.assertLessEqual(high, 16)
                self.assertNotIn("rotation", part)
            self.assertLessEqual(len(data["elements"]), 8)
            self.assertLessEqual(sum(len(p["faces"]) for p in data["elements"]), 42)

    def test_ice_count_and_display_modes(self):
        for index, variant in enumerate(coolers.SIZES):
            data = coolers.model(variant)
            self.assertEqual(sum(p["name"].startswith("ice_") for p in data["elements"]), index)
            self.assertEqual(set(data["display"]), {"gui", "ground", "fixed", "firstperson_righthand", "thirdperson_righthand"})
            for transform in data["display"].values():
                for field in ("rotation", "translation", "scale"):
                    self.assertEqual(len(transform[field]), 3)

    def test_each_face_has_a_valid_uv_and_outward_normal(self):
        normals = {"north": (0, 0, -1), "south": (0, 0, 1), "west": (-1, 0, 0),
                   "east": (1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}
        for variant in coolers.SIZES:
            for part in coolers.model(variant)["elements"]:
                vertices = coolers.vertices(part)
                for direction, face in part["faces"].items():
                    uv = coolers.face_uv(direction, face["uv"])
                    self.assertEqual(len(set(uv)), 4)
                    self.assertTrue(all(0 <= value <= 1 for pair in uv for value in pair))
                    a, b, c = [vertices[i] for i in coolers.FACE_VERTICES[direction][:3]]
                    u, v = [b[i] - a[i] for i in range(3)], [c[i] - a[i] for i in range(3)]
                    normal = (u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0])
                    self.assertGreater(sum(normal[i] * normals[direction][i] for i in range(3)), 0)

    def test_png_has_exactly_eight_opaque_colors_and_valid_checksums(self):
        for variant in coolers.SIZES:
            data = coolers.png_bytes(variant)
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            offset, compressed = 8, b""
            while offset < len(data):
                length = struct.unpack(">I", data[offset:offset + 4])[0]
                kind = data[offset + 4:offset + 8]
                payload = data[offset + 8:offset + 8 + length]
                checksum = struct.unpack(">I", data[offset + 8 + length:offset + 12 + length])[0]
                self.assertEqual(checksum, zlib.crc32(kind + payload) & 0xFFFFFFFF)
                if kind == b"IHDR":
                    self.assertEqual(struct.unpack(">IIBBBBB", payload), (32, 32, 8, 6, 0, 0, 0))
                if kind == b"IDAT":
                    compressed += payload
                offset += length + 12
            raw = zlib.decompress(compressed)
            self.assertEqual(len(raw), 32 * 129)
            colors = set()
            for y in range(32):
                row = raw[y * 129:(y + 1) * 129]
                self.assertEqual(row[0], 0)
                colors.update(row[x:x + 4] for x in range(1, 129, 4))
            expected = {bytes.fromhex(rgb) + b"\xff" for rgb in coolers.PALETTES[variant]}
            self.assertEqual(colors, expected)

    def test_panel_borders_remain_one_pixel_dark(self):
        for variant in coolers.SIZES:
            texture = coolers.texture_indices(variant)
            for x0, y0, x1, y1 in coolers.PANELS.values():
                self.assertTrue(all(texture[y0][x] == texture[y1 - 1][x] == 0 for x in range(x0, x1)))
                self.assertTrue(all(texture[y][x0] == texture[y][x1 - 1] == 0 for y in range(y0, y1)))

    def test_pack_references_resolve_and_zip_has_no_absolute_paths(self):
        with tempfile.TemporaryDirectory() as folder:
            output = Path(folder)
            coolers.write_assets(output)
            for variant in coolers.SIZES:
                model = json.loads((output / f"pack/assets/hnmt/models/item/cooler/{variant}.json").read_text())
                reference = model["textures"]["0"].split(":", 1)[1]
                self.assertTrue((output / f"pack/assets/hnmt/textures/{reference}.png").is_file())
                item = json.loads((output / f"pack/assets/hnmt/items/cooler/{variant}.json").read_text())
                self.assertEqual(item["model"]["model"], f"hnmt:item/cooler/{variant}")
                self.assertEqual((output / f"cooler_{variant}.png").read_bytes(), (output / f"pack/assets/hnmt/textures/{reference}.png").read_bytes())
            with ZipFile(output / "hnmt-coolers-pack.zip") as archive:
                self.assertEqual(len(archive.namelist()), 10)
                self.assertTrue(all(not name.startswith("/") and ".." not in Path(name).parts for name in archive.namelist()))

    def test_invalid_geometry_and_uv_fail(self):
        data = coolers.model("small")
        data["elements"][0]["to"][0] = 17
        with self.assertRaises(ValueError):
            coolers.validate_model(data)
        data = coolers.model("small")
        data["elements"][0]["faces"]["up"]["uv"] = [0, 0, 17, 16]
        with self.assertRaises(ValueError):
            coolers.validate_model(data)


if __name__ == "__main__":
    unittest.main()
