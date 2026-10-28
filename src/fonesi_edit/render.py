"""Production reference compositor. Preview and final export use the same graph."""
from dataclasses import asdict,replace
from copy import deepcopy
from fractions import Fraction
from functools import lru_cache
from pathlib import Path
import hashlib
import json
import math
import os
import shutil
import subprocess
import tempfile
import time
import random

import pysubs2
from fontTools.ttLib import TTFont
from .domain import Composition,atomic_json,canonical,fingerprint
from .fonts import resolve_font,missing_glyphs,open_font
from .motion import transforms
from .prototypes.media import probe,run_checked,_publish,MediaError,extract_frame
from .prototypes.tools import locate_tool
from .prototypes.subtitles import Cue,map_trimmed_cues
from .subtitles import read_captions


def audio_duration(path):
    data=json.loads(run_checked(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(Path(path).resolve())]).stdout)
    if not any(s.get('codec_type')=='audio' for s in data['streams']):raise ValueError('Không có audio track')
    return float(data['format']['duration'])


def atempo(speed):
    values=[]
    while speed>2:values.append('atempo=2');speed/=2
    while speed<.5:values.append('atempo=0.5');speed*=2
    return ','.join([*values,f'atempo={speed:.8f}'])


@lru_cache(maxsize=8)
def encoder_for(mode):
    names={'nvidia':'h264_nvenc','intel':'h264_qsv','amd':'h264_amf'}
    candidates=[mode] if mode not in {'auto','cpu'} else (['nvidia','intel','amd'] if mode=='auto' and (os.name=='nt' or Path('/dev/dri').exists() or Path('/dev/nvidia0').exists()) else [])
    ffmpeg=locate_tool('ffmpeg')
    for candidate in candidates:
        name=names[candidate]
        result=subprocess.run([ffmpeg,'-v','error','-f','lavfi','-i','color=s=128x128:r=1','-t','1','-c:v',name,'-f','null','-'],capture_output=True,timeout=12)
        if result.returncode==0:return name
    if mode not in {'auto','cpu'}:raise PermissionError('Encoder GPU chưa dùng được trên máy này: '+mode)
    return 'libx264'


def _color(value,alpha=0):
    value=value or '#ffffff';return pysubs2.Color(int(value[1:3],16),int(value[3:5],16),int(value[5:7],16),int(alpha))


def _wrap(text,width,font_path,size,spacing=0,style=None):
    with open_font(font_path,style) as font:
        cmap=font.getBestCmap() or {};metrics=font['hmtx'].metrics;units=font['head'].unitsPerEm
        lines=[]
        for paragraph in text.split('\n'):
            line='';advance=0
            for character in paragraph:
                glyph=cmap.get(ord(character),'.notdef');step=metrics.get(glyph,(units,0))[0]/units*size+spacing
                if line and advance+step>width:lines.append(line.rstrip());line='';advance=0
                line+=character;advance+=step
            lines.append(line)
    return '\n'.join(lines)


