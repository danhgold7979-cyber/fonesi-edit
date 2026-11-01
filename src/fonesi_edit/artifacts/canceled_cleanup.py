"""Delete only live exclusive-created canceled staging, never source/final paths."""
import os
from .filesystem import PublicationError,PublicationUnknown,_plain
from .windows_cleanup import DeleteCapability


def cleanup_canceled_stage(destination,owned,*,before_effect):
    if os.name!='nt':raise PublicationError('Safe canceled cleanup unavailable; staging retained')
    destination._check()
    if destination._created.get(owned.directory) is not owned or owned.root_identity!=destination.identity:
        raise PublicationUnknown('Canceled cleanup requires original live creation record')
    original=destination._anchors.get(owned.directory)
    directory=destination._directory_anchors.get(owned.directory)
    if (original is None or original.fd is None or directory is None or directory.fd is None
        or _plain(os.fstat(original.fd))!=owned.file_identity
        or _plain(os.fstat(directory.fd),True)!=owned.directory_identity):
        raise PublicationUnknown('Canceled cleanup lost original object incarnation')
    stage=destination.root/owned.directory
    with DeleteCapability(stage/'payload',original.fd,original.close,parent_identity=owned.directory_identity) as capability:
        if capability.identity!=owned.file_identity:raise PublicationUnknown('Canceled payload changed')
        capability.mark(before_effect=before_effect)
    if os.path.lexists(stage/'payload'):raise PublicationUnknown('Canceled payload retirement not observed')
    with DeleteCapability(stage,directory.fd,directory.close,parent_identity=destination.identity,directory=True) as capability:
        if capability.identity!=owned.directory_identity:raise PublicationUnknown('Canceled directory changed')
        capability.mark(before_effect=before_effect)
    if os.path.lexists(stage):raise PublicationUnknown('Canceled directory retirement not observed')
    before_effect()
