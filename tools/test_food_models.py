"""料理の器の空洞・32px UV・Java版の回転制限・編集元を検査する。"""
import base64
import hashlib
import itertools
import json
import math
import unittest
from PIL import Image
from artwork import PACK, DISHES
from make_food_models import geometry, TILES


class FoodModelTests(unittest.TestCase):
    def test_all_32_dishes_have_distinct_embedded_blockbench_projects(self):
        self.assertEqual(len(DISHES), 32)
        for name, _ in DISHES:
            with self.subTest(name=name):
                project = json.loads((PACK / 'blockbench/dish' / (name + '.bbmodel')).read_text())
                self.assertEqual(project['meta']['model_format'], 'java_block')
                self.assertEqual(project['resolution'], {'width': 32, 'height': 32})
                self.assertEqual(len(project['textures']), 1)
                source = project['textures'][0]['source']
                self.assertTrue(source.startswith('data:image/png;base64,'))
                self.assertEqual(base64.b64decode(source.split(',', 1)[1]), (PACK / 'assets/hnmt/textures/item/dish3d' / (name + '.png')).read_bytes())
                self.assertEqual(len(project['elements']), len(geometry(name)))
                self.assertTrue({'Vessel', 'Food'} <= {g['name'] for g in project['groups']})

    def test_all_rotated_corners_stay_in_one_block(self):
        for name, _ in DISHES:
            for part in geometry(name):
                self.assertTrue(all(0 <= a < b <= 16 for a, b in zip(part['from'], part['to'])))
                rotation = part.get('rotation', {'angle': 0, 'origin': [0, 0, 0]})
                angle = math.radians(rotation['angle'])
                ox, oy, oz = rotation['origin']
                for x, y, z in itertools.product(*zip(part['from'], part['to'])):
                    px = ox + (x - ox) * math.cos(angle) + (z - oz) * math.sin(angle)
                    pz = oz - (x - ox) * math.sin(angle) + (z - oz) * math.cos(angle)
                    self.assertTrue(0 <= px <= 16 and 0 <= y <= 16 and 0 <= pz <= 16, (name, part['name']))

    def test_bowls_have_open_rims_and_connected_wall_tiers(self):
        for name in ('don_maguro', 'don_salmon', 'don_tai', 'don_unagi', 'don_ikura', 'soup_tai'):
            vessel = [p for p in geometry(name) if p['name'].startswith('vessel_')]
            self.assertEqual(sum('_lip_' in p['name'] for p in vessel), 8)
            for part in vessel:
                if part['from'][1] > 2:
                    self.assertFalse(part['from'][0] < 8 < part['to'][0] and part['from'][2] < 8 < part['to'][2], part['name'])
            rings = [next(p for p in vessel if p['name'] == f'vessel_wall{i}_z1') for i in range(4)]
            for lower, upper in zip(rings, rings[1:]):
                self.assertGreaterEqual(lower['to'][1], upper['from'][1])
                self.assertGreaterEqual(lower['to'][2], upper['from'][2])

    def test_uv_atlas_and_element_budget(self):
        for box in TILES.values():
            self.assertTrue(0 <= box[0] < box[2] <= 32 and 0 <= box[1] < box[3] <= 32)
        for name, _ in DISHES:
            parts = geometry(name)
            self.assertLessEqual(len(parts), 150)
            for part in parts:
                for face in part['faces'].values():
                    u0, v0, u1, v1 = face['uv']
                    self.assertTrue(0 <= u0 < u1 <= 16 and 0 <= v0 < v1 <= 16)

    def test_native_exports_retain_all_geometry_and_texture_references(self):
        for name, _ in DISHES:
            model = json.loads((PACK / 'models3d/dish' / (name + '.json')).read_text())
            self.assertEqual(len(model['elements']), len(geometry(name)))
            self.assertEqual(set(model['textures'].values()), {'hnmt:item/dish3d/' + name})
            for mode in ('gui', 'ground', 'fixed', 'firstperson_righthand', 'thirdperson_righthand'):
                self.assertIn(mode, model['display'])
            source = {p['name']: p for p in geometry(name)}
            self.assertEqual({p['name'] for p in model['elements']}, set(source))
            for actual in model['elements']:
                expected = source[actual['name']]
                self.assertEqual(actual['from'], expected['from'])
                self.assertEqual(actual['to'], expected['to'])
                if 'rotation' in expected:
                    for key in ('angle', 'axis', 'origin'):
                        self.assertEqual(actual['rotation'][key], expected['rotation'][key])
                for direction, face in expected['faces'].items():
                    self.assertEqual(actual['faces'][direction]['uv'], face['uv'])

    def test_roe_is_a_dense_three_dimensional_topping(self):
        roe = [p for p in geometry('don_ikura') if p['name'].startswith('food_roe')]
        self.assertGreaterEqual(len(roe), 60)
        self.assertTrue(all(p['to'][1] > p['from'][1] for p in roe))

    def test_all_3d_textures_are_32px_and_food_materials_vary(self):
        digests = set()
        for name, _ in DISHES:
            path = PACK / 'assets/hnmt/textures/item/dish3d' / (name + '.png')
            with Image.open(path) as image:
                self.assertEqual(image.size, (32, 32))
                self.assertEqual(image.mode, 'RGBA')
                digests.add(hashlib.sha256(image.tobytes()).digest())
        self.assertGreaterEqual(len(digests), 12)


if __name__ == '__main__':
    unittest.main()
