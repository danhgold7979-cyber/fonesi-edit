"""Ownership proof for narrow recovery; never infer ownership from a pathname alone."""
import json
import os
from pathlib import Path
import stat
import uuid
from fonesi_edit.fileio import read_bounded

class DatabaseOwnershipError(RuntimeError):pass


def receipt_path(path:Path)->Path:
    return path.with_name(path.name+'.fonesi-owner')


def owns_database(path:Path,application_id:int,schema_hash:str|tuple[str,...])->bool:
    receipt=receipt_path(path)
    try:
        info=receipt.lstat()
        if (not stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode) or
                getattr(info,'st_file_attributes',0)&getattr(stat,'FILE_ATTRIBUTE_REPARSE_POINT',0x400)):
            return False
        data=json.loads(read_bounded(receipt,4096))
        if set(data)!={'format','nonce','application_id','schema_hash','device','inode'}:return False
        if data['format']!='fonesi-db-owner-1' or str(uuid.UUID(data['nonce']))!=data['nonce']:return False
        current=path.stat()
        allowed=(schema_hash,) if isinstance(schema_hash,str) else schema_hash
        if data['schema_hash'] not in allowed:return False
        if (data['application_id'],data['device'],data['inode'])!=(application_id,current.st_dev,current.st_ino):return False
        with path.open('rb') as stream:header=stream.read(100)
        return (len(header)==100 and header[:16]==b'SQLite format 3\x00' and
                int.from_bytes(header[68:72],'big')==application_id)
    except (OSError,ValueError,TypeError,KeyError,AttributeError):
        return False


def register_database(path:Path,application_id:int,schema_hash:str,*,legacy_hashes:tuple[str,...]=()):
    """Call ONLY after application ID + complete expected schema validation/migration."""
    receipt=receipt_path(path)
    # Receipt records reviewed creation lineage, not current schema validity.
    # Caller must independently validate the complete current schema first.
    allowed=(schema_hash,*legacy_hashes)
    if receipt.exists() or receipt.is_symlink():
        if not owns_database(path,application_id,allowed):
            raise DatabaseOwnershipError('Existing DB ownership receipt is invalid/foreign; left untouched')
        return
    current=path.stat()
    data={'format':'fonesi-db-owner-1','nonce':str(uuid.uuid4()),'application_id':application_id,
          'schema_hash':schema_hash,'device':current.st_dev,'inode':current.st_ino}
    try:
        with receipt.open('x',encoding='utf-8',newline='\n') as stream:
            json.dump(data,stream,sort_keys=True);stream.flush();os.fsync(stream.fileno())
    except FileExistsError:
        if not owns_database(path,application_id,allowed):
            raise DatabaseOwnershipError('Concurrent/foreign ownership receipt; retry safely')
    if not owns_database(path,application_id,allowed):
        raise DatabaseOwnershipError('DB identity changed during ownership registration')
