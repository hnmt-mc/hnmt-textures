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


class AllItemsTests(unittest.TestCase):
    ROOT = None

    @classmethod
    def setUpClass(cls):
        import os
        cls.ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

    def bases(self):
        import json
        import os
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bedrock_bases.json"), encoding="utf-8") as handle:
            return json.load(handle)

    def model_items(self):
        """パックにある、3Dモデルを持つ品（models3d の全部と、assets のクーラーボックス）。"""
        import glob
        import os
        items = set()
        for path in glob.glob(os.path.join(self.ROOT, "models3d", "**", "*.json"), recursive=True):
            items.add(os.path.relpath(path, os.path.join(self.ROOT, "models3d"))[:-5])
        for path in glob.glob(os.path.join(self.ROOT, "assets", "hnmt", "models", "item", "cooler", "*.json")):
            items.add("cooler/" + os.path.basename(path)[:-5])
        # 田んぼに立つ稲（rice/plant_*）は、世界に出す ItemDisplay 用で、持ち物のアイテムではない。
        # 統合版で見えるかが未確認なので、対象にしない（2026-10-21 決定）。
        items -= {"rice/plant_seedling", "rice/plant_growing", "rice/plant_mature"}
        # 釣竿は入れない。統合版では、カスタムアイテムにすると、釣りボタンが出ず、手に持つ向きも反転するので、
        # ふつうの釣竿のままにする（2026-10-20 決定）。
        return items

    def test_every_3d_item_has_a_base_item_and_nothing_else_does(self):
        self.assertEqual(set(self.bases()), self.model_items())

    def test_fishing_rods_stay_vanilla_on_bedrock(self):
        self.assertEqual([item for item in self.bases() if item.startswith("rod/")], [])
        self.assertNotIn("minecraft:fishing_rod", self.bases().values())

    def test_every_base_is_a_vanilla_item(self):
        for item, base in self.bases().items():
            self.assertRegex(base, r"^minecraft:[a-z_]+$", item)

    def test_the_whole_pack_builds_and_every_reference_exists(self):
        import json
        import os
        import tempfile
        with tempfile.TemporaryDirectory() as out:
            make_bedrock.build_pack(self.ROOT, out, self.bases(), "v0.1.0")
            pack = os.path.join(out, "pack")
            with open(os.path.join(pack, "textures", "item_texture.json"), encoding="utf-8") as handle:
                atlas = json.load(handle)
            rods = [item for item in self.bases() if item.startswith("rod/")]
            self.assertEqual(len(atlas["texture_data"]), len(self.bases()) + len(rods), "釣竿は、投げた状態の絵も入る")
            for entry in atlas["texture_data"].values():
                self.assertTrue(os.path.exists(os.path.join(pack, entry["textures"][0] + ".png")))
            for item in self.bases():
                name = make_bedrock.safe_name(item)
                if item.startswith("rod/"):
                    continue
                for path in ("models/entity/hnmt_%s.geo.json", "animations/hnmt_%s.animation.json", "attachables/hnmt_%s.json",
                             "textures/entity/hnmt/%s.png"):
                    self.assertTrue(os.path.exists(os.path.join(pack, path % name)), path % name)
            with open(os.path.join(out, "custom_mappings", "hnmt.json"), encoding="utf-8") as handle:
                mappings = json.load(handle)
            models = [(d["model"], json.dumps(d.get("predicate"))) for defs in mappings["items"].values() for d in defs]
            self.assertEqual(len(models), len(set(models)), "同じ model と条件の組が2回ある")
            identifiers = [d["bedrock_identifier"] for defs in mappings["items"].values() for d in defs]
            self.assertEqual(len(identifiers), len(set(identifiers)))


