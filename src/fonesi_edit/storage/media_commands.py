"""Pure completed library commands; file admission and P04 import UI are separate."""
from dataclasses import dataclass,replace
from fonesi_edit.domain.composition import CompositionPlan
from fonesi_edit.domain.media_library import MediaLibrary,MediaRecord
from .projects import Project
from .autosave import CompletedCommand

@dataclass(frozen=True)
class MediaAddition:
    media_id:str
    command:CompletedCommand|None


def add_media(project:Project,item:MediaRecord)->MediaAddition:
    library=MediaLibrary() if project.library is None else project.library
    updated,media_id,changed=library.add(item)
    if not changed:return MediaAddition(media_id,None)
    plan=project.plan.to_dict();revision=plan['revision'];plan['revision']+=1
    plan['provenance']['project_revision']=plan['revision']
    candidate=replace(project,plan=CompositionPlan.parse(plan),library=updated)
    return MediaAddition(media_id,CompletedCommand(candidate,revision))
