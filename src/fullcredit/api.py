from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from collections.abc import Sequence

from fullcredit._git import GitLog
from fullcredit.authors import AuthorCollection


def build_author_collection(identities: Iterable[tuple[str, str]]) -> AuthorCollection:
    authors = AuthorCollection()
    for name, email in identities:
        authors.add(name, email)

    return authors


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


def merge_authors(author_collections: Sequence[AuthorCollection]) -> AuthorCollection:
    merged = AuthorCollection()
    for author_collection in author_collections:
        merged.update(author_collection)
    return merged
