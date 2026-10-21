#!/usr/bin/env python3
"""米作りの座標と32pxの絵を作り、Blockbenchへ渡す。"""
import argparse
import base64
import json
import math
from PIL import Image, ImageDraw
from artwork import PACK, BUILD

RICE = [('seedling', '稲の苗'), ('stalk', '刈った稲'), ('mill', '石臼'),
        ('plant_seedling', '田んぼ・苗'), ('plant_growing', '田んぼ・成長中'), ('plant_mature', '田んぼ・実り')]
PALETTE = {'outline': '#515767', 'green': '#70915b', 'light': '#a3ba79',
           'straw': '#be9659', 'gold': '#dfb86e', 'grain': '#f2d796', 'root': '#a48d6b',
           'stone_dark': '#858d89', 'stone': '#a2aaa5', 'stone_light': '#b5bcb2',
           'wood': '#926e4c', 'wood_light': '#c49b66', 'hole': '#424b4b'}
FACES = ('north', 'south', 'east', 'west', 'up', 'down')


def texture(name):
    if name not in dict(RICE):
        raise ValueError('Unknown rice item: ' + name)
    image = Image.new('RGBA', (32, 32))
    d = ImageDraw.Draw(image)
    p = PALETTE
    def polygon(points, color):
        d.polygon(points, fill=p[color], outline=p['outline'], width=1)
    if name == 'mill':
        polygon([(4,17),(9,14),(24,14),(29,18),(29,24),(24,28),(8,28),(3,24),(3,19)], 'stone_dark')
        polygon([(4,16),(9,12),(24,12),(28,16),(28,21),(24,24),(9,24),(4,21)], 'stone')
        polygon([(4,15),(9,11),(23,11),(28,15),(23,19),(9,19)], 'stone_light')
        d.line((5,20,10,23,23,23,27,20), fill=p['stone_light'])
        d.line((5,24,10,27,22,27,27,24), fill=p['stone'])
        for xy in [(10,12,13,14),(21,12,19,14),(8,15,12,16),(21,16,25,15)]:
            d.line(xy, fill=p['stone_dark'])
        d.rectangle((15,14,18,16), fill=p['hole'])
        polygon([(23,13),(23,4),(26,3),(27,5),(27,13)], 'wood')
        d.line((24,5,24,11), fill=p['wood_light'])
        d.point((16,15), fill=p['grain'])
        for xy in [(11,20),(17,22),(21,20)]: d.point(xy,fill=p['stone_dark'])
        for xy in [(14,21),(20,21),(10,22)]: d.point(xy,fill=p['stone_light'])
        return image
    mature = name in ('stalk', 'plant_mature')
    small = name in ('seedling', 'plant_seedling')
    shoots = [(10,8),(15,4),(20,9)] if not small else [(12,15),(17,12),(21,16)]
    for x,tip in shoots:
        d.line((16,27,x,tip), fill=p['outline'], width=3)
        d.line((16,26,x,tip), fill=p['straw' if mature else 'green'])
        for sign,h in [(-1,tip+6),(1,tip+10)]:
            endx = max(2,min(29,x+sign*(7 if not small else 5)))
            polygon([(x,h+6),(endx,h-2),(endx+sign,h-3),(x+sign*2,h+5)], 'gold' if mature else 'green')
            d.line((x,h+4,endx,h-2), fill=p['grain' if mature else 'light'])
        if mature:
            d.line((x,tip+2,x+3,tip-1,x+6,tip+2,x+7,tip+7), fill=p['straw'], width=2)
            for i in range(4):
                gx,gy = x+3+i,tip+i
                d.rectangle((gx,gy,gx+2,gy+2), fill=p['straw'])
                d.line((gx,gy,gx+1,gy), fill=p['grain'])
                d.point((gx+1,gy+1), fill=p['gold'])
    if name in ('seedling','stalk'):
        polygon([(12,24),(19,23),(21,26),(14,28)], 'root')
        d.line((13,25,19,24), fill=p['grain'])
        for x in (14,17,20):
            d.line((x,27,x-1,30), fill=p['root'])
    return image


