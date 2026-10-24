"""One-time byte transport of four explicitly sealed evidence files; no decryption."""
import hashlib
import io
import json
import os
import pwd
import stat
import tarfile
from pathlib import Path

SOURCE = Path('/var/lib/t44accept852/852_exports')
DESTINATION = Path('/run/t44-relay852/841-two-run-sealed-evidence.tar')
FILES = (
    ('852_sut_round841_flow_v1.enc', 3424800, '1e4274fe0c7d0f2bdb2168d350baa7818dc1bf8e6d7fa1b23edf8d4903c152e5'),
    ('852_sut_round841_flow_v1.meta.json', None, '56884bfa31000b26a319beb662a0a712ccfbb1d2f10ce19dee21bccb8a9f7898'),
    ('852_sut_round841_validation_v1.enc', 1308144, 'a89e35a535282adeb62ae2d613a18e72cc06e5465b299b7a0c206670a2e4ec9a'),
    ('852_sut_round841_validation_v1.meta.json', None, '388617521c3e3f465ac9669130ba1ffd86bb9ff73ef37ad247981562120ca928'),
)


def identity(s):
    return (s.st_dev, s.st_ino, s.st_mode, s.st_uid, s.st_gid, s.st_size,
            s.st_nlink, s.st_mtime_ns, s.st_ctime_ns)


def main():
    os.umask(0o077)
    assert os.geteuid() == 0
    user = pwd.getpwnam('t44accept852')
    for directory, owner in ((SOURCE, user.pw_uid), (DESTINATION.parent, 0)):
        s = directory.lstat()
        assert directory.resolve() == directory and stat.S_ISDIR(s.st_mode)
        assert s.st_uid == owner and stat.S_IMODE(s.st_mode) == 0o700
    source_fd = os.open(SOURCE, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    output = io.BytesIO()
    with tarfile.open(fileobj=output, mode='w', format=tarfile.USTAR_FORMAT) as archive:
        for name, exact_size, expected in FILES:
            fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=source_fd)
            with os.fdopen(fd, 'rb') as stream:
                before = os.fstat(stream.fileno())
                limit = exact_size if exact_size is not None else 65536
                assert stat.S_ISREG(before.st_mode) and before.st_uid == user.pw_uid
                assert stat.S_IMODE(before.st_mode) == 0o600 and before.st_nlink == 1
                assert 0 < before.st_size <= limit
                data = stream.read(limit + 1)
                assert identity(before) == identity(os.fstat(stream.fileno()))
            assert len(data) == before.st_size
            assert exact_size is None or len(data) == exact_size
            assert hashlib.sha256(data).hexdigest() == expected
            info = tarfile.TarInfo(name)
            info.size, info.mode, info.mtime = len(data), 0o600, 0
            archive.addfile(info, io.BytesIO(data))
    os.close(source_fd)
    data = output.getvalue()
    assert len(data) < 6 * 1024 * 1024
    fd = os.open(DESTINATION, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, 'wb') as stream:
        assert stream.write(data) == len(data)
        stream.flush()
        os.fsync(stream.fileno())
    print(json.dumps({'opaque_transport_completed': True, 'file': str(DESTINATION),
                      'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(),
                      'members': len(FILES), 'decrypted_or_interpreted': False}))


if __name__ == '__main__':
    main()