def _ass_text(stage,layer,composition,duration,index):
    style=layer.style;path=resolve_font(style);font_target=stage/('font-'+hashlib.sha256(str(path).encode()).hexdigest()[:8]+path.suffix)
    if not font_target.exists():shutil.copyfile(path,font_target)
    with open_font(path,style) as font:
        family=font['name'].getDebugName(1) or style.get('font_family','Arial')
        line_ratio=(font['hhea'].ascent-font['hhea'].descent+font['hhea'].lineGap)/font['head'].unitsPerEm
    caption_segments=getattr(layer,'_caption_segments',None)
    missing=missing_glyphs(path,'\n'.join(segment[2] for segment in caption_segments) if caption_segments else layer.text,style)
    if missing:raise FileNotFoundError('Font thiếu ký tự: '+''.join(missing[:12])+'; hãy chọn font phù hợp')
    doc=pysubs2.SSAFile();doc.info.update({'PlayResX':str(composition.width),'PlayResY':str(composition.height),'WrapStyle':'2'})
    font_size=float(style.get('font_size',32));ass=pysubs2.SSAStyle(fontname=family,fontsize=font_size,
        primarycolor=_color(style.get('color','#ffffff')),outlinecolor=_color(style.get('outline_color','#000000')),
        backcolor=_color(style.get('shadow_color','#000000')),
        bold=bool(style.get('bold')),italic=bool(style.get('italic')),underline=bool(style.get('underline')),
        outline=float(style.get('outline',2)),shadow=float(style.get('shadow',0)),spacing=float(style.get('spacing',0)),
        borderstyle=1,alignment=pysubs2.Alignment.TOP_LEFT,marginl=0,marginr=0,marginv=0)
    doc.styles['Default']=ass
    padding=max(0,float(style.get('padding',0)))
    move=transforms(layer,composition.width,composition.height,composition.seed,duration)
    for segment_start,segment_end,segment_text in caption_segments if caption_segments is not None else [(layer.start,layer.end if layer.end is not None else duration,layer.text)]:
        text=_wrap(segment_text,max(10,layer.width*composition.width-2*padding),path,font_size,float(style.get('spacing',0)),style)
        lines=[line.replace('\\',r'\\').replace('{',r'\{').replace('}',r'\}') for line in text.split('\n')]
        line_height=font_size*line_ratio+float(style.get('line_spacing',0))
        start,end=segment_start,min(duration,segment_end)
        animated=bool(layer.keyframes) or layer.motion.get('preset','fixed')!='fixed' or layer.motion.get('fade_in') or layer.motion.get('fade_out') or layer.motion.get('rotate_speed')
        step=1/composition.fps if animated else max(.01,end-start)
        t=start
        if (end-start)/step>300000:raise ValueError('Layer quá dài cho chế độ motion hiện tại; chia project')
        align=style.get('align','left');anchor={'left':7,'center':8,'right':9}.get(align,7)
        while t<end-.0001:
            left=move['x'].value(t)*composition.width;top=move['y'].value(t)*composition.height
            x=left+padding
            if anchor==8:x=left+layer.width*composition.width/2
            elif anchor==9:x=left+layer.width*composition.width-padding
            cx=left+layer.width*composition.width/2;cy=top+layer.height*composition.height/2
            opacity=max(0,min(1,move['opacity'].value(t)));scale=max(.01,move['scale'].value(t))*100
            common=f'\\org({cx:.3f},{cy:.3f})\\frz{-move["rotation"].value(t):.3f}\\fscx{scale:.3f}\\fscy{scale:.3f}\\alpha&H{round((1-opacity)*255):02X}&'
            if style.get('background'):
                width=layer.width*composition.width;height=layer.height*composition.height;radius=min(max(0,float(style.get('corner_radius',0))),width/2,height/2)
                drawing=f'm {radius:.2f} 0 l {width-radius:.2f} 0 b {width:.2f} 0 {width:.2f} 0 {width:.2f} {radius:.2f} l {width:.2f} {height-radius:.2f} b {width:.2f} {height:.2f} {width:.2f} {height:.2f} {width-radius:.2f} {height:.2f} l {radius:.2f} {height:.2f} b 0 {height:.2f} 0 {height:.2f} 0 {height-radius:.2f} l 0 {radius:.2f} b 0 0 0 0 {radius:.2f} 0'
                color=style['background'];bgr=color[5:7]+color[3:5]+color[1:3]
                tags=f'{{\\an7\\pos({left:.3f},{top:.3f}){common}\\bord0\\shad0\\1c&H{bgr}&\\p1}}'
                doc.events.append(pysubs2.SSAEvent(start=round(t*1000),end=round(min(end,t+step)*1000),layer=0,text=tags+drawing+r'{\p0}'))
            for line_index,line in enumerate(lines):
                y=top+padding+line_index*line_height*scale/100
                tags=f'{{\\an{anchor}\\pos({x:.3f},{y:.3f}){common}}}'
                doc.events.append(pysubs2.SSAEvent(start=round(t*1000),end=round(min(end,t+step)*1000),layer=1,text=tags+line))
            t+=step
    name=f'layer-{index}.ass';doc.save(str(stage/name),encoding='utf-8');return name