class BlockTests(unittest.TestCase):
    """石臼のように、ハーフブロックの上に立つ置き物を、統合版のカスタムブロックにする。"""
    ROOT = None
    # 石臼（下半分）とまな板（2段）は、同じ Java のブロック（石化したオークのハーフブロック）の、別の状態を使う。
    TABLE = {"board": {"java_block": "minecraft:petrified_oak_slab", "state": "type=double,waterlogged=false",
                       "slab_height": 0, "model": "block/board", "display_name": "Cutting Board"},
             "rice/mill": {"java_block": "minecraft:petrified_oak_slab", "state": "type=bottom,waterlogged=false",
                           "slab_height": 8, "display_name": "Stone Mill"}}

    @classmethod
    def setUpClass(cls):
        import os
        cls.ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")

    def model(self):
        import json
        import os
        with open(os.path.join(self.ROOT, "models3d", "rice", "mill.json"), encoding="utf-8") as handle:
            return json.load(handle)

    def geometry(self):
        return make_bedrock.block_geometry(self.model(), "hnmt_block_rice_mill", (16, 16), slab_height=8)

    def cubes(self):
        return self.geometry()["minecraft:geometry"][0]["bones"][0]["cubes"]

    def test_the_geometry_is_one_slab_plus_the_model_stacked_on_it(self):
        cubes = self.cubes()
        self.assertEqual(len(cubes), 1 + len(self.model()["elements"]))
        slab = cubes[0]
        self.assertEqual(slab["origin"], [-8, 0, -8])
        self.assertEqual(slab["size"], [16, 8, 16])

    def test_every_cube_stays_inside_one_block(self):
        for cube in self.cubes():
            self.assertGreaterEqual(cube["origin"][0], -8)
            self.assertLessEqual(cube["origin"][0] + cube["size"][0], 8)
            self.assertGreaterEqual(cube["origin"][2], -8)
            self.assertLessEqual(cube["origin"][2] + cube["size"][2], 8)
            self.assertGreaterEqual(cube["origin"][1], 0)
            self.assertLessEqual(cube["origin"][1] + cube["size"][1], 16)

    def test_the_model_sits_on_the_slab_and_fills_the_rest_of_the_height(self):
        cubes = self.cubes()
        self.assertEqual(min(c["origin"][1] for c in cubes[1:]), 8)
        self.assertEqual(max(c["origin"][1] + c["size"][1] for c in cubes), 16)

    def test_the_slab_uses_the_base_part_of_the_texture_on_every_face(self):
        faces = self.cubes()[0]["uv"]
        self.assertEqual(set(faces), set(make_bedrock.FACES))
        for face in faces.values():
            self.assertEqual(face["uv"][0] + face["uv_size"][0] <= 16, True)

    def test_a_model_that_is_already_too_tall_is_squeezed_not_clipped(self):
        tall = {"elements": [cube((0, 0, 0), (16, 30, 16))], "textures": {"0": "hnmt:item/x"}}
        cubes = make_bedrock.block_geometry(tall, "x", (16, 16), slab_height=8)["minecraft:geometry"][0]["bones"][0]["cubes"]
        self.assertEqual(max(c["origin"][1] + c["size"][1] for c in cubes), 16)

    def test_a_rotated_element_is_refused(self):
        rotated = {"elements": [cube((0, 0, 0), (4, 4, 4), rotation={"angle": 45, "axis": "y", "origin": [2, 2, 2]})]}
        with self.assertRaises(ValueError):
            make_bedrock.block_geometry(rotated, "x", (16, 16), slab_height=8)

    def test_a_block_without_a_slab_is_just_the_model(self):
        # まな板は、ハーフブロックを足さない（土台が2段で、モデルがブロック1個ぶんを埋める）。
        model = {"elements": [cube((0, 0, 0), (16, 10, 16)), cube((2, 10, 3), (14, 12, 13))]}
        cubes = make_bedrock.block_geometry(model, "x", (16, 16), slab_height=0)["minecraft:geometry"][0]["bones"][0]["cubes"]
        self.assertEqual(len(cubes), 2)
        self.assertEqual(cubes[0]["size"], [16, 10, 16])
        self.assertEqual(max(c["origin"][1] + c["size"][1] for c in cubes), 12, "低いモデルは縮めない")

    def test_one_java_block_carries_a_state_for_each_block(self):
        mappings = make_bedrock.build_block_mappings(self.TABLE)
        self.assertEqual(mappings["format_version"], 1)
        self.assertEqual(list(mappings["blocks"]), ["minecraft:petrified_oak_slab"])
        definition = mappings["blocks"]["minecraft:petrified_oak_slab"]
        self.assertEqual(definition["name"], "hnmt_petrified_oak_slab")
        self.assertTrue(definition["only_override_states"])
        self.assertFalse(definition["included_in_creative_inventory"])
        overrides = definition["state_overrides"]
        self.assertEqual(set(overrides), {"type=bottom,waterlogged=false", "type=double,waterlogged=false"})
        mill, board = overrides["type=bottom,waterlogged=false"], overrides["type=double,waterlogged=false"]
        self.assertEqual(mill["geometry"], "geometry.hnmt_block_rice_mill")
        self.assertEqual(board["geometry"], "geometry.hnmt_block_board")
        self.assertEqual(mill["material_instances"]["*"]["texture"], "hnmt_rice_mill")
        self.assertEqual(board["material_instances"]["*"]["texture"], "hnmt_board")

    def test_every_state_names_its_own_geometry_and_texture(self):
        # 上の定義（既定）に頼らず、状態ごとに、ジオメトリとテクスチャを書く（状態を足したとき、見た目が混ざらないように）。
        definition = make_bedrock.build_block_mappings(self.TABLE)["blocks"]["minecraft:petrified_oak_slab"]
        for state, override in definition["state_overrides"].items():
            self.assertIn("geometry", override, state)
            self.assertIn("material_instances", override, state)

    def test_the_same_state_twice_is_refused(self):
        table = dict(self.TABLE)
        table["rice/other"] = dict(self.TABLE["rice/mill"])
        with self.assertRaises(ValueError):
            make_bedrock.build_block_mappings(table)

    def test_the_real_table_is_well_formed_and_its_items_exist(self):
        import json
        import os
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bedrock_blocks.json"), encoding="utf-8") as handle:
            table = json.load(handle)
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bedrock_bases.json"), encoding="utf-8") as handle:
            bases = json.load(handle)
        self.assertEqual(table, self.TABLE)
        states = set()
        for item, entry in table.items():
            self.assertNotIn((entry["java_block"], entry["state"]), states, "同じ状態を2つのブロックが使っている")
            states.add((entry["java_block"], entry["state"]))
            self.assertIn(item, bases, "ブロックにする品は、アイテムの表にもある")
            self.assertRegex(entry["java_block"], r"^minecraft:[a-z_]+$")
            self.assertRegex(entry["state"], r"^[a-z_]+=[a-z0-9_]+(,[a-z_]+=[a-z0-9_]+)*$")

    def test_the_pack_gets_the_block_files_and_every_reference_exists(self):
        import json
        import os
        import tempfile
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bedrock_bases.json"), encoding="utf-8") as handle:
            bases = json.load(handle)
        with tempfile.TemporaryDirectory() as out:
            make_bedrock.build_pack(self.ROOT, out, bases, "v0.1.0", blocks=self.TABLE)
            pack = os.path.join(out, "pack")
            with open(os.path.join(pack, "textures", "terrain_texture.json"), encoding="utf-8") as handle:
                terrain = json.load(handle)
            self.assertEqual(terrain["texture_name"], "atlas.terrain")
            with open(os.path.join(out, "custom_mappings", "hnmt_blocks.json"), encoding="utf-8") as handle:
                mappings = json.load(handle)
            overrides = mappings["blocks"]["minecraft:petrified_oak_slab"]["state_overrides"]
            for item, geometry_name in (("rice_mill", "hnmt_block_rice_mill"), ("board", "hnmt_block_board")):
                entry = terrain["texture_data"]["hnmt_" + item]
                self.assertTrue(os.path.exists(os.path.join(pack, entry["textures"] + ".png")), item)
                with open(os.path.join(pack, "models", "blocks", geometry_name + ".geo.json"), encoding="utf-8") as handle:
                    geometry = json.load(handle)
                self.assertEqual(geometry["minecraft:geometry"][0]["description"]["identifier"], "geometry." + geometry_name)
                self.assertIn("geometry." + geometry_name, [o["geometry"] for o in overrides.values()])
                self.assertIn("hnmt_" + item, [o["material_instances"]["*"]["texture"] for o in overrides.values()])

    def test_the_mill_item_is_placed_as_the_block_that_geyser_replaces(self):
        # 見せかけを送る方式は、統合版で壊せなかった（Geyser は、サーバー上の本物のブロックで壊す処理を進めるため）。
        # 石臼のアイテムを置くと、置き換え対象のブロックそのものが置かれるようにそろえる。
        import json
        import os
        here = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(here, "bedrock_bases.json"), encoding="utf-8") as handle:
            bases = json.load(handle)
        for item, entry in self.TABLE.items():
            self.assertEqual(bases[item], entry["java_block"], item)

    def test_java_clients_see_the_replaced_block_as_the_mill_base_and_the_board(self):
        # 石化したオークのハーフブロックは、ふつうはオークの板の見た目なので、Java 版のパックで、下半分はなめらかな石、2段はまな板にする。
        import json
        import os
        path = os.path.join(self.ROOT, "assets", "minecraft", "blockstates", "petrified_oak_slab.json")
        with open(path, encoding="utf-8") as handle:
            variants = json.load(handle)["variants"]
        self.assertEqual({key: value["model"] for key, value in variants.items()}, {
            "type=bottom": "minecraft:block/smooth_stone_slab",       # 石臼の土台
            "type=top": "minecraft:block/smooth_stone_slab_top",
            "type=double": "hnmt:block/board",                         # まな板（台の上にまな板と包丁が乗った形）
        })

    def test_no_two_geometries_in_the_pack_share_an_identifier(self):
        # 石臼は、アイテム（手に持つ）とブロックの両方になる。ジオメトリの名前が同じだと、片方がもう片方を上書きして、手に持った石臼が消える。
        import glob
        import json
        import os
        import tempfile
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bedrock_bases.json"), encoding="utf-8") as handle:
            bases = json.load(handle)
        with tempfile.TemporaryDirectory() as out:
            make_bedrock.build_pack(self.ROOT, out, bases, "v0.1.0", blocks=self.TABLE)
            seen = {}
            for path in glob.glob(os.path.join(out, "pack", "models", "**", "*.geo.json"), recursive=True):
                with open(path, encoding="utf-8") as handle:
                    identifier = json.load(handle)["minecraft:geometry"][0]["description"]["identifier"]
                self.assertNotIn(identifier, seen, "%s と %s が同じ名前" % (path, seen.get(identifier)))
                seen[identifier] = path

    def test_without_blocks_no_block_files_are_made(self):
        import json
        import os
        import tempfile
        with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "bedrock_bases.json"), encoding="utf-8") as handle:
            bases = json.load(handle)
        with tempfile.TemporaryDirectory() as out:
            make_bedrock.build_pack(self.ROOT, out, bases, "v0.1.0")
            self.assertFalse(os.path.exists(os.path.join(out, "custom_mappings", "hnmt_blocks.json")))
            self.assertFalse(os.path.exists(os.path.join(out, "pack", "textures", "terrain_texture.json")))