class Model:
    def __init__(self,image):
        self.parts = []
        self.samples = {}
        pixels = list(image.get_flattened_data())
        for key,color in PALETTE.items():
            rgba = tuple(bytes.fromhex(color[1:]))+(255,)
            if rgba in pixels:
                i = pixels.index(rgba)
                x,y = i%32,i//32
                self.samples[key] = [x/2,y/2,(x+1)/2,(y+1)/2]

    def cube(self,name,start,end,color,top=None):
        if any(a>=b for a,b in zip(start,end)):
            raise ValueError('Degenerate part: '+name)
        self.parts.append({'name':name,'from':[round(x,3) for x in start],'to':[round(x,3) for x in end],
                           'faces':{f:{'uv':self.samples[top if f=='up' and top else color],'texture':'#0'} for f in FACES}})

    def line(self,name,a,b,width,color,top=None):
        self.cube(name,[min(x,y)-width/2 for x,y in zip(a,b)],
                  [max(x,y)+width/2 for x,y in zip(a,b)],color,top)

    def leaf(self,name,x,y,z,axis,sign,length,gold=False):
        # 薄い葉身を三つに分け、根元から立ち上げて先端だけ垂らす。
        origin = [x,y,z]
        for i,(fraction,angle) in enumerate([(.5,45),(.3,22.5),(.2,-22.5)]):
            span = length*fraction
            width = .55-i*.18
            start = [origin[0]-width/2,origin[1]-.07,origin[2]-width/2]
            end = [origin[0]+width/2,origin[1]+.07,origin[2]+width/2]
            start[axis] = origin[axis]+min(0,sign*span)
            end[axis] = origin[axis]+max(0,sign*span)
            self.cube(name+str(i),start,end,'gold' if gold else 'green','grain' if gold else 'light')
            self.parts[-1]['rotation'] = {'angle':sign*angle*(1 if axis==0 else -1),
                                          'axis':'z' if axis==0 else 'x','origin':origin.copy()}
            origin[axis] += sign*span*math.cos(math.radians(angle))
            origin[1] += span*math.sin(math.radians(angle))

    def beam(self,name,origin,axis,sign,length,angle,width,color):
        start = [origin[0]-width/2,origin[1]-width/2,origin[2]-width/2]
        end = [origin[0]+width/2,origin[1]+width/2,origin[2]+width/2]
        start[axis] = origin[axis]+min(0,sign*length)
        end[axis] = origin[axis]+max(0,sign*length)
        self.cube(name,start,end,color)
        self.parts[-1]['rotation'] = {'angle':sign*angle*(1 if axis==0 else -1),
                                      'axis':'z' if axis==0 else 'x','origin':origin.copy()}
        point = origin.copy()
        point[axis] += sign*length*math.cos(math.radians(angle))
        point[1] += length*math.sin(math.radians(angle))
        return point

    def ear(self,name,x,y,z,sign,axis=0):
        # 主軸の先を下へ曲げ、細い枝の先に二粒ずつ実らせる。
        origin = [x,y,z]
        for i,(length,angle) in enumerate([(.8,22.5),(.9,-22.5),(1,-45),(.9,-45)]):
            origin = self.beam(name+'_spine'+str(i),origin,axis,sign,length,angle,.13,'straw')
            for side in (-1,1):
                point = origin.copy()
                cross = 2 if axis==0 else 0
                point[cross] += side*(.36+i*.04)
                self.line(name+'_twig'+str(i)+str(side),origin,point,.11,'straw')
                self.cube(name+'_drop'+str(i)+str(side),(point[0]-.055,point[1]-.9,point[2]-.055),
                          (point[0]+.055,point[1]+.05,point[2]+.055),'straw')
                for grain in range(2):
                    cx,cy,cz = point
                    cy -= .25+grain*.46
                    self.cube(name+'_grain'+str(i)+str(side)+str(grain),(cx-.18,cy-.28,cz-.16),
                              (cx+.18,cy+.24,cz+.16),'gold','grain')
                    self.parts[-1]['faces']['down']['uv'] = self.samples['straw']


