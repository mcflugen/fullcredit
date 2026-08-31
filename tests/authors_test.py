import tomllib

import pytest

from fullcredit.authors import Author
from fullcredit.authors import AuthorCollection
from fullcredit.authors import _mailmap_entries_from_author
from fullcredit.authors import _merge_extras
from fullcredit.authors import filter_authors
from fullcredit.authors import score_name_for_display


class TestScoreNameForDisplay:
    @pytest.mark.parametrize(
        "good, not_as_good",
        (
            ("Graham Chapman", "Grapham"),  # full name beats single name
            ("Graham Chapman", "G. Chapman"),  # full name beats abbreviated name
            ("Graham Chapman", "graham@example.com"),  # full name beats email
            ("Graham Chapman", "Graham2 Chapman"),  # full name beats name with number
            ("Terry-Thomas Gilliam", "graham@example.com"),
            ("Graham", "Eric"),  # longer name beats shorter name
        ),
    )
    def test_name_score(self, good, not_as_good):
        assert score_name_for_display(good) > score_name_for_display(not_as_good)


class TestAuthorConstruction:
    def test_basic(self):
        author = Author("Graham", "graham@example.com")
        assert author.name == "Graham"
        assert author.email == "graham@example.com"
        assert author.aliases == ()
        assert author.alternate_emails == ()

    def test_with_aliases(self):
        author = Author(
            "Graham", "graham@example.com", aliases=["G. Chapman", "Graeme"]
        )
        assert set(author.aliases) == {"G. Chapman", "Graeme"}

    def test_with_alternate_emails(self):
        author = Author(
            "Graham", "graham@example.com", alternate_emails=["graham@work.com"]
        )
        assert author.alternate_emails == ("graham@work.com",)

    def test_alias_same_as_name_is_discarded(self):
        author = Author("Graham", "graham@example.com", aliases=["Graham"])
        assert author.aliases == ()

    def test_alternate_email_same_as_email_is_discarded(self):
        author = Author(
            "Graham", "graham@example.com", alternate_emails=["graham@example.com"]
        )
        assert author.alternate_emails == ()

    def test_names_includes_name_and_aliases(self):
        author = Author(
            "Graham", "graham@example.com", aliases=["G. Chapman", "Graeme"]
        )
        assert set(author.names) == {"Graham", "G. Chapman", "Graeme"}

    def test_emails_includes_email_and_alternates(self):
        author = Author(
            "Graham", "graham@example.com", alternate_emails=["graham@work.com"]
        )
        assert set(author.emails) == {"graham@example.com", "graham@work.com"}


class TestAuthorFromDict:
    def test_basic(self):
        author = Author.from_dict({"name": "Graham", "email": "graham@example.com"})
        assert author.name == "Graham"
        assert author.email == "graham@example.com"

    def test_with_aliases(self):
        author = Author.from_dict(
            {"name": "Graham", "email": "graham@example.com", "aliases": ["G. Chapman"]}
        )
        assert author.aliases == ("G. Chapman",)

    def test_with_extras(self):
        author = Author.from_dict(
            {"name": "Graham", "email": "graham@example.com", "github": "graham"}
        )
        assert author.extras == (("github", "graham"),)


class TestAuthorNorm:
    def test_chooses_best_name(self):
        author = Author("graham", "graham@example.com", aliases=["Graham Chapman"])
        assert author.norm().name == "Graham Chapman"

    def test_demoted_name_becomes_alias(self):
        author = Author("graham", "graham@example.com", aliases=["Graham Chapman"])
        normed = author.norm()
        assert "graham" in normed.aliases

    def test_preserves_extras(self):
        author = Author.from_dict(
            {"name": "graham", "email": "graham@example.com", "github": "graham"}
        )
        author._aliases.add("Graham Chapman")
        assert author.norm().extras == (("github", "graham"),)


