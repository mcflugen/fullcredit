import subprocess

import pytest

from fullcredit._git import FullcreditSubprocessError
from fullcredit._git import GitLog


@pytest.fixture
def git_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init"], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "graham@example.com"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.name", "Graham Chapman"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    (repo / "file.txt").write_text("hello")
    subprocess.run(["git", "add", "."], cwd=repo, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "initial commit"],
        cwd=repo,
        check=True,
        capture_output=True,
    )
    return repo


class TestGitLog:
    def test_run_returns_output(self, git_repo):
        log = GitLog("%an", repo=str(git_repo))
        result = log.run()
        assert isinstance(result, str)
        assert len(result) > 0

    def test_run_with_revspec(self, git_repo):
        log = GitLog("%H", repo=str(git_repo), revspec="HEAD^!")
        result = log.run()
        assert len(result.strip()) == 40  # single commit hash

    def test_run_failure_raises(self):
        log = GitLog("%an", repo="/nonexistent/path")
        with pytest.raises(FullcreditSubprocessError):
            log.run()

    def test_str(self, git_repo):
        log = GitLog("%an", repo=str(git_repo))
        s = str(log)
        assert "git" in s
        assert "--format=%an" in s

    def test_repr(self, git_repo):
        log = GitLog("%an", repo=str(git_repo))
        r = repr(log)
        assert r.startswith("GitLog(")
        assert "%an" in r
