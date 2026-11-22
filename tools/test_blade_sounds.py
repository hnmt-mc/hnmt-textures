import io
import json
import unittest
import zipfile
from pathlib import Path

import make_manifest

ROOT = Path(__file__).resolve().parents[1]
EVENTS = make_manifest.BLADE_SOUNDS


def packed(drop=None, empty=None):
    out = io.BytesIO()
    with zipfile.ZipFile(out, 'w') as z:
        for path in [ROOT / 'assets/hnmt/sounds.json', *sorted((ROOT / 'assets/hnmt/sounds/blade').glob('*.ogg'))]:
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


if __name__ == '__main__':
    unittest.main()