class TestAuthorChooseBestName:
    def test_full_name_over_username(self):
        assert Author.choose_best_name(["graham", "Graham Chapman"]) == "Graham Chapman"

    def test_full_name_over_email(self):
        assert (
            Author.choose_best_name(["graham@example.com", "Graham Chapman"])
            == "Graham Chapman"
        )


class TestAuthorMerge:
    def test_merges_names(self):
        a = Author("Graham", "graham@example.com")
        b = Author("G. Chapman", "graham@example.com")
        merged = Author.merge([a, b])
        assert set(merged.names) == {"Graham", "G. Chapman"}

    def test_merges_emails(self):
        a = Author("Graham", "graham@example.com")
        b = Author("Graham", "graham@work.com")
        merged = Author.merge([a, b])
        assert set(merged.emails) == {"graham@example.com", "graham@work.com"}

    def test_chooses_best_name(self):
        a = Author("graham", "graham@example.com")
        b = Author("Graham Chapman", "graham@work.com")
        assert Author.merge([a, b]).name == "Graham Chapman"

    def test_merges_compatible_extras(self):
        a = Author.from_dict(
            {"name": "Graham", "email": "graham@example.com", "github": "graham"}
        )
        b = Author("Graham", "graham@work.com")
        assert Author.merge([a, b]).extras == (("github", "graham"),)

    def test_raises_on_conflicting_extras(self):
        a = Author.from_dict(
            {"name": "Graham", "email": "graham@example.com", "github": "graham"}
        )
        b = Author.from_dict(
            {"name": "Graham", "email": "graham@work.com", "github": "different"}
        )
        with pytest.raises(ValueError, match="github"):
            Author.merge([a, b])

    def test_empty_list_raises(self):
        with pytest.raises(ValueError):
            Author.merge([])


class TestAuthorUpdate:
    def test_adds_new_alias(self):
        author = Author("Graham", "graham@example.com")
        author.update(Author("G. Chapman", "graham@example.com"))
        assert "G. Chapman" in author.aliases

    def test_adds_new_alternate_email(self):
        author = Author("Graham", "graham@example.com")
        author.update(Author("Graham", "graham@work.com"))
        assert "graham@work.com" in author.alternate_emails

    def test_same_name_not_added_as_alias(self):
        author = Author("Graham", "graham@example.com")
        author.update(Author("Graham", "graham@work.com"))
        assert "Graham" not in author.aliases

    def test_same_email_not_added_as_alternate(self):
        author = Author("Graham", "graham@example.com")
        author.update(Author("G. Chapman", "graham@example.com"))
        assert "graham@example.com" not in author.alternate_emails

    def test_merges_compatible_extras(self):
        author = Author.from_dict(
            {"name": "Graham", "email": "graham@example.com", "github": "graham"}
        )
        author.update(Author("G. Chapman", "graham@example.com"))
        assert author.extras == (("github", "graham"),)

    def test_raises_on_conflicting_extras(self):
        author = Author.from_dict(
            {"name": "Graham", "email": "graham@example.com", "github": "graham"}
        )
        other = Author.from_dict(
            {"name": "G. Chapman", "email": "graham@example.com", "github": "different"}
        )
        with pytest.raises(ValueError, match="github"):
            author.update(other)


class TestAuthorAddName:
    def test_adds_alias(self):
        author = Author("Graham", "graham@example.com")
        author.add_name("G. Chapman")
        assert "G. Chapman" in author.aliases

    def test_same_as_name_is_noop(self):
        author = Author("Graham", "graham@example.com")
        author.add_name("Graham")
        assert author.aliases == ()


class TestAuthorAddEmail:
    def test_adds_alternate_email(self):
        author = Author("Graham", "graham@example.com")
        author.add_email("graham@work.com")
        assert "graham@work.com" in author.alternate_emails

    def test_same_as_email_is_noop(self):
        author = Author("Graham", "graham@example.com")
        author.add_email("graham@example.com")
        assert author.alternate_emails == ()


