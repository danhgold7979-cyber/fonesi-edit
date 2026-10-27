"""Small expression tree shared by sampled ASS motion and FFmpeg filters."""
from dataclasses import dataclass
import hashlib
import math
import random


@dataclass(frozen=True)
class Expr:
    op:str
    args:tuple=()
    def __add__(self,x):return expr('+',self,node(x))
    def __radd__(self,x):return node(x)+self
    def __sub__(self,x):return expr('-',self,node(x))
    def __rsub__(self,x):return node(x)-self
    def __mul__(self,x):return expr('*',self,node(x))
    def __rmul__(self,x):return self*x
    def __truediv__(self,x):return expr('/',self,node(x))
    def ffmpeg(self,time='t'):
        if self.op=='number':return f'{self.args[0]:.8f}'
        if self.op=='time':return time
        if self.op in '+-*/':return '('+self.args[0].ffmpeg(time)+self.op+self.args[1].ffmpeg(time)+')'
        return self.op+'('+','.join(a.ffmpeg(time) for a in self.args)+')'
    def value(self,t):
        if self.op=='number':return self.args[0]
        if self.op=='time':return t
        v=[a.value(t) for a in self.args]
        return {'+':lambda:v[0]+v[1],'-':lambda:v[0]-v[1],'*':lambda:v[0]*v[1],'/':lambda:v[0]/v[1],
            'min':lambda:min(v),'max':lambda:max(v),'mod':lambda:v[0]%v[1],'abs':lambda:abs(v[0]),
            'sin':lambda:math.sin(v[0]),'lt':lambda:float(v[0]<v[1]),'if':lambda:v[1] if v[0] else v[2]}[self.op]()


def node(value):return value if isinstance(value,Expr) else Expr('number',(float(value),))
def expr(op,*args):return Expr(op,tuple(node(a) for a in args))
T=Expr('time')


def easing(u,kind):
    if kind=='ease-in':return u*u
    if kind=='ease-out':return 1-(1-u)*(1-u)
    if kind=='ease-in-out':return u*u*(3-2*u)
    return u


def interpolate(points,t,ease='linear'):
    if not points:raise ValueError('Missing keyframes')
    if len(points)>64:raise ValueError('Maximum 64 keyframes per property')
    result=node(points[-1]['value'])
    for a,b in reversed(list(zip(points,points[1:]))):
        span=b['time']-a['time']
        if span<=0:raise ValueError('Keyframes must be sorted')
        u=expr('min',1,expr('max',0,(t-a['time'])/span));u=easing(u,ease)
        result=expr('if',expr('lt',t,b['time']),a['value']+(b['value']-a['value'])*u,result)
    return expr('if',expr('lt',t,points[0]['time']),points[0]['value'],result)


def transforms(layer,width,height,seed=0,total_duration=None):
    m=layer.motion;elapsed=expr('max',0,T-layer.start-float(m.get('delay',0)))
    duration=max(.1,float(m.get('duration',5)))
    hold=max(0,float(m.get('hold',0)));period=duration+hold
    elapsed_cycle=expr('mod',elapsed,period) if m.get('repeat',True) else elapsed
    count=max(0,int(m.get('repeat_count',0)))
    if count and m.get('repeat',True):elapsed_cycle=expr('if',expr('lt',elapsed,period*count),elapsed_cycle,duration)
    u=expr('min',1,elapsed_cycle/duration)
    u=easing(u,m.get('easing','linear'));preset=m.get('preset','fixed')
    x=node(layer.x);y=node(layer.y);scale=node(1);rotation=node(layer.rotation);opacity=node(layer.opacity)
    speed=max(0,min(2000,float(m.get('speed',20))))
    rx=max(.001,1-layer.width);ry=max(.001,1-layer.height)
    if preset in {'left-right','right-left','diagonal'}:
        x=expr('mod',layer.x+elapsed*speed/width,rx)
        if preset=='right-left':x=rx-x
        if preset=='diagonal':y=expr('mod',layer.y+elapsed*speed/height,ry)
    elif preset in {'top-bottom','bottom-top'}:
        y=expr('mod',layer.y+elapsed*speed/height,ry)
        if preset=='bottom-top':y=ry-y
    elif preset in {'pingpong','bounce'}:
        x=rx-expr('abs',expr('mod',layer.x+elapsed*speed/width,2*rx)-rx)
        if preset=='bounce':y=ry-expr('abs',expr('mod',layer.y+elapsed*speed/height,2*ry)-ry)
    elif preset in {'corners','random'}:
        rng=random.Random(int(hashlib.sha256(f'{seed}:{layer.id}'.encode()).hexdigest()[:16],16))
        points=[(0,0),(rx,0),(rx,ry),(0,ry),(0,0)] if preset=='corners' else [(rng.random()*rx,rng.random()*ry) for _ in range(5)]
        x=interpolate([{'time':i/4,'value':p[0]} for i,p in enumerate(points)],u)
        y=interpolate([{'time':i/4,'value':p[1]} for i,p in enumerate(points)],u)
    elif preset=='zoom':
        low=max(.1,float(m.get('zoom_min',.95)));high=max(low,min(5,float(m.get('zoom_max',1.05))))
        scale=(low+high)/2+(high-low)/2*expr('sin',elapsed*(2*math.pi/duration))
    elif preset=='a-b':x=layer.x+(float(m.get('end_x',layer.x))-layer.x)*u;y=layer.y+(float(m.get('end_y',layer.y))-layer.y)*u
    elif preset!='fixed':raise ValueError('Unknown motion preset: '+preset)
    values={'x':x,'y':y,'scale':scale,'rotation':rotation,'opacity':opacity}
    if m.get('rotate_speed'):values['rotation']=rotation+float(m['rotate_speed'])*elapsed
    for key,points in layer.keyframes.items():
        time=(T-layer.start)/max(.001,(layer.end or total_duration or layer.start+1)-layer.start) if m.get('relative_time') else T
        if points:values[key]=interpolate(points,time,m.get('easing','linear'))
    fade_in=float(m.get('fade_in',0));fade_out=float(m.get('fade_out',0))
    if fade_in>0:values['opacity']=values['opacity']*expr('min',1,expr('max',0,(T-layer.start)/fade_in))
    end=layer.end if layer.end is not None else total_duration
    if fade_out>0 and end is not None:values['opacity']=values['opacity']*expr('min',1,expr('max',0,(end-T)/fade_out))
    return values