if __name__ == "__main__":
    unittest.main()


DEFAULT_DISPLAY = {"rotation": [0, 0, 0], "translation": [0, 0, 0], "scale": [1, 1, 1]}


class AnimationTests(unittest.TestCase):
    DISPLAY = {
        "firstperson_righthand": {"rotation": [10, 20, 30], "translation": [1, 2, 3], "scale": [0.5, 0.5, 0.5]},
        "thirdperson_righthand": {"rotation": [10, 20, 30], "translation": [1, 2, 3], "scale": [0.5, 0.5, 0.5]},
        "head": {"rotation": [10, 20, 30], "translation": [1, 2, 3], "scale": [2, 2, 2]},
    }

    def bones(self, display):
        return make_bedrock.display_to_animations(display, "hnmt_fish_tai")["animations"]

    def test_the_first_person_view_swaps_the_axes_and_lifts_the_position(self):
        bone = self.bones(self.DISPLAY)["animation.hnmt_fish_tai.hold_first_person"]["bones"]["model"]
        self.assertEqual(bone["rotation"], [-20, 30, 10])
        self.assertEqual(bone["position"], [-2, 15.5, 1])
        self.assertEqual(bone["scale"], [0.5, 0.5, 0.5])

    def test_the_third_person_view_has_its_own_base_rotation(self):
        bone = self.bones(self.DISPLAY)["animation.hnmt_fish_tai.hold_third_person"]["bones"]["model"]
        self.assertEqual(bone["rotation"], [90, -30, -20])
        self.assertEqual(bone["position"], [-1, 15.5, -2])
        self.assertEqual(bone["scale"], [0.5, 0.5, 0.5])

    def test_the_head_view_is_scaled_down_and_lifted(self):
        bone = self.bones(self.DISPLAY)["animation.hnmt_fish_tai.head"]["bones"]["model"]
        self.assertEqual(bone["rotation"], [-10, -20, 30])
        self.assertEqual(bone["position"], [-0.655, 21.31, 1.965])
        self.assertEqual(bone["scale"], [1.31, 1.31, 1.31])

    def test_a_missing_display_uses_the_java_defaults(self):
        bones = self.bones({})
        first = bones["animation.hnmt_fish_tai.hold_first_person"]["bones"]["model"]
        self.assertEqual(first["rotation"], [0, 0, 0])
        self.assertEqual(first["position"], [0, 12.5, 0])
        self.assertEqual(first["scale"], [1, 1, 1])

    def test_all_three_animations_loop(self):
        for animation in self.bones(self.DISPLAY).values():
            self.assertIs(animation["loop"], True)


