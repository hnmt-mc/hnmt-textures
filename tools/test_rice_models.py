"""米作りの配置、Blockbench編集元、32pxテクスチャの契約を検査する。"""
import base64
import itertools
import json
import math
import unittest
from PIL import Image
from artwork import PACK
from make_models import inventory
from make_rice_models import RICE, geometry, texture


class RiceModelTests(unittest.TestCase):
    def model(self,name):
        return json.loads((PACK/'models3d/rice'/f'{name}.json').read_text())

    def test_six_ids_are_added_without_replacing_cooked_rice(self):
        entries = list(inventory())
        self.assertEqual(len(entries),71)
        self.assertEqual({name for group,name,_ in entries if group=='rice'},set(dict(RICE)))
        self.assertIn(('', 'rice', '米'),entries)
        cooked = json.loads((PACK/'assets/hnmt/items/rice.json').read_text())
        self.assertEqual(cooked['model']['model'],'hnmt:item/rice')
        for name,_ in RICE:
            definition = json.loads((PACK/'assets/hnmt/items/rice'/f'{name}.json').read_text())
            self.assertEqual(definition['model'],{'type':'minecraft:model','model':f'hnmt:item/rice/{name}'})

    def test_textures_are_binary_rgba_32px_and_distinct(self):
        signatures = set()
        for name,_ in RICE:
            with Image.open(PACK/'assets/hnmt/textures/item/rice'/f'{name}.png') as image:
                self.assertEqual(image.size,(32,32))
                self.assertEqual(image.mode,'RGBA')
                self.assertEqual(set(image.getchannel('A').get_flattened_data()),{0,255})
                self.assertLessEqual(len(set(image.get_flattened_data())),16)
                self.assertEqual(image.tobytes(),texture(name).tobytes())
                signatures.add(image.tobytes())
        self.assertEqual(len(signatures),6)

    def test_native_projects_embed_exported_texture_and_named_parts(self):
        for name,_ in RICE:
            with self.subTest(name=name):
                project = json.loads((PACK/'blockbench/rice'/f'{name}.bbmodel').read_text())
                self.assertEqual(project['meta']['model_format'],'java_block')
                self.assertEqual(project['resolution'],{'width':32,'height':32})
                self.assertEqual(len(project['textures']),1)
                data = project['textures'][0]['source'].split(',',1)[1]
                self.assertEqual(base64.b64decode(data),(PACK/'assets/hnmt/textures/item/rice'/f'{name}.png').read_bytes())
                self.assertEqual(len(project['elements']),len(self.model(name)['elements']))
                groups = {group['name'] for group in project['groups']}
                self.assertTrue(({'Base','Top','Handle'} if name=='mill' else {'Stalk','Leaves'}) <= groups)
                if name in ('stalk','plant_mature'): self.assertIn('Ear',groups)

    def test_export_matches_source_geometry_and_samples_only_opaque_pixels(self):
        for name,_ in RICE:
            model = self.model(name)
            self.assertEqual(set(model['textures'].values()),{f'hnmt:item/rice/{name}'})
            self.assertLessEqual(len(model['elements']),220)
            source = {part['name']:part for part in geometry(name)}
            self.assertEqual({part['name'] for part in model['elements']},set(source))
            with Image.open(PACK/'assets/hnmt/textures/item/rice'/f'{name}.png') as image:
                for part in model['elements']:
                    expected = source[part['name']]
                    for key in ('from','to','faces'): self.assertEqual(part[key],expected[key])
                    if 'rotation' in expected:
                        for key in ('axis','angle','origin'):
                            if key=='origin':
                                for a,b in zip(part['rotation'][key],expected['rotation'][key]): self.assertAlmostEqual(a,b,places=4)
                            else: self.assertEqual(part['rotation'][key],expected['rotation'][key])
                    self.assertEqual(len(part['faces']),6)
                    for face in part['faces'].values():
                        u0,v0,u1,v1 = face['uv']
                        self.assertTrue(0<=u0<u1<=16 and 0<=v0<v1<=16)
                        for y in range(round(v0*2),round(v1*2)):
                            for x in range(round(u0*2),round(u1*2)):
                                self.assertEqual(image.getpixel((x,y))[3],255)

    def test_actual_rotated_corners_stay_in_bounds(self):
        for name,_ in RICE:
            for part in self.model(name)['elements']:
                minimum = -1 if name.startswith('plant_') else 0
                rotation = part.get('rotation')
                if rotation:
                    self.assertIn(rotation['angle'],(-45,-22.5,0,22.5,45))
                    axis = 'xyz'.index(rotation['axis'])
                    angle = math.radians(rotation['angle'])
                for corner in itertools.product(*zip(part['from'],part['to'])):
                    point = list(corner)
                    if rotation:
                        a,b = ((1,2),(2,0),(0,1))[axis]
                        pa,pb = point[a]-rotation['origin'][a],point[b]-rotation['origin'][b]
                        point[a] = rotation['origin'][a]+pa*math.cos(angle)-pb*math.sin(angle)
                        point[b] = rotation['origin'][b]+pa*math.sin(angle)+pb*math.cos(angle)
                    self.assertTrue(0<point[0]<16 and minimum<=point[1]<=16 and 0<point[2]<16,(name,part['name'],point))

    def test_display_placement_has_no_hidden_rotation_or_scale(self):
        heights = []
        for name,_ in RICE:
            model = self.model(name)
            fixed = model['display'].get('fixed',{})
            self.assertEqual(fixed.get('rotation',[0,0,0]),[0,0,0])
            self.assertEqual(fixed.get('translation',[0,0,0]),[0,0,0])
            self.assertEqual(fixed.get('scale',[1,1,1]),[1,1,1])
            for mode in ('gui','ground','firstperson_righthand','thirdperson_righthand'):
                self.assertIn(mode,model['display'])
            if name.startswith('plant_'):
                stems = [part for part in model['elements'] if part['name'].startswith('Stalk')]
                self.assertTrue(all(part['from'][1]==-1 for part in stems))
                heights.append(max(part['to'][1] for part in model['elements']))
        self.assertLess(heights[0],heights[1])
        self.assertLess(heights[1],heights[2])
        mill = self.model('mill')['elements']
        lower = [part for part in mill if part['name'].startswith('Base')]
        upper = [part for part in mill if part['name'].startswith('Top')]
        self.assertTrue(all(part['from'][1]==0 for part in lower))
        self.assertGreater(min(part['from'][1] for part in upper),max(part['to'][1] for part in lower))

    def test_binding_follows_the_gathered_stems_without_a_wide_frame(self):
        for name in ('seedling','stalk'):
            model = self.model(name)
            ties = [part for part in model['elements'] if part['name'].startswith('Tie')]
            self.assertTrue(any(part['name']=='Tie_knot' for part in ties))
            self.assertTrue(all(part['to'][0]-part['from'][0]<1.5 for part in ties))
            self.assertTrue(all(part['to'][2]-part['from'][2]<1 for part in ties))
            lower = [part for part in model['elements'] if part['name'].startswith('Stalk_lower')]
            self.assertLess(max(part['to'][0] for part in lower)-min(part['from'][0] for part in lower),1.2)

    def test_unknown_ids_are_rejected(self):
        with self.assertRaises(ValueError): texture('../rice')
        with self.assertRaises(ValueError): geometry('unknown')


if __name__=='__main__': unittest.main()
