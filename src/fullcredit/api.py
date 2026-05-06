from __future__ import annotations

from fullcredit._git import GitLog


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
