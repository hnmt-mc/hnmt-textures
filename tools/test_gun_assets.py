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

    def test_the_scope_view_is_a_ring_with_a_clear_lens_and_clear_surroundings(self):
        from PIL import Image
        view = Image.open(ROOT / 'assets/hnmt/textures/misc/gun_scope.png')
        self.assertEqual((view.size, view.mode), ((1024, 576), 'RGBA'))
        for corner in ((2, 2), (1021, 2), (2, 300), (1021, 300)):
            self.assertEqual(view.getpixel(corner)[3], 0, '縁の外（四隅・左右）は、透明（景色が見える）')
        cx, cy = 512, int(576 * 0.43)
        self.assertEqual(view.getpixel((cx + 90, cy + 60))[3] < 80, True, 'レンズの中は、ほぼ透明')
        self.assertEqual(view.getpixel((cx, cy - 175))[3], 255, '筒の縁（円環）は、不透明な黒')
        self.assertEqual(view.getpixel((cx, cy))[:3], (230, 40, 40), '中央は、赤い点')
        self.assertEqual(view.getpixel((cx, 570))[3], 255, '画面の下には、銃の本体がある')
        opaque = sum(1 for p in view.getdata() if p[3] > 200)
        self.assertLess(opaque / (1024 * 576), 0.35, '視界の大半は、覆わない')

    def test_the_scope_view_capability_needs_the_picture(self):
        self.assertIn('gun-scope-v1', make_manifest.manifest('v0.11.2', packed())['capabilities'])
        self.assertNotIn('gun-scope-v1', make_manifest.manifest('v0.11.2', packed(drop='assets/hnmt/textures/misc/gun_scope.png'))['capabilities'])
        self.assertNotIn('gun-scope-v1', make_manifest.manifest('v0.11.2', packed(empty='assets/hnmt/textures/misc/gun_scope.png'))['capabilities'])

    def test_a_loaded_gun_switches_to_the_aim_pose_while_use_is_held(self):
        for gun in ('matchlock', 'tanzutsu'):
            item = json.loads((ROOT / ('assets/hnmt/items/gun/%s_loaded.json' % gun)).read_text())['model']
            self.assertEqual((item['type'], item['property'], item['keybind']), ('minecraft:condition', 'minecraft:keybind_down', 'key.use'))
            self.assertEqual(item['on_true']['model'], 'hnmt:item/gun/%s_aim' % gun)
            self.assertEqual(item['on_false']['model'], 'hnmt:item/gun/%s_loaded' % gun)
            aim = json.loads((ROOT / ('assets/hnmt/models/item/gun/%s_aim.json' % gun)).read_text())
            self.assertEqual(aim['textures']['layer0'], 'hnmt:item/gun/%s_loaded' % gun, '構えの絵は、装填済みと同じ')
            normal = json.loads((ROOT / ('assets/hnmt/models/item/gun/%s_loaded.json' % gun)).read_text())
            self.assertLess(aim['display']['firstperson_righthand']['translation'][0], normal['display']['firstperson_righthand']['translation'][0], '構えは、銃が中央（左）へ寄る')
            self.assertEqual(aim['display']['firstperson_righthand']['rotation'], normal['display']['firstperson_righthand']['rotation'])
        for gun in ('matchlock', 'tanzutsu'):
            plain = json.loads((ROOT / ('assets/hnmt/items/gun/%s.json' % gun)).read_text())['model']
            self.assertEqual(plain['type'], 'minecraft:model', '空の銃は、構えの絵を持たない')

    def test_every_gun_item_has_an_icon_model_and_item_definition(self):
        names = ('matchlock', 'matchlock_loaded', 'tanzutsu', 'tanzutsu_loaded', 'ammo_teppo', 'ammo_shoidan', 'ammo_sandan')
        for name in names:
            self.assertTrue((ROOT / 'assets/hnmt/textures/item/gun' / (name + '.png')).stat().st_size > 0, name)
            model = json.loads((ROOT / 'assets/hnmt/models/item/gun' / (name + '.json')).read_text())
            self.assertEqual(model['textures']['layer0'], 'hnmt:item/gun/' + name)
            self.assertEqual(model['parent'], 'minecraft:item/generated')
            if name.startswith('ammo_'): self.assertNotIn('display', model)
            else:
                for context in ('firstperson_righthand', 'firstperson_lefthand', 'thirdperson_righthand', 'thirdperson_lefthand'):
                    self.assertIn(context, model['display'], name + ' ' + context)
                right, left = model['display']['firstperson_righthand'], model['display']['firstperson_lefthand']
                self.assertEqual(left['rotation'], [right['rotation'][0], -right['rotation'][1], -right['rotation'][2]], '左手は、右手の左右反転')
            item = json.loads((ROOT / 'assets/hnmt/items/gun' / (name + '.json')).read_text())
            reference = item['model'] if item['model']['type'] == 'minecraft:model' else item['model']['on_false']
            self.assertEqual(reference['model'], 'hnmt:item/gun/' + name)

    def test_the_bedrock_table_has_every_gun_item(self):
        bases = json.loads((ROOT / 'tools/bedrock_bases.json').read_text())
        for name in ('matchlock', 'matchlock_loaded', 'tanzutsu', 'tanzutsu_loaded', 'ammo_teppo', 'ammo_shoidan', 'ammo_sandan'):
            self.assertIn('gun/' + name, bases)
        self.assertEqual(bases['gun/matchlock'], bases['gun/matchlock_loaded'], '装填済みも、元のアイテムは同じ')


if __name__ == '__main__':
    unittest.main()