class AttachableTests(unittest.TestCase):
    def test_the_attachable_names_the_geometry_texture_and_animations(self):
        doc = make_bedrock.build_attachable("hnmt:fish_tai", "hnmt_fish_tai", "textures/entity/hnmt/fish_tai")
        description = doc["minecraft:attachable"]["description"]
        self.assertEqual(description["identifier"], "hnmt:fish_tai")
        self.assertEqual(description["geometry"], {"default": "geometry.hnmt_fish_tai"})
        self.assertEqual(description["textures"]["default"], "textures/entity/hnmt/fish_tai")
        self.assertEqual(set(description["animations"]), {"first_person", "third_person", "head"})
        self.assertEqual(description["animations"]["head"], "animation.hnmt_fish_tai.head")
        self.assertEqual(description["render_controllers"], ["controller.render.item_default"])

    def test_each_view_plays_only_in_its_own_slot(self):
        doc = make_bedrock.build_attachable("hnmt:fish_tai", "hnmt_fish_tai", "t")
        animate = doc["minecraft:attachable"]["description"]["scripts"]["animate"]
        self.assertEqual([list(entry)[0] for entry in animate], ["first_person", "third_person", "head"])
        self.assertIn("context.is_first_person == 1.0", animate[0]["first_person"])
        self.assertIn("context.is_first_person == 0.0", animate[1]["third_person"])
        self.assertIn("context.item_slot == 'head'", animate[2]["head"])

    def test_the_geometry_bone_follows_the_item_slot(self):
        doc = make_bedrock.model_to_geometry(GeometryTests.MODEL, "x", texture_px=(32, 32))
        bone = doc["minecraft:geometry"][0]["bones"][0]
        self.assertEqual(bone["binding"], "q.item_slot_to_bone_name(context.item_slot)")


