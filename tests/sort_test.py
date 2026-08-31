from unittest.mock import patch

import pytest

from fullcredit._sort import key_commits
from fullcredit._sort import key_github
from fullcredit._sort import key_last_name
from fullcredit._sort import key_name
from fullcredit._sort import parse_key
from fullcredit.authors import Author


def make_author(name, *, github=None):
    author = Author(name, f"{name.lower().replace(' ', '.')}@example.com")
    if github:
        author._extras["github"] = github
    return author


class TestKeyName:
    def test_returns_casefolded_name(self):
        assert key_name(make_author("Graham Chapman")) == "graham chapman"


class TestKeyLastName:
    def test_two_part_name(self):
        assert key_last_name(make_author("Graham Chapman")) == ("chapman", "graham")

    def test_single_part_name(self):
        assert key_last_name(make_author("Graham")) == ("graham", "")


class TestKeyGithub:
    def test_returns_casefolded_github(self):
        author = make_author("Graham Chapman", github="GrahamChapman")
        assert key_github(author) == "grahamchapman"

    def test_missing_github_returns_empty(self):
        assert key_github(make_author("Graham Chapman")) == ""


class TestKeyCommits:
    def test_returns_negative_commit_count(self):
        counts = {"Graham Chapman": 5}
        author = make_author("Graham Chapman")
        assert key_commits(author, counts=counts) == -5

    def test_sums_across_aliases(self):
        counts = {"Graham Chapman": 3, "G. Chapman": 2}
        author = Author("Graham Chapman", "graham@example.com", aliases=["G. Chapman"])
        assert key_commits(author, counts=counts) == -5

    def test_missing_author_returns_zero(self):
        author = make_author("Graham Chapman")
        assert key_commits(author, counts={}) == 0


class TestParseKey:
    def test_name(self):
        key = parse_key("name")
        assert key(make_author("Graham Chapman")) == "graham chapman"

    def test_last_name(self):
        key = parse_key("last-name")
        assert key(make_author("Graham Chapman")) == ("chapman", "graham")

    def test_github(self):
        key = parse_key("github")
        author = make_author("Graham Chapman", github="grahamchapman")
        assert key(author) == "grahamchapman"

    def test_commits(self):
        with patch(
            "fullcredit._sort.collect_git_commit_counts",
            return_value={"Graham Chapman": 3},
        ):
            key = parse_key("commits:/some/repo")
            assert key(make_author("Graham Chapman")) == -3

    def test_commits_without_repo_raises(self):
        with pytest.raises(ValueError, match="commits"):
            parse_key("commits")

    def test_unknown_key_raises(self):
        with pytest.raises(ValueError, match="unknown sort key"):
            parse_key("bogus")
