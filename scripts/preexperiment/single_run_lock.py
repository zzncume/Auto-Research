"""Operator lock component; future launcher must hold it until all children stop.

Not a launcher and not proof of production process cleanup. Never unlink a lock
file: replacing its inode would let two callers acquire different locks.
"""
from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import stat


@contextmanager
def single_run_lock(path):
    path = Path(path).absolute()
    if path.parent.resolve(strict=True) != path.parent:
        raise ValueError('operator lock parent must be symlink-free')
    fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    try:
        metadata = os.fstat(fd)
        if not stat.S_ISREG(metadata.st_mode) or metadata.st_nlink != 1 or metadata.st_uid != os.getuid():
            raise ValueError('operator lock must be an owned regular file with one link')
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            raise RuntimeError('another run holds the lock; do not queue or start a second run') from None
        yield
    finally:
        os.close(fd)