class TestAuthorRepr:
    def test_no_aliases(self):
        author = Author("Graham", "graham@example.com")
        assert repr(author) == (
            "Author("
            "'Graham', 'graham@example.com', aliases=None, alternate_emails=None"
            ")"
        )

    def test_with_aliases(self):
        author = Author("Graham", "graham@example.com", aliases=["G. Chapman"])
        assert "aliases=('G. Chapman',)" in repr(author)


class TestAuthorToToml:
    def test_roundtrip(self):
        original = Author.from_dict(
            {
                "name": "Graham Chapman",
                "email": "graham@example.com",
                "aliases": ["G. Chapman"],
                "alternate_emails": ["graham@work.com"],
                "github": "grahamchapman",
            }
        )
        data = tomllib.loads(original.to_toml())
        record = data["author"][0]
        restored = Author.from_dict(record)

        assert restored.name == original.name
        assert restored.email == original.email
        assert restored.aliases == original.aliases
        assert restored.alternate_emails == original.alternate_emails
        assert restored.extras == original.extras


class TestAuthorCollection:
    def test_empty_has_len_zero(self):
        assert len(AuthorCollection()) == 0

    def test_add_single_author(self):
        coll = AuthorCollection()
        coll.add("Graham", "graham@example.com")
        assert len(coll) == 1

    def test_add_two_distinct_authors(self):
        coll = AuthorCollection()
        coll.add("Graham", "graham@example.com")
        coll.add("John", "john@example.com")
        assert len(coll) == 2

    def test_add_same_name_merges(self):
        coll = AuthorCollection()
        coll.add("Graham", "graham@example.com")
        coll.add("Graham", "graham@work.com")
        assert len(coll) == 1
        assert "graham@work.com" in coll.find_author("Graham").emails

    def test_add_same_email_merges(self):
        coll = AuthorCollection()
        coll.add("Graham", "graham@example.com")
        coll.add("G. Chapman", "graham@example.com")
        assert len(coll) == 1

    def test_contains_by_name(self):
        coll = AuthorCollection()
        coll.add("Graham", "graham@example.com")
        assert "Graham" in coll

    def test_contains_by_email(self):
        coll = AuthorCollection()
        coll.add("Graham", "graham@example.com")
        assert "graham@example.com" in coll

    def test_not_contains_unknown(self):
        assert "unknown" not in AuthorCollection()

    def test_not_contains_non_string(self):
        coll = AuthorCollection()
        assert 42 not in coll

    def test_iter_yields_unique_authors(self):
        coll = AuthorCollection()
        coll.add("Graham", "graham@example.com")
        coll.add("Graham", "graham@work.com")
        assert len(list(coll)) == 1

    def test_init_from_authors_merges_duplicates(self):
        authors = [
            Author("Graham", "graham@example.com"),
            Author("Graham", "graham@work.com"),
        ]
        assert len(AuthorCollection(authors=authors)) == 1

    def test_find_author_by_name(self):
        coll = AuthorCollection()
        coll.add("Graham", "graham@example.com")
        assert coll.find_author("Graham").name == "Graham"

    def test_find_author_by_email(self):
        coll = AuthorCollection()
        coll.add("Graham", "graham@example.com")
        assert coll.find_author("graham@example.com").name == "Graham"

    def test_find_author_unknown_raises(self):
        with pytest.raises(KeyError):
            AuthorCollection().find_author("unknown")

    def test_update_merges_two_collections(self):
        a = AuthorCollection()
        a.add("Graham", "graham@example.com")
        b = AuthorCollection()
        b.add("John", "john@example.com")
        a.update(b)
        assert len(a) == 2

    def test_update_merges_overlapping_authors(self):
        a = AuthorCollection()
        a.add("Graham", "graham@example.com")
        b = AuthorCollection()
        b.add("G. Chapman", "graham@example.com")
        a.update(b)
        assert len(a) == 1
        assert "G. Chapman" in a.find_author("Graham").aliases

    def test_add_author_merges_multiple_matching_records(self):
        # Adding an author that matches two different existing records by
        # different keys (name matches one, email matches another) causes
        # all three to be merged into one.
        coll = AuthorCollection()
        coll.add("Graham", "graham@example.com")
        coll.add("John", "john@example.com")
        coll.add_author(Author("Graham", "john@example.com"))
        assert len(coll) == 1

    def test_transitive_merge(self):
        # Graham + G. Chapman share email; G. Chapman + Graeme share name,
        # all three become one record
        coll = AuthorCollection()
        coll.add("Graham", "graham@example.com")
        coll.add("G. Chapman", "graham@example.com")
        coll.add("G. Chapman", "graham@work.com")
        assert len(coll) == 1


