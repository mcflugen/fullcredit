import pytest

from fullcredit.api import build_author_collection
from fullcredit.api import collect_git_commit_counts
from fullcredit.api import collect_git_contributors
from fullcredit.api import merge_authors
from fullcredit.authors import AuthorCollection


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


class TestCollectGitContributors:
    def test_basic(self, mock_git_log):
        mock_git_log.stdout = (
            " Graham Chapman \0 graham@example.com \n"
            "John Cleese\0john@example.com\n"
            "Graham Chapman\0graham@example.com\n"
        )
        assert collect_git_contributors("foobar") == {
            ("Graham Chapman", "graham@example.com"),
            ("John Cleese", "john@example.com"),
        }

    def test_strips_whitespace(self, mock_git_log):
        mock_git_log.stdout = " Graham Chapman \0 graham@example.com \n"
        assert collect_git_contributors("foobar") == {
            ("Graham Chapman", "graham@example.com")
        }

    def test_deduplicates(self, mock_git_log):
        mock_git_log.stdout = (
            "Graham Chapman\0graham@example.com\n"
            "Graham Chapman\0graham@example.com\n"
        )
        assert len(collect_git_contributors("foobar")) == 1

    def test_empty_log(self, mock_git_log):
        mock_git_log.stdout = ""
        assert collect_git_contributors("foobar") == set()

    def test_skips_blank_lines(self, mock_git_log):
        mock_git_log.stdout = (
            "Graham Chapman\0graham@example.com\n\nJohn Cleese\0john@example.com\n"
        )
        assert len(collect_git_contributors("foobar")) == 2


class TestCollectGitCommitCounts:
    def test_counts_commits_per_author(self, mock_git_log):
        mock_git_log.stdout = "Graham Chapman\nJohn Cleese\nGraham Chapman\n"
        counts = collect_git_commit_counts("foobar")
        assert counts["Graham Chapman"] == 2
        assert counts["John Cleese"] == 1

    def test_empty_log(self, mock_git_log):
        mock_git_log.stdout = ""
        assert collect_git_commit_counts("foobar") == {}


class TestBuildAuthorCollection:
    def test_basic(self):
        coll = build_author_collection([("Graham Chapman", "graham@example.com")])
        assert len(coll) == 1
        assert "Graham Chapman" in coll

    def test_empty(self):
        assert len(build_author_collection([])) == 0

    def test_deduplicates_by_name(self):
        coll = build_author_collection(
            [
                ("Graham Chapman", "graham@example.com"),
                ("Graham Chapman", "graham@work.com"),
            ]
        )
        assert len(coll) == 1

    def test_deduplicates_by_email(self):
        coll = build_author_collection(
            [
                ("Graham Chapman", "graham@example.com"),
                ("G. Chapman", "graham@example.com"),
            ]
        )
        assert len(coll) == 1

    def test_merges_alternate_emails(self):
        coll = build_author_collection(
            [
                ("Graham Chapman", "graham@example.com"),
                ("Graham Chapman", "graham@work.com"),
            ]
        )
        assert "graham@work.com" in coll.find_author("Graham Chapman").emails


class TestMergeAuthors:
    def test_merges_distinct_collections(self):
        a = AuthorCollection()
        a.add("Graham Chapman", "graham@example.com")
        b = AuthorCollection()
        b.add("John Cleese", "john@example.com")
        assert len(merge_authors([a, b])) == 2

    def test_merges_overlapping_by_email(self):
        a = AuthorCollection()
        a.add("Graham Chapman", "graham@example.com")
        b = AuthorCollection()
        b.add("G. Chapman", "graham@example.com")
        assert len(merge_authors([a, b])) == 1

    def test_empty_sequence(self):
        assert len(merge_authors([])) == 0

    def test_single_collection(self):
        a = AuthorCollection()
        a.add("Graham Chapman", "graham@example.com")
        assert len(merge_authors([a])) == 1

    def test_is_commutative(self):
        a = AuthorCollection()
        a.add("Graham Chapman", "graham@example.com")
        b = AuthorCollection()
        b.add("John Cleese", "john@example.com")
        names_ab = {author.name for author in merge_authors([a, b])}
        names_ba = {author.name for author in merge_authors([b, a])}
        assert names_ab == names_ba
