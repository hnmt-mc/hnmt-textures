import io
import json
import unittest
import zipfile
from pathlib import Path

import make_manifest

ROOT = Path(__file__).resolve().parents[1]
FONT_IMAGES = ('gun_flash', 'gun_scope', 'gun_ember', 'gun_smoke')


def packed(drop=None, empty=None):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as z:
        files = [ROOT / 'assets/hnmt/sounds.json', ROOT / 'assets/hnmt/font/gun.json',
                 *sorted((ROOT / 'assets/hnmt/textures/font').glob('gun_*.png')), ROOT / 'assets/hnmt/textures/misc/gun_scope.png', *sorted((ROOT / 'assets/hnmt/sounds/gun').glob('*.ogg'))]
        for path in files:
            name = str(path.relative_to(ROOT))
            if name == drop: continue
            z.writestr(name, b'' if name == empty else path.read_bytes())
    return out.getvalue()


class GunAssetTests(unittest.TestCase):
    def test_every_gun_event_points_at_an_existing_ogg(self):
        events = json.loads((ROOT / 'assets/hnmt/sounds.json').read_text())
        for event in make_manifest.GUN_SOUNDS:
            self.assertTrue(events[event]['sounds'], event)
            for entry in events[event]['sounds']:
                namespace, name = entry['name'].split(':')
                self.assertEqual(namespace, 'hnmt')
                self.assertTrue(name.startswith('gun/'), entry['name'])
                self.assertTrue((ROOT / 'assets/hnmt/sounds' / (name + '.ogg')).stat().st_size > 0, entry['name'])

    def test_the_gun_oggs_are_vorbis(self):
        for path in (ROOT / 'assets/hnmt/sounds/gun').glob('*.ogg'):
            data = path.read_bytes()
            self.assertEqual(data[:4], b'OggS', path.name)
            self.assertIn(b'vorbis', data[:200], path.name)

    def test_the_sound_capability_needs_every_gun_sound(self):
        self.assertIn('gun-sounds-v1', make_manifest.manifest('v0.11.0', packed())['capabilities'])
        self.assertNotIn('gun-sounds-v1', make_manifest.manifest('v0.11.0', packed(drop='assets/hnmt/sounds/gun/fire.ogg'))['capabilities'])
        self.assertNotIn('gun-sounds-v1', make_manifest.manifest('v0.11.0', packed(empty='assets/hnmt/sounds/gun/misfire.ogg'))['capabilities'])
        self.assertNotIn('gun-sounds-v1', make_manifest.manifest('v0.11.0', b'not a zip')['capabilities'])

    def test_the_screen_capability_needs_the_font_and_all_images(self):
        self.assertIn('gun-screen-v1', make_manifest.manifest('v0.11.0', packed())['capabilities'])
        self.assertNotIn('gun-screen-v1', make_manifest.manifest('v0.11.0', packed(drop='assets/hnmt/font/gun.json'))['capabilities'])
        for name in FONT_IMAGES:
            missing = 'assets/hnmt/textures/font/%s.png' % name
            self.assertNotIn('gun-screen-v1', make_manifest.manifest('v0.11.0', packed(drop=missing))['capabilities'], missing)
        self.assertNotIn('gun-screen-v1', make_manifest.manifest('v0.11.0', packed(empty='assets/hnmt/textures/font/gun_scope.png'))['capabilities'])

    def test_the_font_maps_the_characters_the_server_sends(self):
        providers = json.loads((ROOT / 'assets/hnmt/font/gun.json').read_text())['providers']
        self.assertEqual({p['file']: p['chars'] for p in providers}, {
            'hnmt:font/gun_flash.png': [''], 'hnmt:font/gun_scope.png': [''],
            'hnmt:font/gun_ember.png': [''], 'hnmt:font/gun_smoke.png': ['']})
        for p in providers: self.assertLessEqual(p['ascent'], p['height'])

    def test_the_screen_images_are_transparent_and_the_expected_size(self):
        from PIL import Image
        for name in FONT_IMAGES:
            image = Image.open(ROOT / 'assets/hnmt/textures/font' / (name + '.png'))
            self.assertEqual((image.size, image.mode), ((512, 256), 'RGBA'), name)
        scope = Image.open(ROOT / 'assets/hnmt/textures/font/gun_scope.png')
        self.assertEqual(scope.getpixel((20, 20))[3], 0, '照準: 画面の縁は、透明（画面を覆わない）')
        self.assertEqual(scope.getpixel((256 + 70, 128 - 90))[3], 0, '照準: 十字線の外側は、透明')
        self.assertTrue(scope.getpixel((256 + 20, 128))[3] > 200, '照準: 十字線がある')
        opaque = sum(1 for p in scope.getdata() if p[3] > 0)
        self.assertLess(opaque / (512 * 256), 0.08, '照準が覆う面積は、画面の8%より小さい')

    def test_the_aim_view_is_a_barrel_with_a_front_sight_in_the_rear_sight_notch(self):
        from PIL import Image
        view = Image.open(ROOT / 'assets/hnmt/textures/misc/gun_scope.png')
        self.assertEqual((view.size, view.mode), ((1024, 576), 'RGBA'))
        for corner in ((2, 2), (1021, 2), (2, 300), (1021, 300), (200, 300), (800, 200)):
            self.assertEqual(view.getpixel(corner)[3], 0, '周りは、透明（景色が見える）')
        self.assertEqual(view.getpixel((512, 200))[3], 0, '照星より上は、透明')
        self.assertEqual(view.getpixel((512, 300 - 22))[3], 255, '照星（柱）が、画面の中央にある')
        self.assertEqual(view.getpixel((512, 560))[3], 255, '照門の U 字の切れ込みの中に、銃身が見える')
        self.assertEqual(view.getpixel((512 - 100, 500))[3], 255, '照門の板がある')
        self.assertEqual(view.getpixel((512 - 100, 560))[3], 255, '照門の板は、下まで続く')
        self.assertEqual(view.getpixel((512 - 300, 570))[3], 255, '銃床の上面（木）が、手前の左右にある')
        glow = view.getpixel((512 + 288, 314))
        self.assertGreater(glow[0] + glow[1], 400, '火縄の先は、明るく燃えている')
        self.assertGreater(view.getpixel((512 + 300, 540))[3], 200, '右手前に、真鍮の側板がある')
        notch = view.getpixel((512, 490))
        self.assertGreater(notch[0] + notch[1] + notch[2], 250, 'U 字の切れ込みから、明るい銃身の上面が見える（照門の板は、暗い）')
        self.assertLess(sum(view.getpixel((512 - 100, 500))[:3]), 150, '照門の板は、暗い')
        opaque = sum(1 for p in view.getdata() if p[3] > 200)
        self.assertLess(opaque / (1024 * 576), 0.30, '視界の大半は、覆わない（上半分は、景色）')
        # 照星は、切れ込みの真ん中（左右の中央）にある
        columns = [x for x in range(1024) if view.getpixel((x, 300 - 22))[3] == 255]
        self.assertAlmostEqual((columns[0] + columns[-1]) / 2, 512, delta=1)

    def test_the_scope_view_capability_needs_the_picture(self):
        self.assertIn('gun-scope-v1', make_manifest.manifest('v0.11.2', packed())['capabilities'])
        self.assertNotIn('gun-scope-v1', make_manifest.manifest('v0.11.2', packed(drop='assets/hnmt/textures/misc/gun_scope.png'))['capabilities'])
        self.assertNotIn('gun-scope-v1', make_manifest.manifest('v0.11.2', packed(empty='assets/hnmt/textures/misc/gun_scope.png'))['capabilities'])

    def test_a_loaded_gun_hides_the_held_model_while_use_is_held(self):
        for gun in ('matchlock', 'tanzutsu'):
            item = json.loads((ROOT / ('assets/hnmt/items/gun/%s_loaded.json' % gun)).read_text())['model']
            self.assertEqual((item['type'], item['property'], item['keybind']), ('minecraft:condition', 'minecraft:keybind_down', 'key.use'))
            self.assertEqual(item['on_true']['model'], 'hnmt:item/gun/%s_aim' % gun)
            aim = json.loads((ROOT / ('assets/hnmt/models/item/gun/%s_aim.json' % gun)).read_text())
            self.assertEqual(aim['display']['firstperson_righthand']['scale'], [0.001] * 3, '狙っている間は、手に持った銃を隠す')
            self.assertEqual(aim['elements'], json.loads((ROOT / ('assets/hnmt/models/item/gun/%s_loaded.json' % gun)).read_text())['elements'])
        for gun in ('matchlock', 'tanzutsu'):
            plain = json.loads((ROOT / ('assets/hnmt/items/gun/%s.json' % gun)).read_text())['model']
            self.assertEqual(plain['type'], 'minecraft:select', '空の銃は、構えの切り替えを持たない（display_context だけ）')

    def test_a_gun_shows_the_flat_icon_in_menus_and_the_3d_model_in_hand(self):
        for name in ('matchlock', 'matchlock_loaded', 'tanzutsu', 'tanzutsu_loaded'):
            item = json.loads((ROOT / ('assets/hnmt/items/gun/%s.json' % name)).read_text())['model']
            held = item['on_false'] if item['type'] == 'minecraft:condition' else item
            self.assertEqual((held['type'], held['property']), ('minecraft:select', 'minecraft:display_context'))
            self.assertEqual(held['cases'][0]['when'], ['gui', 'ground', 'fixed'])
            self.assertEqual(held['cases'][0]['model']['model'], 'hnmt:item/gun/%s_icon' % name)
            self.assertEqual(held['fallback']['model'], 'hnmt:item/gun/%s' % name)
            model = json.loads((ROOT / ('assets/hnmt/models/item/gun/%s.json' % name)).read_text())
            self.assertGreater(len(model['elements']), 15, '3Dモデルは、箱を組んで作る')
            self.assertEqual(model['textures']['0'], 'hnmt:item/gun_model/atlas')
            for element in model['elements']:
                for point in element['from'] + element['to']: self.assertTrue(-16 <= point <= 32, '箱は、モデルの範囲（-16〜32）に収める')
            right, left = model['display']['firstperson_righthand'], model['display']['firstperson_lefthand']
            self.assertEqual(left['rotation'], [right['rotation'][0], -right['rotation'][1], -right['rotation'][2]], '左手は、右手の左右反転')

    def test_the_loaded_models_have_a_glowing_match_and_the_empty_ones_do_not(self):
        for gun in ('matchlock', 'tanzutsu'):
            empty = json.loads((ROOT / ('assets/hnmt/models/item/gun/%s.json' % gun)).read_text())['elements']
            loaded = json.loads((ROOT / ('assets/hnmt/models/item/gun/%s_loaded.json' % gun)).read_text())['elements']
            self.assertEqual(sum(1 for e in empty if e.get('light_emission')), 0)
            self.assertEqual(sum(1 for e in loaded if e.get('light_emission')), 2, '装填済みは、火縄の先が光る')
            self.assertEqual(len(loaded), len(empty) + 2)

    def test_every_gun_item_has_an_icon_model_and_item_definition(self):
        for name in ('matchlock', 'matchlock_loaded', 'tanzutsu', 'tanzutsu_loaded', 'ammo_teppo', 'ammo_shoidan', 'ammo_sandan'):
            self.assertTrue((ROOT / 'assets/hnmt/textures/item/gun' / (name + '.png')).stat().st_size > 0, name)
            icon = name + ('' if name.startswith('ammo_') else '_icon')
            model = json.loads((ROOT / 'assets/hnmt/models/item/gun' / (icon + '.json')).read_text())
            self.assertEqual(model['textures']['layer0'], 'hnmt:item/gun/' + name)
            self.assertEqual(model['parent'], 'minecraft:item/generated')
            self.assertNotIn('display', model, '平らなアイコンは、バニラの設定のまま')

    def test_the_bedrock_table_has_every_gun_item(self):
        bases = json.loads((ROOT / 'tools/bedrock_bases.json').read_text())
        for name in ('matchlock', 'matchlock_loaded', 'tanzutsu', 'tanzutsu_loaded', 'ammo_teppo', 'ammo_shoidan', 'ammo_sandan'):
            self.assertIn('gun/' + name, bases)
        self.assertEqual(bases['gun/matchlock'], bases['gun/matchlock_loaded'], '装填済みも、元のアイテムは同じ')


if __name__ == '__main__':
    unittest.main()
