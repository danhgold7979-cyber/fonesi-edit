"""Owned required-set staging and atomic prepare/claim; no job-success API yet."""
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


class PublicationSession:
    def __init__(self,repository,ownership,job):
        if ownership.repository is not repository:raise JobConflict('Coordinator belongs to another repository')
        ownership.guard()
        self.repository=repository;self.ownership=ownership;self.job=job
        self.manifest=repository.publication_manifest(job)
        self._stack=ExitStack();self._destinations={};self._staged={}
        self._closed=False;self._set_id=None;self._claimed=False
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
            self._guard_worker()
        except BaseException:self.close();raise

    def __enter__(self):return self
    def __exit__(self,*args):self.close()
    def close(self):self._closed=True;self._stack.close()

    def _guard_worker(self):
        if self._closed:raise JobConflict('Publication session closed')
        self.ownership.guard()
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
        return found,self._destinations[found.destination_root]

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
        return self.job
