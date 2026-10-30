"""Versioned project documents, strict schema and immutable save-as."""
from dataclasses import dataclass
from pathlib import Path
from uuid import UUID
import json
import os
import tempfile
from fonesi_edit.snapshot import local_path
from fonesi_edit.timing import ClipMap, Interval, time_value


def identity(value):
    if not isinstance(value,str) or str(UUID(value))!=value:raise ValueError('INVALID_ID')
    return value

@dataclass(frozen=True)
class ProjectMedia:
    id: str
    source: str
    edit: ClipMap | None=None
    def __post_init__(self):
        identity(self.id);local_path(self.source)
        if self.edit is not None and (not isinstance(self.edit,ClipMap) or self.edit.output_start!=0):raise ValueError('UNSUPPORTED_EDIT')

@dataclass(frozen=True)
class Project:
    id: str
    title: str
    media: tuple[ProjectMedia,...]
    def __post_init__(self):
        identity(self.id)
        if not isinstance(self.title,str) or not 1<=len(self.title)<=200 or '\x00' in self.title:raise ValueError('INVALID_TITLE')
        if not isinstance(self.media,tuple) or len(self.media)>1000 or not all(isinstance(x,ProjectMedia) for x in self.media):raise ValueError('INVALID_MEDIA')
        if len({x.id for x in self.media})!=len(self.media):raise ValueError('DUPLICATE_MEDIA_ID')
    def encode(self):
        def fraction(v):return [v.numerator,v.denominator]
        def edit(v):
            if v is None:return None
            return {'start':fraction(v.source.start),'end':fraction(v.source.end),'speed':fraction(v.speed),'output_start':fraction(v.output_start)}
        result=json.dumps({'format':'fonesi-edit-rebuild','schema':1,'id':self.id,'title':self.title,
            'media':[{'id':m.id,'source':m.source,'edit':edit(m.edit)} for m in self.media]},ensure_ascii=False,sort_keys=True,separators=(',',':')).encode('utf-8')
        if len(result)>4194304:raise ValueError('PROJECT_TOO_LARGE')
        return result
    @classmethod
    def decode(cls,data):
        if not isinstance(data,bytes) or len(data)>4194304:raise ValueError('PROJECT_TOO_LARGE')
        def unique(pairs):
            out={}
            for key,value in pairs:
                if key in out:raise ValueError('DUPLICATE_KEY')
                out[key]=value
            return out
        def fields(obj,keys):
            if not isinstance(obj,dict) or set(obj)!=set(keys):raise ValueError('UNKNOWN_OR_MISSING_FIELD')
        def fraction(v):
            if not isinstance(v,list) or len(v)!=2:raise ValueError('INVALID_TIME')
            return time_value(*v)
        try:
            obj=json.loads(data,object_pairs_hook=unique)
            fields(obj,('format','schema','id','title','media'))
            if obj['format']!='fonesi-edit-rebuild' or type(obj['schema']) is not int or obj['schema']!=1:raise ValueError('UNSUPPORTED_SCHEMA')
            if not isinstance(obj['media'],list) or len(obj['media'])>1000:raise ValueError('INVALID_MEDIA')
            media=[]
            for m in obj['media']:
                fields(m,('id','source','edit'));edit=m['edit']
                if edit is not None:
                    fields(edit,('start','end','speed','output_start'))
                    edit=ClipMap(Interval(fraction(edit['start']),fraction(edit['end'])),fraction(edit['speed']),fraction(edit['output_start']))
                media.append(ProjectMedia(m['id'],m['source'],edit))
            return cls(obj['id'],obj['title'],tuple(media))
        except (ValueError,TypeError,KeyError,RecursionError,AttributeError) as exc:
            raise ValueError('INVALID_PROJECT') from exc


def save_new(project: Project,destination: Path):
    data=project.encode();destination=destination.absolute()
    if not destination.parent.is_dir():raise ValueError('MISSING_PARENT')
    with tempfile.TemporaryDirectory(prefix='.fonesi-project-',dir=destination.parent) as folder:
        staged=Path(folder)/'project.json'
        with staged.open('xb') as stream:stream.write(data);stream.flush();os.fsync(stream.fileno())
        if Project.decode(staged.read_bytes())!=project:raise ValueError('READBACK_FAILED')
        os.link(staged,destination)


def load_project(path: Path):
    with path.open('rb') as stream:data=stream.read(4194305)
    return Project.decode(data)
