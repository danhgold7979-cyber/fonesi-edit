"""Best-effort typed observations; failure never replays a completed job command."""
from enum import Enum
import math
from fonesi_edit.storage.db_ownership import ownership_token
from .schema import APPLICATION_ID,KNOWN_LINEAGE_HASHES
from .events import Event
from .event_store import EventStore,EventRecord


class DiagnosticStatus(str,Enum):
    NOT_REQUESTED='NOT_REQUESTED'
    RECORDED='RECORDED'
    UNAVAILABLE='UNAVAILABLE'


def record_job_event(repo,owner,job,event,path):
    if path is None:return DiagnosticStatus.NOT_REQUESTED
    try:
        if owner.repository is not repo or type(event) is not Event:
            return DiagnosticStatus.UNAVAILABLE
        owner.guard()
        current=repo.get(job.id)
        if current!=job:return DiagnosticStatus.UNAVAILABLE
        token=ownership_token(repo.path,APPLICATION_ID,KNOWN_LINEAGE_HASHES)
        now=repo.clock()
        if type(now) not in (int,float) or not math.isfinite(now) or not 0<=now<(2**63-1)/1000:
            return DiagnosticStatus.UNAVAILABLE
        record=EventRecord(token,job.id,job.attempt,job.version,int(now*1000),event)
        with EventStore(path) as store:
            owner.guard()
            if repo.get(job.id)!=job or token!=ownership_token(repo.path,APPLICATION_ID,KNOWN_LINEAGE_HASHES):
                return DiagnosticStatus.UNAVAILABLE
            store.append(record)
        return DiagnosticStatus.RECORDED
    except Exception:
        # Never persist/re-emit exception text: it may contain paths or secrets.
        # Append/close may have had an unknown outcome. No append/job retry.
        return DiagnosticStatus.UNAVAILABLE
