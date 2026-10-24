"""町のメニュー用アイコンの契約を検査する（名前の一覧・3つのファイル・16px・二値の透明）。"""
import json
import unittest
from PIL import Image
from artwork import PACK
from make_menu_icons import ICONS, draw


class MenuIconTests(unittest.TestCase):
    def test_names_are_unique_and_match_the_published_list(self):
        self.assertEqual(len(ICONS), len(set(ICONS)))
        self.assertEqual(json.loads((PACK / 'tools/menu_icons.json').read_text()), ICONS)

    def test_every_icon_has_texture_model_and_item_definition(self):
        for name in ICONS:
            self.assertTrue((PACK / f'assets/hnmt/textures/item/menu/{name}.png').is_file(), name)
            model = json.loads((PACK / f'assets/hnmt/models/item/menu/{name}.json').read_text())
            self.assertEqual(model['textures']['layer0'], f'hnmt:item/menu/{name}')
            definition = json.loads((PACK / f'assets/hnmt/items/menu/{name}.json').read_text())
            self.assertEqual(definition['model'], {'type': 'minecraft:model', 'model': f'hnmt:item/menu/{name}'})

    def test_textures_are_16px_rgba_with_crisp_transparency(self):
        for name in ICONS:
            with Image.open(PACK / f'assets/hnmt/textures/item/menu/{name}.png') as image:
                self.assertEqual(image.size, (16, 16), name)
                self.assertEqual(image.mode, 'RGBA', name)
                self.assertLessEqual(set(image.getchannel('A').get_flattened_data()), {0, 255}, name)

    def test_blank_is_fully_transparent_and_the_others_are_not(self):
        for name in ICONS:
            with Image.open(PACK / f'assets/hnmt/textures/item/menu/{name}.png') as image:
                opaque = sum(1 for a in image.getchannel('A').get_flattened_data() if a)
                if name == 'blank':
                    self.assertEqual(opaque, 0)
                else:
                    self.assertGreater(opaque, 25, name)
                    self.assertLess(opaque, 250, name)

    def test_icons_are_visually_distinct(self):
        seen = {}
        for name in ICONS:
            if name == 'blank': continue
            data = draw(name).tobytes()
            self.assertNotIn(data, seen, f'{name} は {seen.get(data)} と同じ絵')
            seen[data] = name

    def test_committed_textures_match_what_the_script_draws(self):
        for name in ICONS:
            with Image.open(PACK / f'assets/hnmt/textures/item/menu/{name}.png') as image:
                self.assertEqual(image.tobytes(), draw(name).tobytes(), name)


if __name__ == '__main__':
    unittest.main()
