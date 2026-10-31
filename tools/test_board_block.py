"""まな板のブロックの見た目（台の上にまな板と包丁が乗った形）の、Java 版の資源を検査する。"""
import json
import unittest
from PIL import Image
from artwork import PACK
from make_board_block import geometry
from make_bedrock import block_geometry


class BoardBlockTests(unittest.TestCase):
    def model(self):
        return json.loads((PACK / 'assets/hnmt/models/block/board.json').read_text())

    def test_texture_is_a_16px_opaque_atlas(self):
        with Image.open(PACK / 'assets/hnmt/textures/block/board.png') as image:
            self.assertEqual(image.size, (16, 16))
            self.assertEqual(image.mode, 'RGBA')
            self.assertEqual(set(image.getchannel('A').get_flattened_data()), {255}, 'ブロックの面に使う絵は、透けない')
            self.assertLessEqual(len(set(image.get_flattened_data())), 24)

    def test_the_model_uses_one_texture_and_keeps_a_small_top_detail(self):
        model = self.model()
        self.assertEqual(set(model['textures'].values()), {'hnmt:block/board'})
        self.assertGreaterEqual(len(model['elements']), 5)
        self.assertLessEqual(len(model['elements']), 12)
        for part in model['elements']:
            self.assertNotIn('rotation', part, '統合版のブロックにできない')
            for axis, (a, b) in enumerate(zip(part['from'], part['to'])):
                self.assertTrue(0 <= a < b <= (19 if axis == 1 else 16), part)
            for face in part['faces'].values():
                u0, v0, u1, v1 = face['uv']
                self.assertTrue(0 <= u0 < u1 <= 16 and 0 <= v0 < v1 <= 16, part)

    def test_the_parts_are_a_counter_a_board_and_a_knife(self):
        names = {part['name'] for part in self.model()['elements']}
        self.assertTrue({'Counter', 'Top', 'Board', 'Blade', 'Handle'} <= names, names)

    def test_the_board_stands_on_the_counter_and_the_knife_lies_on_the_board(self):
        parts = {part['name']: part for part in self.model()['elements']}
        self.assertEqual(parts['Counter']['from'][1], 0)
        self.assertEqual(parts['Top']['from'][1], parts['Counter']['to'][1])
        self.assertEqual(parts['Board']['from'][1], parts['Top']['to'][1])
        self.assertGreaterEqual(parts['Blade']['from'][1], parts['Board']['from'][1])
        self.assertGreaterEqual(parts['Handle']['from'][1], parts['Board']['from'][1])
        top = max(part['to'][1] for part in parts.values())
        self.assertLessEqual(top, 19)

    def test_counter_fills_the_opaque_block_in_all_outputs(self):
        native = json.loads((PACK / 'blockbench/board/board.bbmodel').read_text())
        for elements in (self.model()['elements'], geometry(), native['elements']):
            parts = {p['name']: p for p in elements}
            self.assertEqual(parts['Counter']['from'], [0, 0, 0])
            self.assertEqual(parts['Counter']['to'], [16, 14, 16])
            self.assertEqual(parts['Top']['from'], [0, 14, 0])
            self.assertEqual(parts['Top']['to'], [16, 16, 16])
            self.assertEqual(parts['Board']['from'][1], 16)

    def test_bedrock_keeps_the_full_height_counter(self):
        cubes = block_geometry(self.model(), 'board', (16, 16), 0)['minecraft:geometry'][0]['bones'][0]['cubes']
        self.assertEqual(cubes[0]['size'], [16, 14, 16])
        self.assertEqual(cubes[1]['origin'][1], 14)
        self.assertEqual(cubes[1]['size'], [16, 2, 16])

    def test_every_face_samples_the_texture_inside_its_bounds(self):
        with Image.open(PACK / 'assets/hnmt/textures/block/board.png') as image:
            self.assertEqual(image.size, (16, 16))
        for part in self.model()['elements']:
            self.assertEqual(set(part['faces']), {'north', 'south', 'east', 'west', 'up', 'down'})


if __name__ == '__main__':
    unittest.main()