class TestFilterAuthors:
    @pytest.fixture
    def authors(self):
        return [
            Author("Graham Chapman", "graham@example.com"),
            Author("John Cleese", "john@example.com"),
            Author("spam[bot]", "spam@example.com"),
        ]

    def test_no_filter_returns_all(self, authors):
        assert filter_authors(authors) == authors

    def test_exclude_pattern(self, authors):
        result = filter_authors(authors, exclude=r"\[bot\]")
        assert len(result) == 2
        assert all("[bot]" not in a.name for a in result)

    def test_include_pattern(self, authors):
        result = filter_authors(authors, include="Chapman")
        assert len(result) == 1
        assert result[0].name == "Graham Chapman"

    def test_exclude_matches_aliases(self):
        author = Author("Graham", "graham@example.com", aliases=["spam[bot]"])
        assert filter_authors([author], exclude=r"\[bot\]") == []

    def test_include_matches_aliases(self):
        author = Author("graham", "graham@example.com", aliases=["Graham Chapman"])
        assert filter_authors([author], include="Chapman") == [author]


class TestMergeExtras:
    def test_disjoint_dicts(self):
        assert _merge_extras({"a": 1}, {"b": 2}) == {"a": 1, "b": 2}

    def test_same_key_same_value(self):
        assert _merge_extras({"a": 1}, {"a": 1}) == {"a": 1}

    def test_conflicting_key_raises(self):
        with pytest.raises(ValueError, match="'a'"):
            _merge_extras({"a": 1}, {"a": 2})

    def test_error_message_includes_both_values(self):
        with pytest.raises(ValueError, match="1"):
            _merge_extras({"a": 1}, {"a": 2})

    def test_both_empty(self):
        assert _merge_extras({}, {}) == {}

    def test_first_empty(self):
        assert _merge_extras({}, {"a": 1}) == {"a": 1}

    def test_second_empty(self):
        assert _merge_extras({"a": 1}, {}) == {"a": 1}


class TestMailmapEntries:
    def test_no_aliases_or_alternate_emails(self):
        author = Author("Graham Chapman", "graham@example.com")
        assert _mailmap_entries_from_author(author) == []

    def test_alias_generates_entry(self):
        author = Author("Graham Chapman", "graham@example.com", aliases=["G. Chapman"])
        entries = _mailmap_entries_from_author(author)
        assert entries == [
            "Graham Chapman <graham@example.com> g. chapman <graham@example.com>"
        ]

    def test_alternate_email_generates_entry(self):
        author = Author(
            "Graham Chapman", "graham@example.com", alternate_emails=["graham@work.com"]
        )
        entries = _mailmap_entries_from_author(author)
        assert entries == [
            "Graham Chapman <graham@example.com> graham chapman <graham@work.com>"
        ]

    def test_proper_combo_not_in_entries(self):
        author = Author("Graham Chapman", "graham@example.com", aliases=["G. Chapman"])
        for entry in _mailmap_entries_from_author(author):
            assert "graham chapman <graham@example.com>" not in entry.split("> ", 1)[1]
