"""Conservative abandoned-publication quarantine, never filesystem recovery.

A newly acquired coordinator cannot authenticate old retained-file incarnations.
This API preserves files/history and prevents treating persisted hashes as authority.
"""
from dataclasses import dataclass
import uuid

from fonesi_edit.domain.composition import canonical
from .repository import JobConflict


@dataclass(frozen=True)
class RecoveryHold:
    set_id: str
    job_id: str
    roles: tuple[str,...]
    code: str='OWNERSHIP_UNKNOWN'


def quarantine_abandoned(repository,ownership,set_id):
    """Classify one prior coordinator's incomplete set; no resume/retry/delete.

    Job and set retain their preexisting validating/publishing and prepared/claimed
    states. In particular this is NOT blocked_configuration: its ordinary resume
    path must never make an unresolved publication eligible for a new worker.
    """
    if ownership.repository is not repository:raise JobConflict('Coordinator belongs to another repository')
    try:
        if type(set_id) is not str or str(uuid.UUID(set_id))!=set_id:raise ValueError
    except (ValueError,AttributeError):raise JobConflict('Canonical required-set ID required') from None
    ownership.guard()
    db=repository.db;db.execute('BEGIN IMMEDIATE')
    try:
        ownership.guard()
        row=db.execute('SELECT * FROM artifact_sets WHERE id=?',(set_id,)).fetchone()
        if row is None or row['coordinator_epoch']>=ownership.epoch or row['state'] not in {'prepared','claimed'}:
            raise JobConflict('Prior coordinator incomplete set required')
        job=repository.get(row['job_id'])
        expected_state='validating' if row['state']=='prepared' else 'publishing'
        if (job.state!=expected_state or job.snapshot_hash!=row['snapshot_hash'] or
            job.attempt!=row['attempt'] or job.lease_token!=row['lease_token'] or
            row['version']!=(1 if row['state']=='prepared' else 2)):
            raise JobConflict('Abandoned set differs from immutable job attempt')
        manifest=repository.publication_manifest(job)
        roles=tuple(sorted(item.role for item in manifest.items))
        members=db.execute('SELECT * FROM publications WHERE set_id=?',(set_id,)).fetchall()
        if (row['roles_json']!=canonical(list(roles)) or len(members)!=len(roles) or
            {member['role'] for member in members}!=set(roles) or
            db.execute('SELECT 1 FROM completion_history WHERE set_id=? OR job_id=?',(set_id,job.id)).fetchone()):
            raise JobConflict('Abandoned member/history identity changed')
        definitions={item.role:item for item in manifest.items}
        allowed={'prepared','unknown'} if row['state']=='prepared' else {'claimed','committed','unknown'}
        for member in members:
            definition=definitions[member['role']]
            if (member['state'] not in allowed or member['destination_root']!=definition.destination_root or
                member['final_name']!=definition.final_name):
                raise JobConflict('Abandoned member identity changed')
        # Deliberately do not inspect, adopt, unlink or hash any filesystem object.
        # Already committed member records remain historical observations only;
        # they cannot establish complete-set success without new trusted recovery.
        db.execute("UPDATE publications SET state='unknown',version=version+1 WHERE set_id=? AND state IN ('prepared','claimed')",(set_id,))
        ownership.guard()
        db.execute('COMMIT')
    except BaseException:
        if db.in_transaction:db.execute('ROLLBACK')
        raise
    return RecoveryHold(set_id,job.id,roles)