def geometry(name,image=None):
    if name not in dict(RICE):
        raise ValueError('Unknown rice item: '+name)
    model = Model(image if image is not None else texture(name))
    if name=='mill':
        # 円盤は重ならない帯を並べ、上石を少し小さくする。
        for label,y0,y1,scale in [('Base',0,2.1,1),('Top',2.45,5.65,.93)]:
            for i,(z0,z1,half) in enumerate([(2,3,2.5),(3,4,4),(4,6,5.3),(6,10,6),(10,12,5.3),(12,13,4),(13,14,2.5)]):
                model.cube(label+'_'+str(i),(8-half*scale,y0,8+(z0-8)*scale),
                           (8+half*scale,y1,8+(z1-8)*scale),'stone','stone_light')
                for face in ('north','south','east','west'):
                    model.parts[-1]['faces'][face]['uv'] = [5,10,11,11.5]
        model.cube('Axle',(7.45,2.05,7.45),(8.55,2.5,8.55),'stone_dark')
        model.cube('Hopper',(7.1,5.65,8.9),(8.9,5.72,10.2),'hole')
        for i in range(3):
            model.cube('Rice'+str(i),(7.3+i*.45,5.72,9.1),(7.55+i*.45,5.9,9.6),'grain')
        for i,(a,b) in enumerate([((4,5.65,6.5),(6.4,5.71,6.7)),((9.2,5.65,5),(9.4,5.71,7)),
                                   ((4.7,5.65,10),(6.3,5.71,10.2)),((9.8,5.65,11),(11.6,5.71,11.2))]):
            model.cube('Groove'+str(i),a,b,'stone_dark')
        model.cube('Handle_socket',(10.6,5.65,7.2),(12.2,6.1,8.8),'stone_dark')
        model.cube('Handle',(10.9,5.95,7.5),(11.9,10.7,8.5),'wood','wood_light')
        model.cube('Handle_cap',(10.8,10.5,7.4),(12,10.9,8.6),'wood_light')
    elif name.startswith('plant_'):
        young = name=='plant_seedling'
        mature = name=='plant_mature'
        for i,(x,z,delta) in enumerate([(6,6,0),(9.4,6.3,.7),(6.4,9.7,.4),(9.5,9.6,-.4),(8,8,.2)]):
            h = (4.7 if young else 11.5 if mature else 10.5)+delta
            model.cube('Stalk'+str(i),(x-.105,-1,z-.105),(x+.105,h,z+.105),'straw' if mature else 'green','gold' if mature else 'light')
            leaves = [(-1,.45),(1,.72)] if young else [(-1,.25),(1,.48),(-1,.75)]
            for n,(side,height) in enumerate(leaves):
                model.leaf('Leaf'+str(i)+'_'+str(n),x,h*height,z,(i+n)%2*2,side,2.6 if young else 3.8,mature)
            if not mature:
                model.leaf('Leaf_tip'+str(i),x,h-.2,z,i%2*2,1 if i%2 else -1,1.8)
            if mature and i%2==0:
                axis = i%2*2
                model.ear('Ear'+str(i),x,h,z,1 if (x if axis==0 else z)<8 else -1,axis)
    else:
        mature = name=='stalk'
        for i in range(5 if mature else 4):
            bx,bz = 7.5+i*.2,7.55+(i%2)*.3
            height = (11+(i%3)*.6 if mature else 8.5+(i%2))
            origin = [bx,4.2,bz]
            angle = (-22.5,22.5,0,22.5,-22.5)[i]
            axis = 'z' if i%2==0 else 'x'
            color = 'straw' if mature else 'green'
            model.cube('Stalk_lower'+str(i),(bx-.09,1.2,bz-.09),(bx+.09,4.2,bz+.09),color)
            model.cube('Stalk_upper'+str(i),(bx-.09,4.2,bz-.09),(bx+.09,height,bz+.09),color)
            model.parts[-1]['rotation'] = {'axis':axis,'angle':angle,'origin':origin}
            length = height-4.2
            x,y,z = bx,4.2+length*math.cos(math.radians(angle)),bz
            if axis=='z': x -= length*math.sin(math.radians(angle))
            else: z += length*math.sin(math.radians(angle))
            attach_x,attach_z = bx+(x-bx)*.65,bz+(z-bz)*.65
            model.leaf('Leaf'+str(i),attach_x,4.2+(y-4.2)*.65,attach_z,0,-1 if i%2 else 1,2.8,mature)
            if mature: model.ear('Ear'+str(i),x,y,z,-1 if x>8 else 1,0 if axis=='z' else 2)
            else:
                model.leaf('Leaf_tip'+str(i),x,y-.3,z,0,1 if i%2 else -1,2.3)
                model.line('Root'+str(i),(bx,1.4,bz),(bx-.25,.4,bz+.1),.12,'root')
        # ひもは束に密着させる。前後の輪郭に細い結び目と垂れを添える。
        for i,(a,b) in enumerate([((7.32,4.05,7.37),(8.48,4.2,7.5)),((7.32,4.05,7.96),(8.48,4.2,8.09)),
                                   ((7.32,4.05,7.5),(7.45,4.2,7.96)),((8.35,4.05,7.5),(8.48,4.2,7.96))]):
            model.cube('Tie_wrap'+str(i),a,b,'root')
        model.cube('Tie_knot',(7.65,3.98,7.21),(7.9,4.27,7.48),'root')
        model.beam('Tie_tail0',[7.72,4.02,7.32],0,-1,.6,45,.1,'root')
        model.beam('Tie_tail1',[7.82,4.02,7.32],0,1,.5,-45,.1,'root')
    return model.parts


