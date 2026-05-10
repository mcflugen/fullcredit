from __future__ import annotations

import copy
import os
import re
from collections.abc import Iterable
from itertools import product
from typing import Any


class Author:
    def __init__(
        self,
        name: str,
        email: str,
        aliases: Iterable | None = None,
        alternate_emails: Iterable | None = None,
    ) -> None:
        self._name = name
        self._email = email
        self._aliases = set(aliases or ())
        self._alternate_emails = set(alternate_emails or ())
        self._aliases.discard(self.name)
        self._alternate_emails.discard(self.email)
        self._extras: dict[str, str] = {}

    def norm(self) -> Author:
        best_name = Author.choose_best_name(self.names)
        aliases = set(self.names) - {best_name}

        normed = Author(
            name=best_name,
            email=self.email,
            aliases=aliases,
            alternate_emails=self.alternate_emails,
        )
        normed._extras = copy.deepcopy(self._extras)

        return normed

    @staticmethod
    def choose_best_name(names: Iterable[str]) -> str:
        return max(names, key=score_name_for_display)

    @classmethod
    def from_dict(cls, attrs: dict[str, Any]) -> Author:
        attrs = dict(attrs)
        author = cls(
            attrs.pop("name"),
            attrs.pop("email"),
            aliases=attrs.pop("aliases", None),
            alternate_emails=attrs.pop("alternate_emails", None),
        )
        for k, v in attrs.items():
            author._extras[k] = v
        return author

    @classmethod
    def merge(cls, authors: Iterable[Author]) -> Author:
        authors = list(authors)

        if len(authors) == 0:
            raise ValueError("list of authors must have length > 0")

        all_names: set[str] = set()
        all_emails: set[str] = set()
        for author in authors:
            all_names.update(author.names)
            all_emails.update(author.emails)

        name = max(all_names, key=score_name_for_display)
        email = authors[0].email

        return cls(
            name=name,
            email=email,
            aliases=sorted(all_names - {name}),
            alternate_emails=sorted(all_emails - {email}),
        )

    @property
    def name(self) -> str:
        return self._name

    @property
    def names(self) -> tuple[str, ...]:
        return (self.name, *self.aliases)

    @property
    def email(self) -> str:
        return self._email

    @property
    def emails(self) -> tuple[str, ...]:
        return (self.email, *self.alternate_emails)

    @property
    def aliases(self) -> tuple[str, ...]:
        return tuple(sorted(self._aliases))

    @property
    def alternate_emails(self) -> tuple[str, ...]:
        return tuple(sorted(self._alternate_emails))

    @property
    def extras(self) -> tuple[tuple[str, Any], ...]:
        return tuple(sorted(self._extras.items()))

    def add_name(self, alias: str) -> None:
        if alias != self.name:
            self._aliases.add(alias)

    def add_email(self, email: str) -> None:
        if email != self.email:
            self._alternate_emails.add(email)

    def to_toml(self) -> str:
        lines = [
            "[[tool.fullcredit.author]]",
            _toml_kv("name", self.name),
            _toml_kv("email", self.email),
            _toml_array("aliases", self.aliases),
            _toml_array("alternate_emails", self.alternate_emails),
        ] + [_toml_kv(k, v) for k, v in self.extras]

        return os.linesep.join(lines)

    def update(self, other: Author) -> None:
        if other.name != self.name:
            self._aliases.add(other.name)
        if other.email != self.email:
            self._alternate_emails.add(other.email)

        self._aliases.update(other._aliases)
        self._alternate_emails.update(other._alternate_emails)
        self._extras.update(other._extras)

        self._aliases.discard(self.name)
        self._alternate_emails.discard(self.email)

    def __repr__(self) -> str:
        aliases = None if not self.aliases else self.aliases
        alternate_emails = None if not self.alternate_emails else self.alternate_emails
        return (
            f"Author({self.name!r}, {self.email!r},"
            f" aliases={aliases!r}, alternate_emails={alternate_emails!r})"
        )


class AuthorList:
    def __init__(self, authors: Iterable[Author] | None = None) -> None:
        self._name: dict[str, Author] = {}
        self._email: dict[str, Author] = {}

        for author in authors or ():
            self._index_author(author)

    def __iter__(self):
        yield from set(self._name.values())

    def __len__(self) -> int:
        names = {author.name for author in self._name.values()}
        return len(names)

    def _index_author(self, author: Author) -> Author:
        author = author.norm()
        for name in author.names:
            self._name[name] = author
        for email in author.emails:
            self._email[email] = author
        return author

    def _reindex_author(self, author: Author) -> Author:
        for name, mapped in list(self._name.items()):
            if mapped is author:
                del self._name[name]
        for email, mapped in list(self._email.items()):
            if mapped is author:
                del self._email[email]
        return self._index_author(author)

    def update(self, other: AuthorList) -> None:
        for author in other:
            self.add_author(author)

    def add_author(self, author: Author) -> Author:
        matches = {
            *(self._name[name] for name in author.names if name in self._name),
            *(self._email[email] for email in author.emails if email in self._email),
        }
        if not matches:
            return self._index_author(author)

        primary = sorted(matches, key=lambda item: item.name)[0]
        primary.update(author)

        for other in matches:
            if other is primary:
                continue
            primary.update(other)

        for other in matches:
            self._reindex_author(other)

        return self._reindex_author(primary)

    def add(self, name: str, email: str) -> Author:
        return self.add_author(Author(name, email))

    def find_author(self, name_or_email: str) -> Author:
        if name_or_email in self._name:
            return self._name[name_or_email]
        if name_or_email in self._email:
            return self._email[name_or_email]
        raise KeyError(f"unknown author: {name_or_email!r}")


def score_name_for_display(name: str) -> tuple[int, int, str]:
    name = name.strip()
    parts = [part for part in re.split(r"\s+", name) if part]

    score = 0

    if len(parts) >= 2:
        score += 10

    if all(len(part) > 1 and not part.endswith(".") for part in parts[:2]):
        score += 10

    if re.fullmatch(
        r"[A-Za-z]+(?:[-'][A-Za-z]+)?(?:\s+[A-Za-z]+(?:[-'][A-Za-z]+)?)+", name
    ):
        score += 20

    if any(part.endswith(".") for part in parts):
        score -= 5

    if any(char.isdigit() for char in name):
        score -= 10

    if "@" in name:
        score -= 20

    return (score, len(name), name.casefold())


def _toml_kv(key: str, value) -> str:
    return f"{key} = {value!r}"


def _toml_array(key: str, values: Iterable[str]) -> str:
    if not values:
        return f"{key} = []"
    return os.linesep.join([f"{key} = ["] + [f"  {v!r}," for v in values] + ["]"])


def _mailmap_entries_from_author(author: Author) -> list[str]:
    proper_name, proper_email = author.name, author.email

    commit_combos = {
        (n.lower(), e.lower()) for n, e in product(author.names, author.emails)
    }
    commit_combos.discard((proper_name.lower(), proper_email.lower()))

    return [
        f"{proper_name} <{proper_email}> {name} <{email}>"
        for name, email in commit_combos
    ]
