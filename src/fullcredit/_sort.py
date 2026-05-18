from __future__ import annotations

import os
from functools import partial
from typing import Any
from typing import Protocol

from fullcredit.api import collect_git_commit_counts
from fullcredit.authors import Author


class AuthorSortKey(Protocol):
    def __call__(self, author: Author) -> Any: ...


def key_name(author: Author) -> str:
    return author.name.casefold()


def key_last_name(author: Author) -> tuple[str, str]:
    parts = author.name.split()
    if len(parts) > 1:
        return parts[-1].casefold(), parts[0].casefold()
    else:
        return author.name.casefold(), ""


def key_github(author: Author) -> str:
    return author._extras.get("github", "").casefold()


def key_commits(author: Author, *, counts: dict[str, int]) -> int:
    return -sum(counts.get(name, 0) for name in author.names)


_KEY_FUNCTIONS: dict[str, AuthorSortKey] = {
    "name": key_name,
    "last-name": key_last_name,
    "github": key_github,
}

SORT_KEYS = (*_KEY_FUNCTIONS, "commits")


def parse_key(key_str: str) -> AuthorSortKey:
    parts = key_str.split(":", 1)
    name = parts[0]
    arg = parts[1] if len(parts) > 1 else None

    if name not in SORT_KEYS:
        raise ValueError(f"unknown sort key: {key_str!r}")

    if name == "commits":
        if not arg:
            raise ValueError("'commits' key requires a repository: --key commits:REPO")
        counts = collect_git_commit_counts(os.path.expanduser(arg))
        return partial(key_commits, counts=counts)

    return _KEY_FUNCTIONS[name]
