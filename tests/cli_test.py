import io
import types

import pytest

from fullcredit._cli import main

GRAHAM_TOML = b"""\
[[author]]
name = "Graham Chapman"
email = "graham@example.com"
aliases = []
alternate_emails = []
"""

JOHN_TOML = b"""\
[[author]]
name = "John Cleese"
email = "john@example.com"
aliases = []
alternate_emails = []
"""

GRAHAM_JOHN_TOML = GRAHAM_TOML + b"\n" + JOHN_TOML

SORT_TOML = b"""\
[[author]]
name = "Michael Palin"
email = "michael@example.com"
aliases = []
alternate_emails = []

[[author]]
name = "Graham Chapman"
email = "graham@example.com"
aliases = []
alternate_emails = []

[[author]]
name = "John Cleese"
email = "john@example.com"
aliases = []
alternate_emails = []
"""

MAILMAP_TOML = b"""\
[[author]]
name = "Graham Chapman"
email = "graham@example.com"
aliases = [
  "G. Chapman",
]
alternate_emails = [
  "graham@work.com",
]
"""


@pytest.fixture
def binary_stdin(monkeypatch):
    def _set(data: bytes):
        monkeypatch.setattr("sys.stdin", types.SimpleNamespace(buffer=io.BytesIO(data)))

    return _set


class TestContributors:
    def test_basic(self, monkeypatch, capsys):
        monkeypatch.setattr(
            "fullcredit._cli.collect_git_contributors",
            lambda repo=None: {
                ("John Cleese", "john@example.com"),
                ("Graham Chapman", "graham@example.com"),
            },
        )
        assert main(["contributors", "foobar"]) == 0
        assert capsys.readouterr().out == (
            "Graham Chapman\0graham@example.com\n" "John Cleese\0john@example.com\n"
        )

    @pytest.mark.parametrize("sep", ("", " ", ":", "---"))
    def test_with_sep(self, monkeypatch, capsys, sep):
        monkeypatch.setattr(
            "fullcredit._cli.collect_git_contributors",
            lambda repo=None: {
                ("John Cleese", "john@example.com"),
                ("Graham Chapman", "graham@example.com"),
            },
        )
        assert main(["contributors", f"--sep={sep}", "foobar"]) == 0
        assert capsys.readouterr().out == (
            f"Graham Chapman{sep}graham@example.com\n"
            f"John Cleese{sep}john@example.com\n"
        )

    def test_no_repos_is_noop(self, capsys):
        assert main(["contributors"]) == 0
        assert capsys.readouterr().out == "\n"

    def test_output_is_sorted(self, monkeypatch, capsys):
        monkeypatch.setattr(
            "fullcredit._cli.collect_git_contributors",
            lambda repo=None: {
                ("Terry Gilliam", "terry@example.com"),
                ("Graham Chapman", "graham@example.com"),
            },
        )
        assert main(["contributors", "foobar"]) == 0
        lines = capsys.readouterr().out.strip().splitlines()
        assert lines[0].startswith("Graham Chapman")
        assert lines[1].startswith("Terry Gilliam")


class TestAuthors:
    def test_basic(self, monkeypatch, capsys):
        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO(
                "Graham Chapman\0graham@example.com\nJohn Cleese\0john@example.com\n"
            ),
        )
        assert main(["authors"]) == 0
        out = capsys.readouterr().out
        assert "[[author]]" in out
        assert "Graham Chapman" in out
        assert "John Cleese" in out

    def test_deduplicates(self, monkeypatch, capsys):
        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO(
                "Graham Chapman\0graham@example.com\n"
                "Graham Chapman\0graham@example.com\n"
            ),
        )
        assert main(["authors"]) == 0
        assert capsys.readouterr().out.count("[[author]]") == 1

    def test_invalid_identity_raises(self, monkeypatch, capsys):
        monkeypatch.setattr("sys.stdin", io.StringIO("not-null-delimited\n"))
        with pytest.raises(ValueError, match="invalid identity"):
            main(["authors"])

    def test_blank_lines_are_skipped(self, monkeypatch, capsys):
        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO("\nGraham Chapman\0graham@example.com\n\n"),
        )
        assert main(["authors"]) == 0
        assert "Graham Chapman" in capsys.readouterr().out


class TestInit:
    def test_produces_toml_with_author_table(self, monkeypatch, capsys):
        monkeypatch.setattr(
            "fullcredit._cli.collect_git_contributors",
            lambda repo=None: {("Graham Chapman", "graham@example.com")},
        )
        assert main(["init", "foobar"]) == 0
        out = capsys.readouterr().out
        assert "[[author]]" in out
        assert "Graham Chapman" in out

    def test_no_repos_produces_empty_output(self, capsys):
        assert main(["init"]) == 0
        assert capsys.readouterr().out.strip() == ""

    def test_output_is_sorted_by_name(self, monkeypatch, capsys):
        monkeypatch.setattr(
            "fullcredit._cli.collect_git_contributors",
            lambda repo=None: {
                ("Terry Gilliam", "terry@example.com"),
                ("Graham Chapman", "graham@example.com"),
            },
        )
        assert main(["init", "foobar"]) == 0
        out = capsys.readouterr().out
        assert out.index("Graham Chapman") < out.index("Terry Gilliam")