class ManifestTests(unittest.TestCase):
    def test_the_manifest_carries_the_version_from_the_tag(self):
        doc = make_bedrock.build_manifest("v1.2.3")
        self.assertEqual(doc["header"]["version"], [1, 2, 3])
        self.assertEqual(doc["modules"][0]["version"], [1, 2, 3])
        self.assertEqual(doc["format_version"], 2)

    def test_the_uuids_do_not_change_between_builds(self):
        a = make_bedrock.build_manifest("v0.1.0")
        b = make_bedrock.build_manifest("v0.2.0")
        self.assertEqual(a["header"]["uuid"], b["header"]["uuid"])
        self.assertNotEqual(a["header"]["uuid"], a["modules"][0]["uuid"])

    def test_a_tag_that_is_not_a_version_is_refused(self):
        with self.assertRaises(ValueError):
            make_bedrock.build_manifest("main")


class MappingTests(unittest.TestCase):
    def test_the_mapping_binds_the_java_model_to_the_bedrock_item(self):
        doc = make_bedrock.build_mappings({"fish/tai": "minecraft:tropical_fish"})
        self.assertEqual(doc["format_version"], 2)
        entry = doc["items"]["minecraft:tropical_fish"][0]
        self.assertEqual(entry["type"], "definition")
        self.assertEqual(entry["model"], "hnmt:fish/tai")
        self.assertEqual(entry["bedrock_identifier"], "hnmt:fish_tai")
        self.assertEqual(entry["bedrock_options"]["icon"], "hnmt.fish_tai")

    def test_items_with_the_same_base_share_one_list(self):
        doc = make_bedrock.build_mappings({"fish/tai": "minecraft:cod", "fish/saba": "minecraft:cod"})
        self.assertEqual(len(doc["items"]["minecraft:cod"]), 2)

    def test_the_item_atlas_lists_every_icon(self):
        doc = make_bedrock.build_item_atlas(["fish/tai"])
        self.assertEqual(doc["texture_data"]["hnmt.fish_tai"], {"textures": ["textures/items/hnmt/fish_tai"]})
        self.assertEqual(doc["texture_name"], "atlas.items")


