import io
import json
import unittest
import zipfile
from pathlib import Path

import make_manifest

ROOT = Path(__file__).resolve().parents[1]
EVENTS = make_manifest.BLADE_SOUNDS + make_manifest.BLADE_ATTACK_SOUNDS


def packed(drop=None, empty=None):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as z:
        for path in [ROOT / 'assets/hnmt/sounds.json', ROOT / 'assets/hnmt/font/blade.json', *sorted((ROOT / 'assets/hnmt/textures/font').glob('blade_*.png')), *sorted((ROOT / 'assets/hnmt/sounds/blade').glob('*.ogg'))]:
            name = str(path.relative_to(ROOT))
            if name == drop: continue
            z.writestr(name, b'' if name == empty else path.read_bytes())
    return out.getvalue()


class BladeSoundTests(unittest.TestCase):
    def test_every_event_points_at_an_existing_ogg(self):
        events = json.loads((ROOT / 'assets/hnmt/sounds.json').read_text())
        for event in EVENTS:
            self.assertTrue(events[event]['sounds'], event)
            for entry in events[event]['sounds']:
                namespace, name = entry['name'].split(':')
                self.assertEqual(namespace, 'hnmt')
                self.assertTrue((ROOT / 'assets/hnmt/sounds' / (name + '.ogg')).stat().st_size > 0, entry['name'])

    def test_the_ogg_files_are_vorbis_mono(self):
        for path in (ROOT / 'assets/hnmt/sounds/blade').glob('*.ogg'):
            data = path.read_bytes()
            self.assertEqual(data[:4], b'OggS', path.name)
            self.assertIn(b'vorbis', data[:200], path.name)

    def test_the_capability_is_advertised_only_when_every_sound_is_in_the_zip(self):
        self.assertIn('blade-sounds-v1', make_manifest.manifest('v0.9.0', packed())['capabilities'])
        self.assertNotIn('blade-sounds-v1', make_manifest.manifest('v0.9.0', packed(drop='assets/hnmt/sounds/blade/draw.ogg'))['capabilities'])
        self.assertNotIn('blade-sounds-v1', make_manifest.manifest('v0.9.0', packed(empty='assets/hnmt/sounds/blade/dash.ogg'))['capabilities'])
        self.assertNotIn('blade-sounds-v1', make_manifest.manifest('v0.9.0', b'not a zip')['capabilities'])

    def test_the_attack_capability_needs_the_attack_sounds_too(self):
        self.assertIn('blade-attack-sounds-v1', make_manifest.manifest('v0.9.1', packed())['capabilities'])
        broken = make_manifest.manifest('v0.9.1', packed(drop='assets/hnmt/sounds/blade/crit1.ogg'))['capabilities']
        self.assertIn('blade-sounds-v1', broken, '古い5つの音は、そのまま使える')
        self.assertNotIn('blade-attack-sounds-v1', broken)


    def test_the_screen_capability_needs_the_font_and_both_images(self):
        self.assertIn('blade-screen-v1', make_manifest.manifest('v0.10.0', packed())['capabilities'])
        for missing in ('assets/hnmt/font/blade.json', 'assets/hnmt/textures/font/blade_slash.png', 'assets/hnmt/textures/font/blade_drain.png'):
            self.assertNotIn('blade-screen-v1', make_manifest.manifest('v0.10.0', packed(drop=missing))['capabilities'], missing)
        self.assertNotIn('blade-screen-v1', make_manifest.manifest('v0.10.0', packed(empty='assets/hnmt/textures/font/blade_drain.png'))['capabilities'])

    def test_the_font_maps_the_characters_the_server_sends(self):
        providers = json.loads((ROOT / 'assets/hnmt/font/blade.json').read_text())['providers']
        self.assertEqual({p['file']: p['chars'] for p in providers}, {'hnmt:font/blade_slash.png': ['\ue000'], 'hnmt:font/blade_drain.png': ['\ue001']})
        for p in providers: self.assertLessEqual(p['ascent'], p['height'])

    def test_the_screen_images_are_transparent_and_the_size_the_font_expects(self):
        from PIL import Image
        for name in ('blade_slash', 'blade_drain'):
            image = Image.open(ROOT / 'assets/hnmt/textures/font' / (name + '.png'))
            self.assertEqual(image.size, (512, 256))
            self.assertEqual(image.mode, 'RGBA')
            self.assertEqual(image.getpixel((256, 128))[3] == 0 or name == 'blade_slash', True, '吸血の絵は、中央が透明')


if __name__ == '__main__':
    unittest.main()