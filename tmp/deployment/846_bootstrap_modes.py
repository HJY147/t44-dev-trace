"""Public checkout modes only: local Git fixtures, no bootstrap/cloud/service execution."""

import os
import stat
import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[2] / "deployment/ubuntu24-bootstrap.sh"
BEGIN = "# T44_PUBLIC_TRACKED_MODES_BEGIN\n"
END = "# T44_PUBLIC_TRACKED_MODES_END"


def git(root: Path, *arguments: str) -> str:
    result = subprocess.run(["git", "-C", str(root), *arguments], capture_output=True,
                            text=True, check=True, timeout=10)
    return result.stdout.strip()


def normalizer():
    text = SCRIPT.read_text()
    if BEGIN not in text:
        # The original source stage has no post-checkout mode normalization.
        return lambda root, expected: None
    code = text.split(BEGIN, 1)[1].split(END, 1)[0]
    namespace = {"__name__": "bootstrap_mode_guard"}
    exec(compile(code, "<bootstrap-mode-logic>", "exec"), namespace)
    return namespace["canonical_modes"]


def mode(path: Path) -> int:
    return stat.S_IMODE(path.lstat().st_mode)


@pytest.fixture
def checkout(tmp_path):
    origin = (tmp_path / "origin").resolve()
    origin.mkdir()
    git(origin, "init", "--quiet")
    for name, content in {"README.md": "public\n", "backend/t44/cli.py": "public = True\n",
                          "nginx/nginx.conf": "events {}\n", "bin/run.sh": "#!/bin/sh\n"}.items():
        target = origin / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content)
        target.chmod(0o755 if name.endswith(".sh") else 0o644)
    git(origin, "add", "--", "README.md", "backend", "nginx", "bin")
    git(origin, "-c", "user.name=Synthetic Guard", "-c", "user.email=guard@example.invalid",
        "commit", "--quiet", "-m", "public fixture")
    root = (tmp_path / "checkout").resolve()
    previous = os.umask(0o077)
    try:
        subprocess.run(["git", "clone", "--quiet", "--local", "--no-hardlinks", str(origin), str(root)],
                       capture_output=True, check=True, timeout=10)
    finally:
        os.umask(previous)
    (root / ".env").write_text("SYNTHETIC_ONLY=private\n")
    (root / ".env").chmod(0o600)
    (root / ".git/private-marker").write_text("private synthetic metadata\n")
    (root / ".git/private-marker").chmod(0o600)
    (root / "private-runtime").mkdir(mode=0o700)
    (root / "private-runtime/keep").write_text("private synthetic runtime\n")
    (root / "private-runtime/keep").chmod(0o600)
    return root, git(root, "rev-parse", "HEAD")


def test_umask_checkout_public_modes(checkout):
    root, head = checkout
    assert mode(root / "backend/t44/cli.py") == 0o600
    assert mode(root / "backend/t44") == 0o700
    normalizer()(root, head)
    assert mode(root / "backend/t44/cli.py") == 0o644
    assert mode(root / "nginx/nginx.conf") == 0o644
    assert mode(root / "bin/run.sh") == 0o755
    assert mode(root / "backend/t44") == 0o755
    assert mode(root) == 0o750
    git(root, "diff", "--quiet", "HEAD", "--")


def test_private_files_git_and_untracked_unchanged(checkout):
    root, head = checkout
    names = [".env", ".git/private-marker", "private-runtime/keep"]
    before = {name: ((root / name).read_bytes(), (root / name).lstat()) for name in names}
    normalizer()(root, head)
    for name, (data, metadata) in before.items():
        assert (root / name).read_bytes() == data
        assert (root / name).lstat() == metadata
        assert mode(root / name) == 0o600
    assert mode(root / "private-runtime") == 0o700
    assert mode(root / ".git") == 0o700


def test_wrong_head_refused_without_chmod(checkout):
    root, _ = checkout
    with pytest.raises(ValueError, match="HEAD"):
        normalizer()(root, "0" * 40)
    assert mode(root / "backend/t44/cli.py") == 0o600


def test_dirty_bytes_refused_without_chmod(checkout):
    root, head = checkout
    (root / "README.md").write_text("dirty\n")
    with pytest.raises(subprocess.CalledProcessError):
        normalizer()(root, head)
    assert mode(root / "backend/t44/cli.py") == 0o600


def test_private_env_mode_not_repaired_or_published(checkout):
    root, head = checkout
    (root / ".env").chmod(0o640)
    with pytest.raises(ValueError, match="private"):
        normalizer()(root, head)
    assert mode(root / ".env") == 0o640
    assert mode(root / "README.md") == 0o600


def test_hardlink_to_private_env_refused_before_chmod(checkout):
    root, head = checkout
    (root / ".env").write_bytes((root / "README.md").read_bytes())
    (root / "README.md").unlink()
    os.link(root / ".env", root / "README.md")
    with pytest.raises(ValueError, match="public_file"):
        normalizer()(root, head)
    assert mode(root / ".env") == 0o600


def test_tracked_symlink_mode_refused(checkout):
    root, _ = checkout
    (root / "link").symlink_to("README.md")
    git(root, "add", "--", "link")
    git(root, "-c", "user.name=Synthetic Guard", "-c", "user.email=guard@example.invalid",
        "commit", "--quiet", "-m", "unsupported mode fixture")
    with pytest.raises(ValueError, match="Git_mode"):
        normalizer()(root, git(root, "rev-parse", "HEAD"))
    assert mode(root / "README.md") == 0o600
