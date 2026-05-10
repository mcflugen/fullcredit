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
        "Alice alice@example.com\n" "Bob bob@example.com\n"
    )


def test_contributors_with_no_repos_is_noop(capsys):
    assert main(["contributors"]) == 0
    assert capsys.readouterr().out == "\n"
