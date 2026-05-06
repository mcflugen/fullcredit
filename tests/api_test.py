import pytest

from fullcredit.api import collect_git_contributors


@pytest.fixture
def mock_git_log(monkeypatch):
    class MockGitLog:
        stdout = ""

        def __init__(self, *args, **kwargs):
            pass

        def run(self):
            return self.stdout

    monkeypatch.setattr("fullcredit.api.GitLog", MockGitLog)
    return MockGitLog


def test_collect_git_contributors(mock_git_log):
    mock_git_log.stdout = (
        " Alice \0 alice@example.com \n"
        "Bob\0bob@example.com\n"
        "Alice\0alice@example.com\n"
    )

    assert collect_git_contributors("foobar") == {
        ("Alice", "alice@example.com"),
        ("Bob", "bob@example.com"),
    }
