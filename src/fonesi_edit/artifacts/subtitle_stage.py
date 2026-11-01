"""Parse-only observations for owned subtitle staging, never job-success authority."""
from dataclasses import dataclass
from typing import Callable
import pysubs2
from .filesystem import Destination, StageReceipt, PublicationError
from fonesi_edit.subtitles.adapter import parse_subtitles
from fonesi_edit.subtitles.files import SubtitleCanceled


@dataclass(frozen=True)
class SubtitleStage:
    receipt: StageReceipt
    format: str
    encoding: str
    cue_count: int
    diagnostics: tuple[str,...]
    parser_version: str
    policy: str = 'subtitle-parse-only-v1'


class SubtitleStageCanceled(SubtitleCanceled):
    """A post-write cancellation retains its exact owned receipt for reconciliation."""
    def __init__(self,receipt:StageReceipt):
        super().__init__('Subtitle staging canceled; owned stage retained, no final published')
        self.receipt=receipt


def stage_subtitles(destination:Destination,data:bytes,format_:str,*,encoding='utf-8-sig',
                    cancel:Callable[[],bool]=lambda:False)->SubtitleStage:
    if cancel():raise SubtitleCanceled('Subtitle staging canceled before validation')
    document=parse_subtitles(data,format_,encoding=encoding)
    if cancel():raise SubtitleCanceled('Subtitle staging canceled before writing')
    receipt=destination.create_stage(data)
    # The parser and writer observed the same immutable bytes, not a reopened source.
    if receipt.sha256!=document.source_sha256 or receipt.size!=len(data):
        raise PublicationError('Staging observation does not match parsed bytes; stage retained')
    if cancel():raise SubtitleStageCanceled(receipt)
    return SubtitleStage(receipt,format_,encoding,len(document.cues),document.diagnostics,pysubs2.__version__)
