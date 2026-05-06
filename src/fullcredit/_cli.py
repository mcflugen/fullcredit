import argparse
import sys

from fullcredit.api import collect_git_contributors


def err(msg: str) -> None:
    print(msg, file=sys.stderr)


def cmd_contributors(args: argparse.Namespace) -> int:
    identities = set()
    for repo in args.repo:
        identities |= collect_git_contributors(repo=repo)

    sep = "\0" if args.null else " "

    for name, email in sorted(identities):
        print(f"{name}{sep}{email}")

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

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    return args.func(args)