def audio_timeline_offset(track, total, clips, clip_ranges):
    """Resolve an optional SFX trigger against the exported timeline.

    Offset measures seconds after absolute/percent/scene-start positions or
    seconds before video-end/scene-end. Scene numbers are 1-based and use
    the actual post-speed/transition clip ranges.
    """
    delay=float(track.get('offset',0))
    placement=track.get('placement','absolute')
    if placement=='absolute':
        resolved=delay
    elif placement=='percent':
        resolved=total*float(track['position_pct'])/100+delay
    elif placement=='video_end':
        resolved=total-delay
    elif placement in {'scene_start','scene_end'}:
        scene=clips[track['scene_index']-1]
        start,length=clip_ranges[scene.id]
        resolved=start+delay if placement=='scene_start' else start+length-delay
    else:
        raise ValueError('Unsupported SFX placement')
    if track.get('mode','music')=='sfx' and (not math.isfinite(resolved)
            or resolved<0 or resolved>=total-1e-8):
        raise ValueError('SFX starts outside the output timeline; adjust anchor or offset')
    return resolved


def compile_graph(c:Composition,stage:Path):
    c.validate()
    if not c.clips:raise ValueError('Chưa có clip')
    if len(c.clips)>128:raise ValueError('Một render tối đa 128 clip; chia lô để giữ tài nguyên')
    args=[];graph=[];segments=[];cursor=0.;mapped_cues=[];inputs=0;clip_ranges={}
    for i,clip in enumerate(c.clips):
        info=probe(Path(clip.path));end=clip.end if clip.end is not None else info.duration
        if end>info.duration+.1:raise ValueError('Trim vượt media nguồn')
        duration=(end-clip.start)/clip.speed+clip.freeze
        offset=cursor if clip.offset is None else clip.offset
        if offset<cursor-.02 and not c.transition:raise ValueError('Clip chồng thời gian; hãy đặt chuyển cảnh hoặc di chuyển clip')
        if offset>cursor+.02:
            gap=offset-cursor;label=f'gap{i}'
            graph += [f'color=c=black:s={c.width}x{c.height}:r={c.fps}:d={gap}[{label}v]',f'anullsrc=r=48000:cl=stereo,atrim=duration={gap}[{label}a]']
            segments.append((label+'v',label+'a',gap))
        args+=['-i',str(Path(clip.path).resolve())];idx=inputs;inputs+=1
        vf=[f'trim=start={clip.start:.8f}:end={end:.8f}',f'setpts=(PTS-STARTPTS)/{clip.speed:.8f}',f'fps={c.fps}','settb=AVTB']
        if clip.flip:vf.append('hflip')
        if clip.freeze:vf.append(f'tpad=stop_mode=clone:stop_duration={clip.freeze}')
        if clip.rotation:vf.append(f'rotate={clip.rotation:.8f}*PI/180:fillcolor=black')
        if c.fit=='crop':vf += [f'scale={c.width}:{c.height}:force_original_aspect_ratio=increase',f'crop={c.width}:{c.height}']
        else:vf += [f'scale={c.width}:{c.height}:force_original_aspect_ratio=decrease',f'pad={c.width}:{c.height}:(ow-iw)/2:(oh-ih)/2:color=black']
        vf += ['setsar=1','format=yuv420p']
        graph.append(f'[{idx}:v]'+','.join(vf)+f'[v{i}]')
        if c.fit=='blur':
            # Real blurred background from the same segment, with a fitted foreground.
            freeze=f',tpad=stop_mode=clone:stop_duration={clip.freeze}' if clip.freeze else ''
            transforms_source=','.join(vf[:next(j for j,v in enumerate(vf) if v.startswith('scale='))])
            graph[-1]=f'[{idx}:v]{transforms_source},split[bg{i}][fg{i}]'
            graph += [f'[bg{i}]scale={c.width}:{c.height}:force_original_aspect_ratio=increase,crop={c.width}:{c.height},boxblur=20:1[bgblur{i}]',
                      f'[fg{i}]scale={c.width}:{c.height}:force_original_aspect_ratio=decrease[fgfit{i}]',
                      f'[bgblur{i}][fgfit{i}]overlay=(W-w)/2:(H-h)/2,setsar=1,format=yuv420p[v{i}]']
        if info.audio_codec and not c.mute_original and not any(track.get('solo') and not track.get('mute') for track in c.audio):
            graph.append(f'[{idx}:a]atrim=start={clip.start}:end={end},asetpts=PTS-STARTPTS,{atempo(clip.speed)},volume={clip.volume},aresample=48000,aformat=channel_layouts=stereo,apad,atrim=duration={duration}[a{i}]')
        else:graph.append(f'anullsrc=r=48000:cl=stereo,atrim=duration={duration}[a{i}]')
        video_label=f'v{i}'
        settings=c.adjustments.get('batch_video',{})
        if settings.get('random_zoom'):
            lower,upper=float(settings.get('zoom_min',1)),float(settings.get('zoom_max',1.1))
            if not 1<=lower<=upper<=2:raise ValueError('Random zoom phải trong khoảng 1–2')
            rng=random.Random(f'{c.seed}:{clip.id}:zoom');phase=rng.uniform(0,6.28);period=rng.uniform(3,8)
            zoom=f'({lower}+({upper}-{lower})*(sin(t*2*PI/{period}+{phase})+1)/2)'
            graph.append(f"[v{i}]scale=w='ceil({c.width}*{zoom}/2)*2':h='ceil({c.height}*{zoom}/2)*2':eval=frame,crop={c.width}:{c.height}:(iw-ow)/2:(ih-oh)/2[zoom{i}]")
            video_label=f'zoom{i}'
        segments.append((video_label,f'a{i}',duration))
        clip_ranges[clip.id]=(offset,duration)
        if clip.subtitles:
            raw=[Cue(q.start_ms,q.end_ms,q.text) for q in read_captions(Path(clip.subtitles))]
            mapped_cues.extend(map_trimmed_cues(raw,round(clip.start*1000),round(end*1000),Fraction(str(clip.speed)),round(offset*1000)))
        cursor=offset+duration-(c.transition if i<len(c.clips)-1 else 0)
    if c.transition and len(segments)>1:
        video,audio,total=segments[0]
        for i,(v,a,length) in enumerate(segments[1:],1):
            overlap=c.transition
            if overlap>=min(total,length):raise ValueError('Transition dài hơn cảnh')
            graph += [f'[{video}][{v}]xfade=transition=fade:duration={overlap}:offset={total-overlap}[joinv{i}]',f'[{audio}][{a}]acrossfade=d={overlap}[joina{i}]']
            video,audio=f'joinv{i}',f'joina{i}';total+=length-overlap
    else:
        graph.append(''.join(f'[{v}][{a}]' for v,a,_ in segments)+f'concat=n={len(segments)}:v=1:a=1[basev][basea]')
        video,audio,total='basev','basea',sum(s[2] for s in segments)
    if c.duration_target and abs(total-c.duration_target)>max(.1,2/c.fps):raise ValueError('Duration plan chưa khớp âm thanh; chạy bước khớp thời lượng trước')
    if c.adjustments:
        eq={k:float(c.adjustments.get(k,d)) for k,d in [('brightness',0),('contrast',1),('saturation',1),('gamma',1)]}
        if not -1<=eq['brightness']<=1 or not all(0.1<=eq[k]<=3 for k in ('contrast','saturation','gamma')):raise ValueError('Color adjustment outside allowed range')
        graph.append(f'[{video}]eq='+':'.join(f'{k}={v}' for k,v in eq.items())+'[adjusted]');video='adjusted'
    layers=[]
    for layer in c.layers:
        if layer.kind=='subtitle' and layer.path:
            if layer.style.get('subtitle_role')=='target' and any(other.kind=='subtitle' and other.style.get('subtitle_role')=='source' and other.path==layer.path and other.clip_ids==layer.clip_ids for other in c.layers):continue
            caption_source=read_captions(Path(layer.path))
            scopes=[clip for clip in c.clips if clip.id in layer.clip_ids] if layer.clip_ids else [None]
            for clip in scopes:
                if clip is not None:
                    offset,length=clip_ranges[clip.id]
                    raw=[Cue(q.start_ms,q.end_ms,q.text) for q in caption_source]
                    end=clip.end if clip.end is not None else probe(Path(clip.path)).duration
                    mapped=map_trimmed_cues(raw,round(clip.start*1000),round(end*1000),Fraction(str(clip.speed)),round(offset*1000))
                else:mapped=[Cue(q.start_ms+round(layer.start*1000),q.end_ms+round(layer.start*1000),q.text) for q in caption_source]
                copy=deepcopy(layer);copy.path=None;copy.clip_ids=[]
                copy.start=(offset if clip is not None else 0)+layer.start
                copy.end=min(total,(offset+length if clip is not None else total),copy.start+layer.end-layer.start if layer.end is not None else total)
                shift=layer.start if clip is not None else 0
                copy._caption_segments=[(max(copy.start,q.start_ms/1000+shift),min(copy.end,q.end_ms/1000+shift),q.text) for q in mapped if min(copy.end,q.end_ms/1000+shift)>max(copy.start,q.start_ms/1000+shift)]
                if clip is not None and not layer.motion.get('relative_time'):
                    copy.keyframes={key:[{'time':p['time']+offset,'value':p['value']} for p in points] for key,points in layer.keyframes.items()}
                if copy._caption_segments:layers.append(copy)
            continue
        if layer.kind in {'text','subtitle'} and not layer.text:continue
        if not layer.clip_ids:layers.append(layer);continue
        for clip_id in layer.clip_ids:
            if clip_id not in clip_ranges:continue
            offset,length=clip_ranges[clip_id];copied=deepcopy(layer)
            copied.start=offset+layer.start;copied.end=min(offset+length,offset+(layer.end if layer.end is not None else length))
            if copied.end<=copied.start:continue
            if not layer.motion.get('relative_time'):
                copied.keyframes={key:[{'time':p['time']+offset,'value':p['value']} for p in points] for key,points in layer.keyframes.items()}
            layers.append(copied)
    for i,layer in enumerate(layers):
        if not layer.visible:continue
        target=f'layer{i}';enabled=f"between(t,{layer.start:.6f},{min(total,layer.end or total):.6f})"
        move=transforms(layer,c.width,c.height,c.seed,total)
        if layer.kind in {'text','subtitle'}:
            ass=_ass_text(stage,layer,c,total,i);graph.append(f'[{video}]subtitles=filename={ass}:fontsdir=.[{target}]')
        elif layer.kind=='image':
            if not layer.path or not Path(layer.path).is_file():raise FileNotFoundError('Logo missing')
            image=stage/f'image-{i}{Path(layer.path).suffix.lower()}';shutil.copyfile(layer.path,image)
            args+=['-loop','1','-i',image.name];idx=inputs;inputs+=1
            width=max(2,round(layer.width*c.width));height=max(2,round(layer.height*c.height))
            scale=move['scale'].ffmpeg();angle=move['rotation'].ffmpeg()+'*PI/180'
            alpha=move['opacity'].ffmpeg(time='T')
            graph.append(f"[{idx}:v]format=rgba,scale=w='{width}*({scale})':h='{height}*({scale})':eval=frame,rotate=a='{angle}':ow='hypot(iw,ih)':oh='hypot(iw,ih)':c=none,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='alpha(X,Y)*({alpha})'[image{i}]")
            x=f'({move["x"].ffmpeg()})*W+({width}-w)/2';y=f'({move["y"].ffmpeg()})*H+({height}-h)/2'
            graph.append(f"[{video}][image{i}]overlay=x='{x}':y='{y}':enable='{enabled}':shortest=1[{target}]")
        else:
            w=max(2,round(layer.width*c.width));h=max(2,round(layer.height*c.height))
            mode=layer.style.get('mode','blur')
            x=f'({move["x"].ffmpeg("T")})*{c.width}+{w}/2';y=f'({move["y"].ffmpeg("T")})*{c.height}+{h}/2'
            angle=f'({move["rotation"].ffmpeg("T")})*PI/180';scale=move['scale'].ffmpeg('T')
            localx=f'abs((X-({x}))*cos({angle})+(Y-({y}))*sin({angle}))'
            localy=f'abs(-(X-({x}))*sin({angle})+(Y-({y}))*cos({angle}))'
            corner=max(0,min(float(layer.style.get('corner_radius',0)),w/2,h/2))
            qx=f'({localx}-{w}/2*({scale})+{corner})';qy=f'({localy}-{h}/2*({scale})+{corner})'
            distance=f'(hypot(max({qx},0),max({qy},0))+min(max({qx},{qy}),0)-{corner})'
            feather=max(0,min(100,float(layer.style.get('feather',0))))
            shape=f'min(1,max(0,-{distance}/{feather}))' if feather else f'lte({distance},0)'
            alpha=f'255*({move["opacity"].ffmpeg("T")})*({shape})'
            graph.append(f'[{video}]split[maskbase{i}][masksrc{i}]')
            if mode=='color':
                color=layer.style.get('color','#000000')
                rgb=[int(color[j:j+2],16) for j in (1,3,5)]
                graph.append(f"[masksrc{i}]format=rgba,geq=r={rgb[0]}:g={rgb[1]}:b={rgb[2]}:a='{alpha}'[mask{i}]")
            else:
                radius=max(1,min(int(layer.style.get('radius',10)),w//4,h//4,50))
                effect=f'scale={max(1,c.width//12)}:{max(1,c.height//12)},scale={c.width}:{c.height}:flags=neighbor' if mode=='mosaic' else f'boxblur={radius}:1'
                graph.append(f"[masksrc{i}]{effect},format=rgba,geq=r='r(X,Y)':g='g(X,Y)':b='b(X,Y)':a='{alpha}'[mask{i}]")
            graph.append(f"[maskbase{i}][mask{i}]overlay=0:0:enable='{enabled}'[{target}]")
        video=target
    if mapped_cues:
        from .domain import Layer
        doc=pysubs2.SSAFile();doc.info.update({'PlayResX':str(c.width),'PlayResY':str(c.height)})
        style=c.subtitle_style;path=resolve_font(style);shutil.copyfile(path,stage/'sub-font.ttf')
        with open_font(path,style) as font:family=font['name'].getDebugName(1) or 'Arial'
        doc.styles['Default']=pysubs2.SSAStyle(fontname=family,fontsize=style.get('font_size',32),primarycolor=_color(style.get('color','#ffffff')),outlinecolor=_color(style.get('outline_color','#000000')),outline=style.get('outline',2),alignment=pysubs2.Alignment.BOTTOM_CENTER,marginv=style.get('margin',35))
        for cue in mapped_cues:doc.events.append(pysubs2.SSAEvent(start=cue.start_ms,end=cue.end_ms,text=cue.text.replace('\n',r'\N')))
        doc.save(str(stage/'captions.ass'),encoding='utf-8');graph.append(f'[{video}]subtitles=filename=captions.ass:fontsdir=.[subbed]');video='subbed'
    mix=[audio];modes=['original']
    solo=any(track.get('solo') and not track.get('mute') for track in c.audio)
    for i,track in enumerate(c.audio):
        if track.get('mute') or solo and not track.get('solo'):continue
        path=Path(track['path']).resolve();source_duration=audio_duration(path)
        loop_crossfade=float(track.get('loop_crossfade',0))
        if track.get('loop') and not track.get('trim_end') and not loop_crossfade:
            args+=['-stream_loop','-1']
        args+=['-i',str(path)];idx=inputs;inputs+=1
        start=max(0,float(track.get('trim_start',0)))
        offset=audio_timeline_offset(track,total,c.clips,clip_ranges)
        gain=float(track.get('volume',.2))
        end=float(track.get('trim_end') or source_duration)
        if not 0<=start<end<=source_duration+.001:raise ValueError('Audio trim nằm ngoài nguồn')
        if not 0<=gain<=4:raise ValueError('Audio volume must be 0–4')
        input_audio=f'{idx}:a'
        if loop_crossfade:
            segment_duration=end-start
            if loop_crossfade*2>=segment_duration:
                raise ValueError('Nhạc crossfade cần đoạn nguồn dài hơn hai lần thời lượng chuyển tiếp')
            remaining=max(0,total-offset)
            repeat_count=max(1,1+math.ceil((remaining-segment_duration)/(segment_duration-loop_crossfade)))
            if repeat_count>128:
                raise ValueError('Nhạc lặp crossfade vượt 128 đoạn; chọn nguồn dài hơn hoặc giảm video')
            labels=[f'loop{i}_{number}' for number in range(repeat_count)]
            # Feed each repetition from its own FFmpeg input. Reusing a single
            # stream through asplit plus chained acrossfade crashes FFmpeg
            # 7.1.1 on Windows (ffmpeg_filter.c: best_input assertion).
            for number,label in enumerate(labels):
                stream_index=idx
                if number:
                    stream_index=inputs
                    args+=['-i',str(path)]
                    inputs+=1
                graph.append(f'[{stream_index}:a]atrim=start={start}:end={end},'
                             f'asetpts=PTS-STARTPTS,aresample=48000,'
                             f'aformat=channel_layouts=stereo[{label}]')
            input_audio=labels[0]
            for number in range(1,repeat_count):
                joined=f'loopjoin{i}_{number}'
                graph.append(f'[{input_audio}][{labels[number]}]acrossfade='
                             f'd={loop_crossfade}:c1=tri:c2=tri[{joined}]')
                input_audio=joined
            filters=[f'volume={gain}']
        else:
            filters=[f'atrim=start={start}'+(f':end={end}' if track.get('trim_end') else ''),
                     'asetpts=PTS-STARTPTS',f'volume={gain}',
                     'aresample=48000','aformat=channel_layouts=stereo']
            if track.get('loop') and track.get('trim_end'):
                if end-start>600:raise ValueError('Đoạn âm thanh lặp sau trim giới hạn 10 phút để giữ RAM')
                filters.append(f'aloop=loop=-1:size={round((end-start)*48000)}')
        fi=float(track.get('fade_in',0));fo=float(track.get('fade_out',0))
        if fi>0:filters.append(f'afade=t=in:d={fi}')
        if fo>0:filters.append(f'afade=t=out:st={max(0,min(total-offset,total if track.get("loop") else end-start)-fo)}:d={fo}')
        filters += [f'adelay={round(offset*1000)}:all=1','apad',f'atrim=duration={total}']
        graph.append(f'[{input_audio}]'+','.join(filters)+f'[music{i}]');mix.append(f'music{i}');modes.append(track.get('mode','music'))
    music=[i for i,mode in enumerate(modes) if mode=='music']
    if c.adjustments.get('ducking') and music:
        voice=modes.index('main') if 'main' in modes else 0
        graph.append(f'[{mix[voice]}]asplit={len(music)+1}[voicemain]'+''.join(f'[duckside{i}]' for i in range(len(music))))
        mix[voice]='voicemain'
        for side,index in enumerate(music):
            graph.append(f'[{mix[index]}][duckside{side}]sidechaincompress=threshold=0.04:ratio=8[ducked{index}]');mix[index]=f'ducked{index}'
    normalize='loudnorm=I=-16:TP=-1.5:LRA=11,' if c.adjustments.get('normalize') else ''
    graph.append(''.join(f'[{a}]' for a in mix)+f'amix=inputs={len(mix)}:normalize=0:duration=longest,{normalize}alimiter=limit=0.95,atrim=duration={total}[outa]')
    graph.append(f'[{video}]format=yuv420p[outv]')
    return args,';'.join(graph),total


def render_composition(composition,destination,progress=lambda n:None,cancel=None):
    destination=destination.resolve();composition.validate()
    payload=composition.to_dict()
    assets=[Path(clip.path) for clip in composition.clips]+[Path(clip.subtitles) for clip in composition.clips if clip.subtitles]
    assets += [Path(layer.path) for layer in composition.layers if layer.path]+[Path(track['path']) for track in composition.audio]
    assets += [resolve_font(layer.style) for layer in composition.layers if layer.kind in {'text','subtitle'}]
    source_hashes={str(path.resolve()):fingerprint(path) for path in assets}
    config_hash=hashlib.sha256(canonical({'composition':payload,'sources':source_hashes}).encode()).hexdigest()
    sidecar=destination.with_suffix(destination.suffix+'.fonesi.json')
    if destination.exists():
        if sidecar.is_file():
            saved=json.loads(sidecar.read_text(encoding='utf-8'))
            if saved.get('config_hash')==config_hash and saved.get('sha256')==fingerprint(destination):
                probe(destination);return {**saved,'reused':True}
        raise FileExistsError('Không ghi đè đầu ra đã có: '+destination.name)
    if destination.suffix.lower()!='.mp4':raise ValueError('Output must be MP4')
    destination.parent.mkdir(parents=True,exist_ok=True);started=time.monotonic();encoder=encoder_for(composition.encoder)
    ffmpeg=locate_tool('ffmpeg')
    if not ffmpeg:raise FileNotFoundError('FFmpeg missing')
    with tempfile.TemporaryDirectory(prefix='.fonesi-render-',dir=destination.parent) as directory:
        stage=Path(directory);inputs,graph,duration=compile_graph(composition,stage)
        (stage/'graph.txt').write_text(graph,encoding='utf-8')
        quality=['-crf',str(composition.quality),'-preset','veryfast'] if encoder=='libx264' else ['-cq',str(composition.quality),'-preset','p4'] if encoder=='h264_nvenc' else ['-global_quality',str(composition.quality)] if encoder=='h264_qsv' else ['-qp_i',str(composition.quality),'-qp_p',str(composition.quality)]
        command=[ffmpeg,'-v','warning','-hide_banner','-nostdin','-n',*inputs,'-filter_complex_threads','1','-filter_complex_script','graph.txt','-map','[outv]','-map','[outa]',
            '-c:v',encoder,'-threads','2',*quality,'-c:a','aac','-t',f'{duration:.8f}','-movflags','+faststart','-progress','pipe:1','-nostats','output.mp4']
        with (stage/'progress').open('w') as log,(stage/'errors').open('w+') as errors:
            process=subprocess.Popen(command,cwd=stage,stdout=log,stderr=errors)
            try:
                while process.poll() is None:
                    if cancel and cancel.is_set():raise RuntimeError('Canceled')
                    if time.monotonic()-started>max(180,duration*60):raise TimeoutError('Render exceeded its safety time budget')
                    lines=(stage/'progress').read_text().splitlines()
                    times=[line.split('=',1)[1] for line in lines if line.startswith('out_time_us=')]
                    if times and times[-1].lstrip('-').isdigit():progress(min(.99,max(0,int(times[-1])/1e6/duration)))
                    time.sleep(.1)
                if process.returncode:
                    errors.seek(0);raise MediaError(errors.read()[-2500:])
            finally:
                if process.poll() is None:
                    process.terminate()
                    try:process.wait(3)
                    except subprocess.TimeoutExpired:process.kill();process.wait()
        output=stage/'output.mp4';info=probe(output)
        if (info.width,info.height)!=(composition.width,composition.height) or abs(info.duration-duration)>max(.15,2/composition.fps):raise MediaError('Output dimensions/duration did not match plan')
        run_checked([ffmpeg,'-v','error','-i',str(output),'-f','null','-'],timeout=max(30,duration*5))
        sha=fingerprint(output);_publish(output,destination)
    result={'output':str(destination),'validated':True,'config_hash':config_hash,'source_hashes':source_hashes,'sha256':sha,'encoder':encoder,'duration':duration,'elapsed_seconds':round(time.monotonic()-started,3),'media':asdict(info)}
    atomic_json(sidecar,result);progress(1)
    return result


def reference_frame(composition,folder,second=0,cancel=None):
    folder.mkdir(parents=True,exist_ok=True)
    # Same graph as export, but request a single composited frame instead of encoding the full video.
    inputs,graph,duration=compile_graph(composition,folder)
    graph+=';[outa]anullsink'
    (folder/'graph.txt').write_text(graph,encoding='utf-8')
    second=max(0,min(second,duration-1/composition.fps));frame=folder/'frame.png'
    command=[locate_tool('ffmpeg'),'-v','error','-nostdin','-n',*inputs,'-filter_complex_threads','1','-filter_complex_script','graph.txt',
        '-map','[outv]','-ss',str(second),'-frames:v','1','-threads','1',str(frame.resolve())]
    with (folder/'errors').open('w+') as errors:
        process=subprocess.Popen(command,cwd=folder,stdout=subprocess.DEVNULL,stderr=errors)
        started=time.monotonic()
        try:
            while process.poll() is None:
                if cancel and cancel.is_set():raise RuntimeError('Preview canceled')
                if time.monotonic()-started>120:raise TimeoutError('Preview exceeded time budget')
                time.sleep(.05)
            if process.returncode or not frame.is_file():
                errors.seek(0);raise MediaError(errors.read()[-1800:])
        finally:
            if process.poll() is None:process.terminate();process.wait(timeout=5)
    return frame
