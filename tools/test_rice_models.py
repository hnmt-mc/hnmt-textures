"""米作りの配置、Blockbench編集元、16pxテクスチャの契約を検査する。"""
import base64
import json
import unittest
from PIL import Image
from artwork import PACK
from make_models import inventory
from make_rice_models import RICE, geometry, texture


class RiceModelTests(unittest.TestCase):
    def model(self, name):
        return json.loads((PACK/'models3d/rice'/f'{name}.json').read_text())

    def test_six_ids_are_added_without_replacing_cooked_rice(self):
        entries = list(inventory())
        self.assertEqual(len(entries), 71)
        self.assertEqual({name for group, name, _ in entries if group == 'rice'}, set(dict(RICE)))
        self.assertIn(('', 'rice', '米'), entries)
        cooked = json.loads((PACK/'assets/hnmt/items/rice.json').read_text())
        self.assertEqual(cooked['model']['model'], 'hnmt:item/rice')
        for name, _ in RICE:
            definition = json.loads((PACK/'assets/hnmt/items/rice'/f'{name}.json').read_text())
            self.assertEqual(definition['model'], {'type': 'minecraft:model', 'model': f'hnmt:item/rice/{name}'})

    def test_textures_are_16px_rgba_and_distinct(self):
        signatures = set()
        for name, _ in RICE:
            with Image.open(PACK/'assets/hnmt/textures/item/rice'/f'{name}.png') as image:
                self.assertEqual(image.size, (16, 16))
                self.assertEqual(image.mode, 'RGBA')
                alpha = set(image.getchannel('A').get_flattened_data())
                self.assertEqual(alpha, {255} if name == 'mill' else {0, 255})   # 石臼は、領域を並べた不透明の絵
                self.assertLessEqual(len(set(image.get_flattened_data())), 16)
                self.assertEqual(image.tobytes(), texture(name).tobytes())
                signatures.add(image.tobytes())
        self.assertEqual(len(signatures), 6)

    def test_native_projects_embed_exported_texture_and_named_groups(self):
        for name, _ in RICE:
            with self.subTest(name=name):
                project = json.loads((PACK/'blockbench/rice'/f'{name}.bbmodel').read_text())
                self.assertEqual(project['meta']['model_format'], 'java_block')
                self.assertEqual(project['resolution'], {'width': 16, 'height': 16})
                self.assertEqual(len(project['textures']), 1)
                data = project['textures'][0]['source'].split(',', 1)[1]
                self.assertEqual(base64.b64decode(data), (PACK/'assets/hnmt/textures/item/rice'/f'{name}.png').read_bytes())
                self.assertEqual(len(project['elements']), len(self.model(name)['elements']))
                groups = {group['name'] for group in project['groups']}
                expected = {'Base', 'Top', 'Handle'} if name == 'mill' else {'Plant'} if name.startswith('plant_') else {'Sprite'}
                self.assertEqual(groups, expected)

    def test_export_matches_source_geometry(self):
        for name, _ in RICE:
            model = self.model(name)
            self.assertEqual(set(model['textures'].values()), {f'hnmt:item/rice/{name}'})
            source = {part['name']: part for part in geometry(name)}
            self.assertEqual({part['name'] for part in model['elements']}, set(source))
            for part in model['elements']:
                expected = source[part['name']]
                for key in ('from', 'to', 'faces'): self.assertEqual(part[key], expected[key])
                if 'rotation' in expected:
                    self.assertEqual(part['rotation']['axis'], expected['rotation']['axis'])
                    self.assertEqual(part['rotation']['angle'], expected['rotation']['angle'])
                    self.assertEqual(part['rotation']['origin'], expected['rotation']['origin'])

    def test_cuboid_budget_stays_small(self):
        # 田んぼには何十本も並ぶので、重くしない（前の版は、実りで158個だった）。
        for name, _ in RICE:
            self.assertLessEqual(len(self.model(name)['elements']), 4)

    def test_uvs_only_sample_opaque_pixels(self):
        for name, _ in RICE:
            with Image.open(PACK/'assets/hnmt/textures/item/rice'/f'{name}.png') as image:
                for part in self.model(name)['elements']:
                    if part['name'].startswith(('Plant', 'Sprite')): continue   # 絵の透明な所は、板の抜けとして使う
                    for face in part['faces'].values():
                        u0, v0, u1, v1 = face['uv']
                        for y in range(int(v0), int(v1)):
                            for x in range(int(u0), int(u1)):
                                self.assertEqual(image.getpixel((x, y))[3], 255, (name, part['name']))

    def test_plants_are_crossed_planes_at_the_farmland_surface(self):
        for name in ('plant_seedling', 'plant_growing', 'plant_mature'):
            model = self.model(name)
            planes = model['elements']
            self.assertEqual(sorted(part['rotation']['angle'] for part in planes), [-45, 45])
            for part in planes:
                self.assertEqual(part['from'][1], -1)     # 耕地の面は実際には 1/16 低いので、足元を1下まで伸ばす
                self.assertEqual(part['from'][2], part['to'][2])   # 厚みのない板
                self.assertEqual(set(part['faces']), {'north', 'south'})
            fixed = model['display'].get('fixed', {})   # すべて初期値なら、Blockbench は書き出さない
            self.assertEqual(fixed.get('rotation', [0, 0, 0]), [0, 0, 0])
            self.assertEqual(fixed.get('translation', [0, 0, 0]), [0, 0, 0])
            self.assertEqual(fixed.get('scale', [1, 1, 1]), [1, 1, 1])

    def test_mill_sits_on_the_slab_and_stacks_upward(self):
        mill = {part['name']: part for part in self.model('mill')['elements']}
        self.assertEqual(mill['Base']['from'][1], 0)
        self.assertEqual(mill['Top']['from'][1], mill['Base']['to'][1])
        self.assertGreaterEqual(mill['Hopper']['from'][1], mill['Top']['to'][1])
        fixed = self.model('mill')['display'].get('fixed', {})
        self.assertEqual((fixed.get('rotation', [0, 0, 0]), fixed.get('translation', [0, 0, 0]), fixed.get('scale', [1, 1, 1])), ([0, 0, 0], [0, 0, 0], [1, 1, 1]))

    def test_unknown_ids_are_rejected(self):
        with self.assertRaises(ValueError): texture('../rice')
        with self.assertRaises(ValueError): geometry('unknown')


if __name__ == '__main__': unittest.main()
