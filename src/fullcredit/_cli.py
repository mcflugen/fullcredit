import argparse
import sys
import tomllib
from collections.abc import Iterable
from typing import BinaryIO

from fullcredit.api import build_author_list
from fullcredit.api import collect_git_contributors
from fullcredit.api import merge_authors
from fullcredit.authors import Author
from fullcredit.authors import AuthorList
from fullcredit.authors import _mailmap_entries_from_author


class FullcreditError(Exception):
    """Base exception for fullcredit."""


def err(msg: str) -> None:
    print(msg, file=sys.stderr)


def cmd_contributors(args: argparse.Namespace) -> int:
    sep = "\0" if args.null else " "

    identities = _merge_identities(args.repo)
    print(_dump_identities(identities, sep=sep))

    return 0


def cmd_authors(args: argparse.Namespace) -> int:
    identities = sorted(_load_identities(sys.stdin))
    print(_dump_authors(build_author_list(identities)))

    return 0


def cmd_init(args: argparse.Namespace) -> int:
    identities = sorted(_merge_identities(args.repo))
    print(_dump_authors(build_author_list(identities)))

    return 0


def cmd_merge(args: argparse.Namespace) -> int:
    lists = [_load_authors(sys.stdin.buffer)]
    for path in args.authors:
        with open(path, "rb") as stream:
            lists.append(_load_authors(stream))
    authors = merge_authors(lists)

    print(_dump_authors(authors))

    return 0


def cmd_mailmap(args: argparse.Namespace) -> int:
    try:
        authors = _load_authors(sys.stdin.buffer)
    except FullcreditError as error:
        err(str(error))
        return 1

    lines = []
    for author in authors:
        lines += _mailmap_entries_from_author(author)

    print("\n".join(sorted(lines)))

    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="fullcredit")

    subparsers = parser.add_subparsers(dest="command", required=True)

    contrib_parser = subparsers.add_parser("contributors")
    contrib_parser.add_argument(
        "repo",
        nargs="*",
        help="git repository",
    )
    contrib_parser.add_argument(
        *("-0", "--null"),
        action="store_true",
        help="use null to separate names from emails",
    )
    contrib_parser.set_defaults(func=cmd_contributors)

    authors_parser = subparsers.add_parser("authors")
    authors_parser.set_defaults(func=cmd_authors)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("repo", nargs="*", help="git repository")
    init_parser.set_defaults(func=cmd_init)

    merge_parser = subparsers.add_parser("merge")
    merge_parser.add_argument("authors", nargs="*", help="merge author files")
    merge_parser.set_defaults(func=cmd_merge)

    mailmap_parser = subparsers.add_parser("mailmap")
    mailmap_parser.set_defaults(func=cmd_mailmap)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    return args.func(args)


def _dump_authors(authors: Iterable[Author]) -> str:
    return "\n\n".join(
        author.to_toml() for author in sorted(authors, key=lambda a: (a.name, a.email))
    )


def _load_authors(source: BinaryIO) -> AuthorList:
    data = tomllib.load(source)

    try:
        records = data["tool"]["fullcredit"]["author"]
    except KeyError as err:
        raise FullcreditError(
            "toml source must have [[tool.fullcredit.author]]"
        ) from err
    authors = [Author.from_dict(author) for author in records]

    return AuthorList(authors=authors)


def _dump_identities(identities: Iterable[tuple[str, str]], sep=None) -> str:
    sep = " " if sep is None else sep

    lines = [f"{name}{sep}{email}" for name, email in sorted(identities)]

    return "\n".join(lines)


def _merge_identities(repos: Iterable[str]) -> set[tuple[str, str]]:
    identities = set()
    for repo in repos:
        identities |= collect_git_contributors(repo=repo)
    return identities


def _load_identities(stream: Iterable[str]) -> list[tuple[str, str]]:
    identities = set()
    for line in stream:
        identity = line.strip()
        if not identity:
            continue
        try:
            name, email = identity.split("\0", maxsplit=1)
        except ValueError:
            raise ValueError(f"{identity}: invalid identity")

        identities.add((name.strip(), email.strip()))
    return list(identities)
