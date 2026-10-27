import itertools
import json
import unittest
import zipfile
import io
from pathlib import Path

import make_manifest

ROOT = Path(__file__).resolve().parents[1]
DIRECTIONS = ('north', 'east', 'south', 'west', 'up', 'down')


class RiceInteractionTests(unittest.TestCase):
    def test_only_the_faceless_state_uses_an_invisible_model(self):
        parts = json.loads((ROOT / 'assets/minecraft/blockstates/sculk_vein.json').read_text())['multipart']
        for flags in itertools.product((False, True), repeat=6):
            state = dict(zip(DIRECTIONS, flags))
            applied = [p['apply'] for p in parts if all(state[k] == (v == 'true') for k, v in p['when'].items())]
            if any(flags):
                self.assertEqual(len(applied), sum(flags))
                self.assertTrue(all(p['model'] == 'minecraft:block/sculk_vein' for p in applied))
            else:
                self.assertEqual(applied, [{'model': 'hnmt:block/rice_hitbox'}])
        model = json.loads((ROOT / 'assets/hnmt/models/block/rice_hitbox.json').read_text())
        self.assertEqual(model['elements'], [])
        self.assertEqual(model['textures']['particle'], 'minecraft:block/wheat_stage7')

    def test_capability_is_only_advertised_when_the_support_assets_exist(self):
        def packed(include):
            out = io.BytesIO()
            with zipfile.ZipFile(out, 'w') as z:
                if include:
                    for file in ('assets/minecraft/blockstates/sculk_vein.json', 'assets/hnmt/models/block/rice_hitbox.json'):
                        z.writestr(file, (ROOT / file).read_bytes())
            return out.getvalue()
        self.assertNotIn('rice-held-harvest-v1', make_manifest.manifest('v0.4.2', packed(False))['capabilities'])
        self.assertIn('rice-held-harvest-v1', make_manifest.manifest('v0.4.2', packed(True))['capabilities'])
