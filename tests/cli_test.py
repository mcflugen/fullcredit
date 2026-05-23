import pytest

from fullcredit._cli import main


def test_contributors(monkeypatch, capsys):
    monkeypatch.setattr(
        "fullcredit._cli.collect_git_contributors",
        lambda repo=None: {
            ("Bob", "bob@example.com"),
            ("Alice", "alice@example.com"),
        },
    )

    assert main(["contributors", "foobar"]) == 0
    assert capsys.readouterr().out == (
        "Alice\0alice@example.com\n" "Bob\0bob@example.com\n"
    )


@pytest.mark.parametrize("sep", ("", " ", ":", "---"))
def test_contributors_with_sep(monkeypatch, capsys, sep):
    monkeypatch.setattr(
        "fullcredit._cli.collect_git_contributors",
        lambda repo=None: {
            ("Bob", "bob@example.com"),
            ("Alice", "alice@example.com"),
        },
    )

    assert main(["contributors", "--sep={sep}", "foobar"]) == 0
    assert capsys.readouterr().out == (
        "Alice{sep}alice@example.com\n" "Bob{sep}bob@example.com\n"
    )


def test_contributors_with_no_repos_is_noop(capsys):
    assert main(["contributors"]) == 0
    assert capsys.readouterr().out == "\n"
