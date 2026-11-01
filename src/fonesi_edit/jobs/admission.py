"""Live source/output namespace checks, not media/hash validation or restart authority."""
from contextlib import ExitStack
import os
from pathlib import Path

from fonesi_edit.artifacts.filesystem import Destination,PublicationConflict,PublicationUnknown,_plain


def _under(path,root):return path==root or root in path.parents


def _signature(info):return (_plain(info),info.st_size,info.st_mtime_ns,info.st_ctime_ns)


class NamespaceAdmission:
    """Coordinator-owned pins; every source must already have an absolute snapshot path.

    Cache roots are explicit trusted coordinator configuration, not untrusted project
    authority. Missing cache configuration is not proof that every cache was excluded.
    No handles are exposed to workers; synchronous callers must serialize operations.
    """
    def __init__(self,composition,destinations,manifest,*,cache_roots=()):
        self._stack=ExitStack();self._closed=False;self._revoked=False
        self._sources=[];self._parents={};self._destinations=destinations;self.manifest=manifest
        if type(cache_roots) is not tuple or len(cache_roots)>128:
            raise PublicationConflict('Bounded explicit cache roots required')
        try:
            self._caches=[self._stack.enter_context(Destination(root)) for root in cache_roots]
            for root in destinations.values():
                if any(_under(root.root,c.root) or _under(c.root,root.root) or root.identity==c.identity for c in self._caches):
                    raise PublicationConflict('Output overlaps a configured cache namespace')
            for item in (*composition['assets'],*composition['fonts']):
                ref=item['path_ref'];path=Path(ref['path'])
                if ref['base']!='absolute' or not path.is_absolute() or '..' in path.parts:
                    raise PublicationConflict('Resolve project-relative sources into the immutable execution snapshot before publication')
                if any(part.startswith('.fonesi-stage-') for part in path.parts) or any(_under(path,c.root) for c in self._caches):
                    raise PublicationConflict('Cache/staging inputs cannot enter publication admission')
                parent=self._parents.get(path.parent)
                if parent is None:
                    parent=self._parents[path.parent]=self._stack.enter_context(Destination(path.parent))
                before=parent._stat(path.name);_plain(before)
                fd=parent._open(path.name,os.O_RDONLY|getattr(os,'O_NONBLOCK',0))
                self._stack.callback(os.close,fd)
                signature=_signature(os.fstat(fd))
                named_signature=_signature(before)
                # Windows path-stat and fstat timestamps may have different precision.
                # Identity/size cross APIs; timestamps only against their own baseline.
                if signature[:2]!=named_signature[:2]:raise PublicationUnknown('Source changed during admission')
                self._sources.append((parent,path.name,fd,signature,named_signature))
            self.guard()
        except BaseException:self.close();raise

    def close(self):self._closed=True;self._stack.close()
    def __enter__(self):return self
    def __exit__(self,*args):self.close()

    def guard(self):
        if self._closed or self._revoked:raise PublicationUnknown('Source/output admission closed or permanently revoked')
        try:
            for root in (*self._destinations.values(),*self._caches,*self._parents.values()):root._check()
            for parent,name,fd,signature,named_signature in self._sources:
                if _signature(os.fstat(fd))!=signature or _signature(parent._stat(name))!=named_signature:
                    raise PublicationUnknown('Source identity/content observation changed since admission')
        except BaseException:
            self._revoked=True
            raise

    def guard_final(self,definition):
        self.guard()
        root=self._destinations[definition.destination_root]
        # Existing finals (including a hardlink to source or broken symlink) never
        # become an overwrite/adoption target, even if their bytes match.
        try:root._stat(definition.final_name)
        except FileNotFoundError:return
        raise PublicationConflict('Final/source collision; existing path left untouched')

    @property
    def excluded_roots(self):
        self.guard()
        return tuple(dict.fromkeys([x.root for x in self._destinations.values()]+[x.root for x in self._caches]))