class FlatItemTests(unittest.TestCase):
    def test_a_flat_item_has_a_plain_definition_that_holds_like_a_tool(self):
        doc = make_bedrock.build_mappings({"rod/bamboo": "minecraft:fishing_rod"}, flat={"rod/bamboo"})
        plain = [d for d in doc["items"]["minecraft:fishing_rod"] if "predicate" not in d]
        self.assertEqual(len(plain), 1)
        self.assertEqual(plain[0]["model"], "hnmt:rod/bamboo")
        self.assertEqual(plain[0]["bedrock_identifier"], "hnmt:rod_bamboo")
        self.assertIs(plain[0]["bedrock_options"]["display_handheld"], True)

    def test_a_cast_state_is_a_separate_definition_with_the_cast_predicate_listed_first(self):
        doc = make_bedrock.build_mappings({"rod/bamboo": "minecraft:fishing_rod"}, flat={"rod/bamboo"}, cast={"rod/bamboo"})
        definitions = doc["items"]["minecraft:fishing_rod"]
        self.assertEqual(len(definitions), 2)
        self.assertEqual(definitions[0]["predicate"], {"type": "condition", "property": "fishing_rod_cast"})
        self.assertEqual(definitions[0]["bedrock_identifier"], "hnmt:rod_bamboo_cast")
        self.assertEqual(definitions[0]["bedrock_options"]["icon"], "hnmt.rod_bamboo_cast")
        self.assertEqual(definitions[0]["model"], "hnmt:rod/bamboo")
        self.assertNotIn("predicate", definitions[1])

    def test_a_three_d_item_is_not_held_like_a_tool(self):
        doc = make_bedrock.build_mappings({"fish/tai": "minecraft:tropical_fish"})
        self.assertIs(doc["items"]["minecraft:tropical_fish"][0]["bedrock_options"]["display_handheld"], False)

    def test_the_atlas_lists_the_cast_icon_too(self):
        doc = make_bedrock.build_item_atlas(["rod/bamboo", "fish/tai"], cast={"rod/bamboo"})
        self.assertEqual(set(doc["texture_data"]), {"hnmt.rod_bamboo", "hnmt.rod_bamboo_cast", "hnmt.fish_tai"})
        self.assertEqual(doc["texture_data"]["hnmt.rod_bamboo_cast"], {"textures": ["textures/items/hnmt/rod_bamboo_cast"]})

    def test_building_a_rod_writes_both_icons_and_no_geometry(self):
        import os
        import tempfile
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        with tempfile.TemporaryDirectory() as out:
            make_bedrock.build_pack(root, out, {"rod/bamboo": "minecraft:fishing_rod"}, "v0.1.0")
            pack = os.path.join(out, "pack")
            self.assertTrue(os.path.exists(os.path.join(pack, "textures/items/hnmt/rod_bamboo.png")))
            self.assertTrue(os.path.exists(os.path.join(pack, "textures/items/hnmt/rod_bamboo_cast.png")))
            self.assertFalse(os.path.exists(os.path.join(pack, "attachables/hnmt_rod_bamboo.json")))
            self.assertFalse(os.path.exists(os.path.join(pack, "models/entity/hnmt_rod_bamboo.geo.json")))


