"""Live-coordinator required-set publication; restart reconciliation stays UNKNOWN."""
from contextlib import ExitStack
from dataclasses import asdict
from hashlib import sha256
import json
import os
from pathlib import Path
import uuid

from fonesi_edit.artifacts.filesystem import Destination,PublicationConflict
from fonesi_edit.artifacts.subtitle_stage import stage_subtitles
from fonesi_edit.subtitles.adapter import MAX_BYTES
from fonesi_edit.media.validation import validate_media
from fonesi_edit.domain.composition import canonical
from .repository import JobConflict
from .admission import NamespaceAdmission
from fonesi_edit.media.discovery import scan_media


class PublicationSession:
    def __init__(self,repository,ownership,job,*,cache_roots=()):
        if ownership.repository is not repository:raise JobConflict('Coordinator belongs to another repository')
        ownership.guard()
        self.repository=repository;self.ownership=ownership;self.job=job
        self.manifest=repository.publication_manifest(job)
        self._stack=ExitStack();self._destinations={};self._staged={}
        self._closed=False;self._set_id=None;self._claimed=False
        self._linked=set();self._claim_token=None;self._admission=None
        try:
            reservations=set()
            for definition in self.manifest.items:
                root=definition.destination_root
                if root not in self._destinations:self._destinations[root]=self._stack.enter_context(Destination(root))
                destination=self._destinations[root]
                key=(destination.identity,definition.final_name.casefold())
                if key in reservations:raise PublicationConflict('Required outputs alias the same destination')
                reservations.add(key)
                if os.path.lexists(destination.root/definition.final_name):
                    raise PublicationConflict('Existing destination is never adopted')
            self._admission=self._stack.enter_context(NamespaceAdmission(
                json.loads(job.snapshot_json)['composition'],self._destinations,self.manifest,cache_roots=cache_roots))
            self._guard_worker()
        except BaseException:self.close();raise

    def __enter__(self):return self
    def __exit__(self,*args):self.close()
    def close(self):self._closed=True;self._stack.close()

    def _guard_worker(self):
        if self._closed:raise JobConflict('Publication session closed')
        self.ownership.guard()
        if self._admission is not None:self._admission.guard()
        current=self.repository.get(self.job.id)
        if (current.snapshot_hash!=self.job.snapshot_hash or current.attempt!=self.job.attempt or
            current.lease_token!=self.job.lease_token or current.state!='validating' or
            current.cancel_requested or current.lease_deadline is None or self.repository.clock()>=current.lease_deadline):
            raise JobConflict('Publication requires current uncanceled validating worker lease')
        return current

    def _definition(self,role,kind):
        self._guard_worker()
        if type(role) is not str:raise JobConflict('Explicit artifact role required')
        if self._set_id is not None or role in self._staged:raise JobConflict('Role already staged or set frozen')
        found=next((item for item in self.manifest.items if item.role==role),None)
        if found is None or found.kind!=kind:raise JobConflict('Unknown or mismatched required role')
        self._admission.guard_final(found)
        return found,self._destinations[found.destination_root]

    def scan_sources(self,root,*,cancel=lambda:False,**limits):
        self._guard_worker()
        rows=self.repository.db.execute('SELECT final_identity_json FROM artifacts LIMIT 100001').fetchall()
        if len(rows)>100000:raise JobConflict('Artifact exclusion budget exceeded; choose a bounded index scope')
        identities=tuple(tuple(json.loads(row[0])) for row in rows)
        result=scan_media(root,excluded_roots=self._admission.excluded_roots,
                          excluded_file_ids=identities,cancel=cancel,**limits)
        self._guard_worker()
        return result

    def stage_subtitle(self,role,data,*,cancel=lambda:False):
        definition,destination=self._definition(role,'subtitle')
        if type(data) is not bytes or len(data)>MAX_BYTES or sha256(data).hexdigest()!=definition.subtitle_sha256:
            raise JobConflict('Subtitle bytes differ from immutable output policy')
        staged=stage_subtitles(destination,data,definition.subtitle_format,
                               encoding=definition.subtitle_encoding,cancel=cancel)
        self._guard_worker()
        observation={'policy':staged.policy,'parser_version':staged.parser_version,
                     'format':staged.format,'encoding':staged.encoding,'cue_count':staged.cue_count,
                     'diagnostics':list(staged.diagnostics),'sha256':staged.receipt.sha256}
        self._staged[role]=(staged.receipt,observation)

    def stage_media(self,role,source,ffprobe,ffmpeg,*,cancel=lambda:False,timeout=300):
        definition,destination=self._definition(role,'media')
        receipt=destination.copy_stage(source,cancel=cancel)
        path=destination.root/receipt.directory/'payload'
        validation=validate_media(path,ffprobe,ffmpeg,definition.expected_streams,cancel=cancel,timeout=timeout)
        if validation.sha256!=receipt.sha256:raise JobConflict('Validated media differs from owned stage')
        self._guard_worker()
        self._staged[role]=(receipt,{'policy':validation.policy,'sha256':validation.sha256})

    def _verify_stages(self):
        if set(self._staged)!={item.role for item in self.manifest.items}:
            raise JobConflict('Required artifact set incomplete')
        for definition in self.manifest.items:
            destination=self._destinations[definition.destination_root]
            receipt,_=self._staged[definition.role]
            # Reuse exact live-anchor/content verification; no serialized authority.
            destination._receipt(receipt)
            with destination._stage_directory(receipt.directory,receipt.directory_identity) as fd:
                destination._verify(receipt,'payload' if fd is not None else receipt.directory+'/payload',fd)

    def prepare(self):
        self._guard_worker()
        if self._set_id is not None:raise JobConflict('Set already prepared')
        self._verify_stages() # slow readback outside SQLite write transaction
        db=self.repository.db;set_id=str(uuid.uuid4())
        db.execute('BEGIN IMMEDIATE')
        try:
            current=self._guard_worker()
            db.execute('INSERT INTO artifact_sets VALUES(?,?,?,?,?,?,?,\'prepared\',1)',
                       (set_id,current.id,current.snapshot_hash,current.attempt,current.lease_token,
                        self.ownership.epoch,canonical(sorted(self._staged))))
            for definition in self.manifest.items:
                receipt,validation=self._staged[definition.role]
                db.execute('INSERT INTO publications VALUES(?,?,?,?,?,?,?,\'prepared\',1)',
                           (str(uuid.uuid4()),set_id,definition.role,definition.destination_root,
                            definition.final_name,canonical(asdict(receipt)),canonical(validation)))
            db.execute('COMMIT')
        except BaseException:
            if db.in_transaction:db.execute('ROLLBACK')
            raise
        self.job=current;self._set_id=set_id
        return set_id

    def claim(self):
        self._guard_worker()
        if self._set_id is None or self._claimed:raise JobConflict('Prepared unclaimed set required')
        self._verify_stages()
        db=self.repository.db;db.execute('BEGIN IMMEDIATE')
        try:
            current=self._guard_worker()
            row=db.execute('SELECT * FROM artifact_sets WHERE id=?',(self._set_id,)).fetchone()
            members=db.execute('SELECT * FROM publications WHERE set_id=?',(self._set_id,)).fetchall()
            if (row is None or row['job_id']!=current.id or row['version']!=1 or row['state']!='prepared' or row['coordinator_epoch']!=self.ownership.epoch or
                row['snapshot_hash']!=current.snapshot_hash or row['attempt']!=current.attempt or row['lease_token']!=current.lease_token or
                json.loads(row['roles_json'])!=sorted(self._staged) or len(members)!=len(self._staged) or
                {r['role'] for r in members}!=set(self._staged) or any(r['state']!='prepared' or r['version']!=1 for r in members)):
                raise JobConflict('Prepared required-set identity changed')
            definitions={item.role:item for item in self.manifest.items}
            for member in members:
                definition=definitions[member['role']];receipt,validation=self._staged[member['role']]
                if (member['destination_root']!=definition.destination_root or member['final_name']!=definition.final_name or
                    member['staging_receipt_json']!=canonical(asdict(receipt)) or member['validation_json']!=canonical(validation)):
                    raise JobConflict('Prepared member differs from retained owned observation')
            claimed_job=self.repository._update(current,'publishing',lease=current.lease_token,
                                             deadline=current.lease_deadline)
            db.execute("UPDATE artifact_sets SET state='claimed',version=version+1 WHERE id=?",(self._set_id,))
            db.execute("UPDATE publications SET state='claimed',version=version+1 WHERE set_id=?",(self._set_id,))
            db.execute('COMMIT')
        except BaseException:
            if db.in_transaction:db.execute('ROLLBACK')
            raise
        self.job=claimed_job
        self._claimed=True
        self._claim_token=claimed_job.lease_token
        return self.job

    def _guard_claimed(self, *, completed=False):
        if self._closed or not self._claimed:raise JobConflict('Live claimed session required')
        self.ownership.guard()
        if self._admission is not None:self._admission.guard()
        current=self.repository.get(self.job.id)
        expected_version=self.job.version+(current.state=='succeeded' and self.job.state!='succeeded')
        if (current.snapshot_hash!=self.job.snapshot_hash or current.attempt!=self.job.attempt or
            current.version!=expected_version or current.cancel_requested or
            current.state not in ({'publishing','succeeded'} if completed else {'publishing'}) or
            (current.state=='publishing' and current.lease_token!=self.job.lease_token)):
            raise JobConflict('Claimed job identity changed')
        # Worker deadline no longer grants authority after the atomic claim.
        return current

    def _journal(self,current):
        db=self.repository.db
        row=db.execute('SELECT * FROM artifact_sets WHERE id=?',(self._set_id,)).fetchone()
        done=current.state=='succeeded'
        if (row is None or row['job_id']!=current.id or row['snapshot_hash']!=current.snapshot_hash or
            row['attempt']!=current.attempt or row['lease_token']!=self._claim_token or
            row['coordinator_epoch']!=self.ownership.epoch or
            row['roles_json']!=canonical(sorted(self._staged)) or
            row['state']!=('committed' if done else 'claimed') or row['version']!=(3 if done else 2)):
            raise JobConflict('Claimed required-set identity changed')
        members=db.execute('SELECT * FROM publications WHERE set_id=?',(self._set_id,)).fetchall()
        if len(members)!=len(self._staged) or {m['role'] for m in members}!=set(self._staged):
            raise JobConflict('Required member set changed')
        definitions={item.role:item for item in self.manifest.items}
        for member in members:
            definition=definitions[member['role']];receipt,validation=self._staged[member['role']]
            if (member['destination_root']!=definition.destination_root or member['final_name']!=definition.final_name or
                member['staging_receipt_json']!=canonical(asdict(receipt)) or member['validation_json']!=canonical(validation) or
                member['state'] not in {'claimed','committed'} or member['version']!=(3 if member['state']=='committed' else 2)):
                raise JobConflict('Claimed member differs from retained observation')
            artifact=db.execute('SELECT * FROM artifacts WHERE publication_id=?',(member['id'],)).fetchone()
            if member['state']=='committed':
                if (artifact is None or artifact['final_identity_json']!=canonical(list(receipt.file_identity)) or
                    artifact['sha256']!=receipt.sha256 or artifact['size']!=receipt.size):
                    raise JobConflict('Committed artifact differs from retained observation')
            elif artifact is not None:raise JobConflict('Uncommitted member has artifact record')
        return {member['role']:member for member in members}

    def publish_member(self,role):
        current=self._guard_claimed();members=self._journal(current)
        if type(role) is not str or role not in members:raise JobConflict('Unknown required role')
        definition=next(item for item in self.manifest.items if item.role==role)
        destination=self._destinations[definition.destination_root];receipt,_=self._staged[role]
        if role not in self._linked:
            # Record authority only AFTER no-replace link, flush and live readback
            # returned successfully. Uncertain filesystem errors remain fail-closed.
            def before_link():
                self._journal(self._guard_claimed())
                self._admission.guard_final(definition)
            destination.publish(receipt,definition.final_name,before_link=before_link)
            self._linked.add(role)
        else:destination.verify_published(receipt,definition.final_name)
        db=self.repository.db;db.execute('BEGIN IMMEDIATE')
        try:
            current=self._guard_claimed();member=self._journal(current)[role]
            if member['state']=='claimed':
                db.execute('INSERT INTO artifacts VALUES(?,?,?,?,?)',
                           (member['id'],canonical(list(receipt.file_identity)),receipt.sha256,receipt.size,self.repository.clock()))
                db.execute("UPDATE publications SET state='committed',version=version+1 WHERE id=?",(member['id'],))
            db.execute('COMMIT')
        except BaseException:
            if db.in_transaction:db.execute('ROLLBACK')
            raise
        return destination.root/definition.final_name

    def finish(self):
        current=self._guard_claimed(completed=True);members=self._journal(current)
        if any(member['state']!='committed' for member in members.values()) or self._linked!=set(members):
            raise JobConflict('Every required artifact must be committed by this live session')
        # Slow content readback stays outside the SQLite write transaction.
        for definition in self.manifest.items:
            receipt,_=self._staged[definition.role]
            self._destinations[definition.destination_root].verify_published(receipt,definition.final_name)
        db=self.repository.db;db.execute('BEGIN IMMEDIATE')
        try:
            current=self._guard_claimed(completed=True);members=self._journal(current)
            if any(member['state']!='committed' for member in members.values()):raise JobConflict('Required artifact no longer committed')
            history=db.execute('SELECT * FROM completion_history WHERE set_id=?',(self._set_id,)).fetchone()
            if current.state=='succeeded':
                if history is None or history['job_id']!=current.id or history['snapshot_hash']!=current.snapshot_hash:
                    raise JobConflict('Completion identity changed')
                finished=current
            else:
                if history is not None:raise JobConflict('Unexpected completion history')
                finished=self.repository._update(current,'succeeded')
                db.execute("UPDATE artifact_sets SET state='committed',version=version+1 WHERE id=?",(self._set_id,))
                db.execute('INSERT INTO completion_history VALUES(?,?,?,?)',
                           (self._set_id,current.id,current.snapshot_hash,self.repository.clock()))
            db.execute('COMMIT')
        except BaseException:
            if db.in_transaction:db.execute('ROLLBACK')
            raise
        self.job=finished
        return finished
