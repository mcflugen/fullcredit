import argparse
import sys
from collections.abc import Iterable

from fullcredit.api import build_author_list
from fullcredit.api import collect_git_contributors
from fullcredit.authors import Author


def err(msg: str) -> None:
    print(msg, file=sys.stderr)


def cmd_contributors(args: argparse.Namespace) -> int:
    sep = "\0" if args.null else " "

    identities = _merge_identities(args.repo)
    print(_dump_identities(identities, sep=sep))

    return 0


def cmd_init(args: argparse.Namespace) -> int:
    identities = sorted(_merge_identities(args.repo))
    print(_dump_authors(build_author_list(identities)))

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

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("repo", nargs="*", help="git repository")
    init_parser.set_defaults(func=cmd_init)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    return args.func(args)


def _dump_authors(authors: Iterable[Author]) -> str:
    return "\n\n".join(
        author.to_toml() for author in sorted(authors, key=lambda a: (a.name, a.email))
    )


def _dump_identities(identities: Iterable[tuple[str, str]], sep=None) -> str:
    sep = " " if sep is None else sep

    lines = [f"{name}{sep}{email}" for name, email in sorted(identities)]

    return "\n".join(lines)


def _merge_identities(repos: Iterable[str]) -> set[tuple[str, str]]:
    identities = set()
    for repo in repos:
        identities |= collect_git_contributors(repo=repo)
    return identities
