import unittest

import make_bedrock


def cube(frm, to, uv=(0, 0, 16, 16), rotation=None):
    faces = {name: {"uv": list(uv), "texture": "#0"} for name in ("north", "south", "east", "west", "up", "down")}
    element = {"from": list(frm), "to": list(to), "faces": faces}
    if rotation:
        element["rotation"] = rotation
    return element


class CubeTests(unittest.TestCase):
    def test_a_full_block_is_centred_and_keeps_its_size(self):
        result = make_bedrock.convert_element(cube((0, 0, 0), (16, 16, 16)), uv_space=(16, 16), texture_px=(16, 16))
        self.assertEqual(result["origin"], [-8, 0, -8])
        self.assertEqual(result["size"], [16, 16, 16])

    def test_the_x_axis_is_mirrored_around_the_centre(self):
        result = make_bedrock.convert_element(cube((2, 1, 3), (5, 4, 9)), uv_space=(16, 16), texture_px=(16, 16))
        self.assertEqual(result["origin"], [3, 1, -5])
        self.assertEqual(result["size"], [3, 3, 6])

    def test_a_cube_given_with_from_and_to_swapped_is_the_same_cube(self):
        a = make_bedrock.convert_element(cube((2, 1, 3), (5, 4, 9)), uv_space=(16, 16), texture_px=(16, 16))
        b = make_bedrock.convert_element(cube((5, 4, 9), (2, 1, 3)), uv_space=(16, 16), texture_px=(16, 16))
        self.assertEqual(a["origin"], b["origin"])
        self.assertEqual(a["size"], b["size"])


class UvTests(unittest.TestCase):
    def test_side_faces_use_the_uv_as_written(self):
        element = cube((0, 0, 0), (1, 1, 1), uv=(0, 6.5, 0.5, 7.5))
        result = make_bedrock.convert_element(element, uv_space=(16, 16), texture_px=(16, 16))
        self.assertEqual(result["uv"]["north"], {"uv": [0, 6.5], "uv_size": [0.5, 1]})

    def test_up_and_down_faces_are_flipped(self):
        result = make_bedrock.convert_element(cube((0, 0, 0), (16, 16, 16)), uv_space=(16, 16), texture_px=(16, 16))
        self.assertEqual(result["uv"]["up"], {"uv": [16, 16], "uv_size": [-16, -16]})
        self.assertEqual(result["uv"]["down"], {"uv": [16, 16], "uv_size": [-16, -16]})

    def test_a_texture_larger_than_the_uv_space_scales_the_uv(self):
        element = cube((0, 0, 0), (1, 1, 1), uv=(0, 6.5, 0.5, 7.5))
        result = make_bedrock.convert_element(element, uv_space=(16, 16), texture_px=(32, 32))
        self.assertEqual(result["uv"]["north"], {"uv": [0, 13], "uv_size": [1, 2]})

    def test_a_model_with_its_own_texture_size_is_not_scaled_again(self):
        element = cube((0, 0, 0), (1, 1, 1), uv=(2, 4, 6, 8))
        result = make_bedrock.convert_element(element, uv_space=(32, 32), texture_px=(32, 32))
        self.assertEqual(result["uv"]["east"], {"uv": [2, 4], "uv_size": [4, 4]})

    def test_a_mirrored_uv_keeps_its_negative_size(self):
        element = cube((0, 0, 0), (1, 1, 1), uv=(16, 0, 0, 16))
        result = make_bedrock.convert_element(element, uv_space=(16, 16), texture_px=(16, 16))
        self.assertEqual(result["uv"]["south"], {"uv": [16, 0], "uv_size": [-16, 16]})

    def test_all_six_faces_are_written(self):
        result = make_bedrock.convert_element(cube((0, 0, 0), (1, 1, 1)), uv_space=(16, 16), texture_px=(16, 16))
        self.assertEqual(set(result["uv"]), {"north", "south", "east", "west", "up", "down"})


