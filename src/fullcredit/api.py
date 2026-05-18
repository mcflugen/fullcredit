from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from collections.abc import Sequence

from fullcredit._git import GitLog
from fullcredit.authors import AuthorList


def build_author_list(identities: Iterable[tuple[str, str]]) -> AuthorList:
    author_list = AuthorList()
    for name, email in identities:
        author_list.add(name, email)

    return author_list


def collect_git_contributors(
    repo: str | None = None, *, revspec: str | None = None
) -> set[tuple[str, str]]:
    git_log = GitLog("%an%x00%ae", repo=repo, revspec=revspec)

    name_and_email = set()
    for line in git_log.run().splitlines():
        if line:
            name, email = line.split("\0", maxsplit=1)
            name_and_email.add((name.strip(), email.strip()))

    return name_and_email


def collect_git_commit_counts(repo: str | None = None) -> Counter[str]:
    git_log = GitLog("%an", repo=repo)
    return Counter(git_log.run().splitlines())


def merge_authors(author_lists: Sequence[AuthorList]) -> AuthorList:
    merged = AuthorList()
    for author_list in reversed(author_lists):
        merged.update(author_list)
    return merged
