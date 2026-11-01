"""Explicit empty-project intent and exclusive file creation, not rendering."""
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
import uuid
from fonesi_edit.domain.composition import CompositionPlan
from .projects import Project, StorageError, ConflictError, save_project_file, load_project_file


@dataclass(frozen=True)
class NewProjectIntent:
    name: str
    width: int
    height: int
    fps: Fraction
    duration: Fraction

    def __post_init__(self):
        if type(self.name) is not str or not self.name.strip() or len(self.name)>200:
            raise ValueError('Project name requires1..200characters')
        if any(type(x) is not int or not 1<=x<=16384 for x in (self.width,self.height)):
            raise ValueError('Creation UI geometry must be1..16384 pixels')
        for value in (self.fps,self.duration):
            if type(value) is not Fraction or value<=0 or value.numerator.bit_length()>128 or value.denominator.bit_length()>128:
                raise ValueError('Positive bounded exact project time required')
        if self.width%2 or self.height%2:
            raise ValueError('Initial yuv420p output intent requires even dimensions')


def empty_project(intent):
    if type(intent) is not NewProjectIntent:raise ValueError('Typed explicit project intent required')
    project_id=str(uuid.uuid4())
    def q(value):return [value.numerator,value.denominator]
    plan=CompositionPlan.parse({
        'schema_version':1,'evaluator_version':'eval-1','id':str(uuid.uuid4()),'revision':0,
        'output':{'width':intent.width,'height':intent.height,'fps':q(intent.fps),'duration':q(intent.duration),
                  'sample_rate':48000,'channel_layout':'stereo','color_space':'bt709','pixel_format':'yuv420p',
                  'container':'mp4','video_codec':'h264','audio_codec':'aac'},
        'assets':[],'clips':[],'layers':[],'transitions':[],'fonts':[],
        'audio':{'clips':[],'master':{'normalization':'none','target_lufs':[-16,1],
                                     'target_peak_db':[-1,1],'limiter':False,'ducking':[]}},
        'seed':0,'algorithm_revision':'initial-empty-project-1',
        'provenance':{'project_id':project_id,'project_revision':0,'preset_id':None,
                      'preset_version':0,'preset_hash':None,'source_ids':[],'account_binding_ids':[]}})
    return Project(project_id,intent.name,plan)


class CreationCanceled(StorageError):pass
class CreationUnknown(StorageError):pass

@dataclass(frozen=True)
class CreatedProject:
    path: Path
    project: Project
    digest: str


def create_project_file(path, project, *, cancel=lambda:False, fault=lambda _:None):
    """Never retries or deletes a target; caller decides whether to activate it."""
    path=Path(path)
    if not path.is_absolute() or '\0' in str(path) or type(project) is not Project:
        raise ValueError('Absolute explicit destination and typed project required')
    # Validate before any filesystem operation and check cancellation once before
    # entering the shared writer. Once entered, cancellation is NOT rollback.
    validated=Project.parse(project.to_json())
    if cancel():raise CreationCanceled('Creation canceled before writer entry')
    try:
        digest=save_project_file(path,validated,expected_digest=None,fault=fault)
        observed,actual=load_project_file(path)
        if actual!=digest or observed.to_json()!=validated.to_json():
            raise CreationUnknown('Created project changed before confirmation')
        return CreatedProject(path,validated,digest)
    except ConflictError:raise # Shared writer classifies this before publication.
    except BaseException as exc:
        raise CreationUnknown('Project creation outcome unknown; inspect target, do not replay') from exc