class IdentifierTests(unittest.TestCase):
    def test_slashes_become_underscores(self):
        self.assertEqual(make_bedrock.safe_name("dish/sashimi_tai"), "dish_sashimi_tai")
        self.assertEqual(make_bedrock.safe_name("rice"), "rice")


class BuildTests(unittest.TestCase):
    def test_building_tai_writes_a_complete_pack(self):
        import json
        import os
        import tempfile
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        with tempfile.TemporaryDirectory() as out:
            make_bedrock.build_pack(root, out, {"fish/tai": "minecraft:tropical_fish"}, "v0.1.0")
            expected = [
                "pack/manifest.json",
                "pack/textures/item_texture.json",
                "pack/textures/items/hnmt/fish_tai.png",
                "pack/textures/entity/hnmt/fish_tai.png",
                "pack/models/entity/hnmt_fish_tai.geo.json",
                "pack/attachables/hnmt_fish_tai.json",
                "pack/animations/hnmt_fish_tai.animation.json",
                "custom_mappings/hnmt.json",
            ]
            for path in expected:
                self.assertTrue(os.path.exists(os.path.join(out, path)), path)
            with open(os.path.join(out, "pack/textures/item_texture.json"), encoding="utf-8") as handle:
                atlas = json.load(handle)
            for entry in atlas["texture_data"].values():
                for texture in entry["textures"]:
                    self.assertTrue(os.path.exists(os.path.join(out, "pack", texture + ".png")), texture)

    def test_the_pack_is_zipped_with_the_manifest_at_the_top(self):
        import os
        import tempfile
        import zipfile
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        with tempfile.TemporaryDirectory() as out:
            make_bedrock.build_pack(root, out, {"fish/tai": "minecraft:tropical_fish"}, "v0.1.0")
            target = make_bedrock.zip_pack(out)
            with zipfile.ZipFile(target) as archive:
                names = archive.namelist()
            self.assertIn("manifest.json", names)
            self.assertIn("attachables/hnmt_fish_tai.json", names)

    def test_an_item_without_a_model_is_refused(self):
        import os
        import tempfile
        root = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
        with tempfile.TemporaryDirectory() as out:
            with self.assertRaises(FileNotFoundError):
                make_bedrock.build_pack(root, out, {"fish/not_a_fish": "minecraft:cod"}, "v0.1.0")
