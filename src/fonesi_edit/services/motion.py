"""Deterministic time-based keyframes; independent of preview zoom and output FPS."""
from dataclasses import dataclass
import math
import random
from ..core.model import Keyframe,Layer,US

PRESETS=['fixed','left-right','right-left','top-bottom','bottom-top','diagonal','ping-pong','corners','zoom-in','zoom-out','rotate','fade','random']


def motion(layer:Layer,preset:str,*,duration:int,delay=0,hold=0,gap=0,repeat=1,easing='linear',seed=0,margin=.03):
    if layer.locked:raise ValueError('Layer is locked; motion was not changed')
    if preset not in PRESETS or duration<=0 or min(delay,hold,gap)<0 or repeat<1:raise ValueError('Invalid motion parameters')
    if easing not in {'linear','ease-in','ease-out','ease-in-out'}:raise ValueError('Unsupported easing')
    if layer.width>1-2*margin or layer.height>1-2*margin:raise ValueError('Object is too large for the configured motion region')
    right=1-margin-layer.width;bottom=1-margin-layer.height;paths={
        'left-right':[(margin,layer.y),(right,layer.y)],'right-left':[(right,layer.y),(margin,layer.y)],
        'top-bottom':[(layer.x,margin),(layer.x,bottom)],'bottom-top':[(layer.x,bottom),(layer.x,margin)],
        'diagonal':[(margin,margin),(right,bottom)],'ping-pong':[(margin,layer.y),(right,layer.y),(margin,layer.y)],
        'corners':[(margin,margin),(right,margin),(right,bottom),(margin,bottom),(margin,margin)]}
    if preset=='random':
        rng=random.Random(seed);paths[preset]=[(rng.uniform(margin,right),rng.uniform(margin,bottom)) for _ in range(5)]
    result={}
    def put(key,t,value):result.setdefault(key,[]).append(Keyframe(t,value,easing))
    for cycle in range(repeat):
        offset=delay+cycle*(duration+hold+gap)
        if preset in paths:
            points=paths[preset]
            for i,(x,y) in enumerate(points):
                t=offset+round(duration*i/(len(points)-1));put('x',t,x);put('y',t,y)
            if hold:
                put('x',offset+duration+hold,points[-1][0]);put('y',offset+duration+hold,points[-1][1])
        elif preset in {'zoom-in','zoom-out'}:
            start,end=(.8,1) if preset=='zoom-in' else (1,.8)
            for key,value in [('width',layer.width),('height',layer.height)]:put(key,offset,value*start);put(key,offset+duration,value*end)
        elif preset=='rotate':put('rotation',offset,layer.rotation);put('rotation',offset+duration,layer.rotation+360)
        elif preset=='fade':
            put('opacity',offset,0);put('opacity',offset+duration//4,layer.opacity);put('opacity',offset+duration*3//4,layer.opacity);put('opacity',offset+duration,0)
    return result


def layout_random(layer:Layer,seed:int,avoid=(),attempts=100):
    if layer.locked:return {'x':layer.x,'y':layer.y,'reason':'manual lock preserved'}
    if layer.width>1 or layer.height>1:raise ValueError('Layer is larger than canvas')
    rng=random.Random(seed)
    for _ in range(attempts):
        x=rng.uniform(0,1-layer.width);y=rng.uniform(0,1-layer.height)
        if all(x+layer.width<=a or a+w<=x or y+layer.height<=b or b+h<=y for a,b,w,h in avoid):return {'x':x,'y':y,'reason':'seeded nonoverlapping candidate'}
    return {'x':layer.x,'y':layer.y,'warning':'No placement found within bounded attempts; original position preserved'}
