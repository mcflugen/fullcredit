from __future__ import annotations

from collections.abc import Iterable

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