class TestMerge:
    def test_merges_stdin_with_file(self, capsys, tmp_path, binary_stdin):
        db = tmp_path / "authors.toml"
        db.write_bytes(JOHN_TOML)
        binary_stdin(GRAHAM_TOML)

        assert main(["merge", str(db)]) == 0
        out = capsys.readouterr().out
        assert "Graham Chapman" in out
        assert "John Cleese" in out

    def test_merges_overlapping_records(self, capsys, tmp_path, binary_stdin):
        extra = b"""\
[[author]]
name = "G. Chapman"
email = "graham@example.com"
aliases = []
alternate_emails = []
"""
        db = tmp_path / "authors.toml"
        db.write_bytes(GRAHAM_TOML)
        binary_stdin(extra)

        assert main(["merge", str(db)]) == 0
        out = capsys.readouterr().out
        assert out.count("[[author]]") == 1

    def test_stdin_only(self, capsys, binary_stdin):
        binary_stdin(GRAHAM_JOHN_TOML)
        assert main(["merge"]) == 0
        out = capsys.readouterr().out
        assert "Graham Chapman" in out
        assert "John Cleese" in out


def _parse_names_from_toml_output(out: str) -> list[str]:
    import tomllib

    data = tomllib.loads(out)
    return [a["name"] for a in data["author"]]


class TestSort:
    def test_sort_by_name(self, capsys, binary_stdin):
        binary_stdin(SORT_TOML)
        assert main(["sort", "name"]) == 0
        names = _parse_names_from_toml_output(capsys.readouterr().out)
        assert names == sorted(names, key=str.casefold)

    def test_sort_by_last_name(self, capsys, binary_stdin):
        binary_stdin(SORT_TOML)
        assert main(["sort", "last-name"]) == 0
        names = _parse_names_from_toml_output(capsys.readouterr().out)
        last_names = [n.split()[-1].casefold() for n in names]
        assert last_names == sorted(last_names)

    def test_sort_reverse(self, capsys, binary_stdin):
        binary_stdin(SORT_TOML)
        assert main(["sort", "name", "--reverse"]) == 0
        names = _parse_names_from_toml_output(capsys.readouterr().out)
        assert names == sorted(names, key=str.casefold, reverse=True)

    def test_invalid_key_returns_error(self, capsys, binary_stdin):
        binary_stdin(SORT_TOML)
        assert main(["sort", "invalid"]) == 1

    def test_sort_by_last_name_single_word(self, capsys, binary_stdin):
        single_word_toml = SORT_TOML + b"""
[[author]]
name = "Patsy"
email = "patsy@example.com"
aliases = []
alternate_emails = []
"""
        binary_stdin(single_word_toml)
        assert main(["sort", "last-name"]) == 0
        import tomllib

        names = [a["name"] for a in tomllib.loads(capsys.readouterr().out)["author"]]
        last_names = [n.split()[-1].casefold() for n in names]
        assert last_names == sorted(last_names)


class TestBuild:
    def test_default_format(self, capsys, binary_stdin):
        binary_stdin(GRAHAM_JOHN_TOML)
        assert main(["build"]) == 0
        out = capsys.readouterr().out
        assert "* Graham Chapman" in out
        assert "* John Cleese" in out

    def test_custom_format(self, capsys, binary_stdin):
        binary_stdin(GRAHAM_TOML)
        assert main(["build", "--format={name}"]) == 0
        assert capsys.readouterr().out.strip() == "Graham Chapman"

    def test_exclude_pattern(self, capsys, binary_stdin):
        bot_toml = b"""\
[[author]]
name = "spam[bot]"
email = "spam@example.com"
aliases = []
alternate_emails = []
"""
        binary_stdin(GRAHAM_TOML + b"\n" + bot_toml)
        assert main(["build", r"--exclude=\[bot\]"]) == 0
        out = capsys.readouterr().out
        assert "Graham Chapman" in out
        assert "spam" not in out

    def test_one_line_per_author(self, capsys, binary_stdin):
        binary_stdin(GRAHAM_JOHN_TOML)
        assert main(["build"]) == 0
        lines = [line for line in capsys.readouterr().out.splitlines() if line.strip()]
        assert len(lines) == 2


class TestMailmap:
    def test_generates_entries_for_aliases(self, capsys, binary_stdin):
        binary_stdin(MAILMAP_TOML)
        assert main(["mailmap"]) == 0
        out = capsys.readouterr().out
        assert "Graham Chapman <graham@example.com>" in out

    def test_output_is_sorted(self, capsys, binary_stdin):
        binary_stdin(MAILMAP_TOML)
        assert main(["mailmap"]) == 0
        lines = [line for line in capsys.readouterr().out.splitlines() if line]
        assert lines == sorted(lines)

    def test_no_aliases_produces_no_entries(self, capsys, binary_stdin):
        binary_stdin(GRAHAM_TOML)
        assert main(["mailmap"]) == 0
        assert capsys.readouterr().out.strip() == ""

    def test_invalid_toml_returns_error(self, capsys, binary_stdin):
        binary_stdin(b"[not_an_author_table]\nfoo = 'bar'\n")
        assert main(["mailmap"]) == 1