class RotationTests(unittest.TestCase):
    def convert(self, axis, angle, origin):
        element = cube((0, 0, 0), (1, 1, 1), rotation={"angle": angle, "axis": axis, "origin": origin})
        return make_bedrock.convert_element(element, uv_space=(16, 16), texture_px=(16, 16))

    def test_y_rotation_keeps_its_sign_and_moves_the_pivot_to_the_centred_x(self):
        result = self.convert("y", 22.5, [9.6, 2.7, 9])
        self.assertEqual(result["rotation"], [0, 22.5, 0])
        self.assertEqual(result["pivot"], [-1.6, 2.7, 1])

    def test_x_rotation_changes_its_sign(self):
        result = self.convert("x", 45, [8, 8, 8])
        self.assertEqual(result["rotation"], [-45, 0, 0])
        self.assertEqual(result["pivot"], [0, 8, 0])

    def test_z_rotation_keeps_its_sign(self):
        result = self.convert("z", -22.5, [8, 0, 8])
        self.assertEqual(result["rotation"], [0, 0, -22.5])

    def test_an_element_without_rotation_has_neither_rotation_nor_pivot(self):
        result = make_bedrock.convert_element(cube((0, 0, 0), (1, 1, 1)), uv_space=(16, 16), texture_px=(16, 16))
        self.assertNotIn("rotation", result)
        self.assertNotIn("pivot", result)


class GeometryTests(unittest.TestCase):
    MODEL = {"textures": {"0": "hnmt:item/fish/tai", "particle": "hnmt:item/fish/tai"},
             "elements": [cube((0, 0, 0), (16, 16, 16)), cube((2, 1, 3), (5, 4, 9))]}

    def test_the_document_names_the_geometry_and_the_texture_size(self):
        doc = make_bedrock.model_to_geometry(self.MODEL, "hnmt_fish_tai", texture_px=(32, 32))
        self.assertEqual(doc["format_version"], "1.21.0")
        description = doc["minecraft:geometry"][0]["description"]
        self.assertEqual(description["identifier"], "geometry.hnmt_fish_tai")
        self.assertEqual((description["texture_width"], description["texture_height"]), (32, 32))

    def test_every_element_becomes_a_cube_in_one_bone(self):
        doc = make_bedrock.model_to_geometry(self.MODEL, "x", texture_px=(32, 32))
        bones = doc["minecraft:geometry"][0]["bones"]
        self.assertEqual(len(bones), 1)
        self.assertEqual(len(bones[0]["cubes"]), 2)

    def test_the_bone_pivot_is_the_centre_of_all_cubes(self):
        doc = make_bedrock.model_to_geometry(self.MODEL, "x", texture_px=(32, 32))
        bone = doc["minecraft:geometry"][0]["bones"][0]
        self.assertEqual(bone["pivot"], [0, 8, 0])

    def test_a_model_texture_size_sets_the_uv_space(self):
        model = {"texture_size": [32, 32], "textures": {"0": "a"}, "elements": [cube((0, 0, 0), (1, 1, 1), uv=(2, 4, 6, 8))]}
        doc = make_bedrock.model_to_geometry(model, "x", texture_px=(32, 32))
        cube_out = doc["minecraft:geometry"][0]["bones"][0]["cubes"][0]
        self.assertEqual(cube_out["uv"]["east"], {"uv": [2, 4], "uv_size": [4, 4]})

    def test_a_model_without_elements_is_refused(self):
        with self.assertRaises(ValueError):
            make_bedrock.model_to_geometry({"textures": {}, "elements": []}, "x", texture_px=(16, 16))

    def test_negative_zero_is_not_written(self):
        doc = make_bedrock.model_to_geometry({"textures": {}, "elements": [cube((8, 0, 8), (16, 1, 16))]}, "x", texture_px=(16, 16))
        text = repr(doc)
        self.assertNotIn("-0.0", text)


class PngSizeTests(unittest.TestCase):
    def test_the_size_is_read_from_the_png_header(self):
        import struct
        data = b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(">II", 32, 24) + b"\x08\x06\x00\x00\x00"
        self.assertEqual(make_bedrock.png_size(data), (32, 24))

    def test_something_that_is_not_a_png_is_refused(self):
        with self.assertRaises(ValueError):
            make_bedrock.png_size(b"not a png at all, sorry...")


class RealModelTests(unittest.TestCase):
    def test_every_3d_model_in_the_pack_converts(self):
        import glob
        import json
        import os
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        paths = sorted(glob.glob(os.path.join(root, "models3d", "**", "*.json"), recursive=True))
        self.assertGreaterEqual(len(paths), 51)
        for path in paths:
            with open(path, encoding="utf-8") as handle:
                model = json.load(handle)
            texture = model["textures"]["0"].replace("hnmt:", "")
            with open(os.path.join(root, "assets", "hnmt", "textures", texture + ".png"), "rb") as handle:
                size = make_bedrock.png_size(handle.read(32))
            doc = make_bedrock.model_to_geometry(model, os.path.basename(path), size)
            cubes = doc["minecraft:geometry"][0]["bones"][0]["cubes"]
            self.assertEqual(len(cubes), len(model["elements"]), path)
            json.dumps(doc)


if __name__ == "__main__":
    unittest.main()