def build(name):
    image = texture(name)
    parts = geometry(name,image)
    path = PACK/'assets/hnmt/textures/item/rice'/f'{name}.png'
    path.parent.mkdir(parents=True,exist_ok=True)
    image.save(path)
    display = {'fixed':{'rotation':[0,0,0],'translation':[0,0,0],'scale':[1,1,1]},
               'gui':{'rotation':[25,225,0],'translation':[0,3 if name=='mill' else 1,0],'scale':[1.05]*3},
               'ground':{'translation':[0,3,0],'scale':[.5]*3},
               'firstperson_righthand':{'rotation':[0,-35,0],'translation':[0,2,0],'scale':[.65]*3},
               'thirdperson_righthand':{'rotation':[75,45,0],'translation':[0,2,0],'scale':[.55]*3}}
    model = {'credit':'HNMT rice models / Blockbench','texture_size':[32,32],'gui_light':'side',
             'textures':{'0':f'hnmt:item/rice/{name}','particle':f'hnmt:item/rice/{name}'},'elements':parts,'display':display}
    for folder,data in [('items',{'model':{'type':'minecraft:model','model':f'hnmt:item/rice/{name}'}}),
                        ('models/item',{'parent':'minecraft:item/generated','textures':{'layer0':f'hnmt:item/rice/{name}'}})]:
        out = PACK/'assets/hnmt'/folder/'rice'/f'{name}.json'
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n')
    return model,path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--review',action='store_true',help='Blockbenchのプレビュー一覧を作る')
    args = parser.parse_args()
    target = BUILD/'rice3d'
    target.mkdir(parents=True,exist_ok=True)
    if args.review:
        from artwork import sheet
        images = [Image.open(target/(n+'-preview.png')).convert('RGBA') for n,_ in RICE]
        boxes = [im.getbbox() for im in images]
        bounds = (min(b[0] for b in boxes)-12,min(b[1] for b in boxes)-12,
                  max(b[2] for b in boxes)+12,max(b[3] for b in boxes)+12)
        size = max(bounds[2]-bounds[0],bounds[3]-bounds[1])
        entries = []
        for image,(name,label) in zip(images,RICE):
            crop = image.crop(bounds)
            square = Image.new('RGBA',(size,size))
            square.paste(crop,((size-crop.width)//2,(size-crop.height)//2))
            entries.append((square,label,name))
        sheet(entries,'rice3d/contact-sheet.png',columns=3,tile=256)
        return
    entries = []
    for name,label in RICE:
        model,path = build(name)
        entries.append({'name':name,'label':label,'model':model,'image':'data:image/png;base64,'+base64.b64encode(path.read_bytes()).decode()})
    (target/'manifest.json').write_text(json.dumps(entries,ensure_ascii=False,indent=2)+'\n')
    print('Prepared 6 rice models for Blockbench')


if __name__=='__main__': main()
