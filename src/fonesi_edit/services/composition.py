"""Canonical CPU raster compositor shared by reference preview and export."""
from functools import lru_cache
from pathlib import Path
import math
from PIL import Image,ImageDraw,ImageFilter,ImageColor
from ..core.model import Project,Layer,US
from .fonts import load_font,missing_glyphs,font_file

STYLE_KEYS={'font_path','font_size','fill','stroke','stroke_width','align','padding','line_spacing','background','background_radius','shadow','shadow_x','shadow_y','shadow_blur','overflow','min_font_size','max_lines','mask_mode','blur_radius','mosaic_size','radius','fade_in','fade_out'}


def rgba(color,default='#ffffff'):
    return ImageColor.getcolor(color or default,'RGBA')


def wrap_text(text,font,width,draw,stroke=0):
    lines=[]
    for paragraph in text.split('\n'):
        if not paragraph:lines.append('');continue
        line=''
        for ch in paragraph:
            trial=line+ch
            if line and draw.textbbox((0,0),trial,font=font,stroke_width=stroke)[2]>width:
                lines.append(line.rstrip());line=ch.lstrip()
            else:line=trial
        lines.append(line)
    return lines


def text_image(layer:Layer,width:int,height:int) -> Image.Image:
    style=layer.style;unknown=set(style)-STYLE_KEYS
    if unknown:raise ValueError('Unsupported text/style properties: '+', '.join(sorted(unknown)))
    pad=int(style.get('padding',6));size=int(style.get('font_size',40));minimum=int(style.get('min_font_size',12))
    image=Image.new('RGBA',(max(1,width),max(1,height)));draw=ImageDraw.Draw(image)
    stroke=int(style.get('stroke_width',0));spacing=float(style.get('line_spacing',1.15))
    while True:
        font=load_font(style.get('font_path',''),size);lines=wrap_text(layer.text,font,max(1,width-2*pad),draw,stroke)
        line_h=math.ceil(size*spacing);needed=len(lines)*line_h+2*pad
        too_many=len(lines)>int(style.get('max_lines',100))
        if needed<=height and not too_many:break
        if style.get('overflow','warn')=='shrink' and size>minimum:size-=1;continue
        raise ValueError(f'Text overflow in layer {layer.name}; enlarge box or enable shrink (text was not silently clipped)')
    if style.get('background'):
        draw.rounded_rectangle((0,0,width-1,height-1),radius=int(style.get('background_radius',0)),fill=rgba(style['background']))
    for i,line in enumerate(lines):
        bbox=draw.textbbox((0,0),line,font=font,stroke_width=stroke);text_width=bbox[2]-bbox[0]
        align=style.get('align','center');x=pad if align=='left' else width-pad-text_width if align=='right' else (width-text_width)/2
        y=pad+i*line_h-bbox[1]
        if style.get('shadow'):
            shadow=Image.new('RGBA',image.size);sd=ImageDraw.Draw(shadow)
            sd.text((x+int(style.get('shadow_x',2)),y+int(style.get('shadow_y',2))),line,font=font,fill=rgba(style['shadow']))
            image.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(float(style.get('shadow_blur',0)))))
        draw=ImageDraw.Draw(image);draw.text((x,y),line,font=font,fill=rgba(style.get('fill')),stroke_width=stroke,stroke_fill=rgba(style.get('stroke','#000000')))
    return image


@lru_cache(maxsize=32)
def _logo(path,mtime):
    with Image.open(path) as image:return image.convert('RGBA')


def composition_warnings(project:Project) -> list[str]:
    warnings=[]
    texts=[(x.style.get('font_path',''),x.text,x.name) for x in project.layers if x.kind=='text']
    texts += [(project.settings.get('subtitle_font',''),c.translation or c.text,'subtitle') for c in project.cues]
    for path,text,name in texts:
        absent=missing_glyphs(path,text)
        if absent:warnings.append(f'{name}: font is missing glyphs: '+''.join(absent))
    return list(dict.fromkeys(warnings))


def paint_frame(frame:Image.Image,project:Project,time_us:int) -> Image.Image:
    frame=frame.convert('RGBA')
    if frame.size!=(project.width,project.height):raise ValueError('Base frame size differs from composition canvas')
    for layer in sorted(project.layers,key=lambda x:x.z):
        if not layer.visible or not layer.start<=time_us<layer.end:continue
        values=layer.at(time_us);w=max(1,round(values['width']*project.width));h=max(1,round(values['height']*project.height))
        if w*h>project.width*project.height*16:raise ValueError('Layer dimensions exceed safe raster budget')
        x=round(values['x']*project.width);y=round(values['y']*project.height)
        if layer.kind=='text':overlay=text_image(layer,w,h)
        elif layer.kind=='logo':
            if not layer.asset_path:raise ValueError('Logo path missing')
            p=Path(layer.asset_path);overlay=_logo(str(p),p.stat().st_mtime_ns).resize((w,h),Image.Resampling.LANCZOS)
        elif layer.kind=='mask':
            mode=layer.style.get('mask_mode','color')
            if mode=='color':overlay=Image.new('RGBA',(w,h),rgba(layer.style.get('fill','#000000')))
            elif mode=='blur':overlay=frame.crop((x,y,x+w,y+h)).filter(ImageFilter.GaussianBlur(float(layer.style.get('blur_radius',12))))
            elif mode=='mosaic':
                block=max(2,int(layer.style.get('mosaic_size',12)))
                overlay=frame.crop((x,y,x+w,y+h)).resize((max(1,w//block),max(1,h//block))).resize((w,h),Image.Resampling.NEAREST)
            else:raise ValueError('Unsupported mask mode '+mode)
            radius=int(layer.style.get('radius',0))
            if radius:
                alpha=Image.new('L',(w,h));ImageDraw.Draw(alpha).rounded_rectangle((0,0,w-1,h-1),radius=radius,fill=255);overlay.putalpha(alpha)
        else:raise ValueError('Unsupported layer '+layer.kind)
        opacity=values['opacity'];fi=int(layer.style.get('fade_in',0));fo=int(layer.style.get('fade_out',0))
        if fi:opacity*=min(1,(time_us-layer.start)/fi)
        if fo:opacity*=min(1,(layer.end-time_us)/fo)
        opacity=max(0,min(1,opacity));overlay.putalpha(overlay.getchannel('A').point(lambda a:round(a*opacity)))
        if values['rotation']:
            overlay=overlay.rotate(-values['rotation'],expand=True,resample=Image.Resampling.BICUBIC)
            x-=round((overlay.width-w)/2);y-=round((overlay.height-h)/2)
        frame.alpha_composite(overlay,(x,y))
    if project.settings.get('burn_subtitles',True):
        active=[c for c in project.cues if c.start<=time_us<c.end]
        if active:
            text='\n'.join((c.text+'\n'+c.translation if project.settings.get('bilingual') and c.translation else c.translation or c.text) for c in active)
            sub=Layer(text=text,name='Phụ đề',width=.9,height=.28,style={
                'font_size':int(project.settings.get('subtitle_size',max(16,project.height//22))),
                'font_path':project.settings.get('subtitle_font',''),'fill':'#ffffff','stroke':'#000000','stroke_width':2,
                'align':'center','overflow':'shrink','min_font_size':12,'padding':8})
            overlay=text_image(sub,round(project.width*.9),round(project.height*.28))
            frame.alpha_composite(overlay,(round(project.width*.05),round(project.height*.70)))
    return frame.convert('RGB')
