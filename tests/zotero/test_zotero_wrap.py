__author__ = "Pierre-Alexandre Fonta"
__maintainer__ = "Pierre-Alexandre Fonta"

import os
from copy import deepcopy

import pyzotero
from _pytest.mark import param
from pytest import raises, mark
from pytest_lazyfixture import lazy_fixture

import nat
from tests.zotero.data import (REFERENCES, REFERENCE_TYPES, REFERENCE_TEMPLATES,
                               DOI, DOI_STR, PMID, PMID_STR, UPID, UPID_STR,
                               DATE, CREATORS, TEMPLATES_TEST_DATA)


# Helper to get the ZoteroWrap instance in the required state for testing.

def init(zww, field, value, is_data_subfield=True):
    """Add to a ZoteroWrap instance a reference with a field set to a value."""
    from tests.zotero.data import ARTICLE_TEMPLATE
    ref = deepcopy(ARTICLE_TEMPLATE)
    if is_data_subfield:
        ref["data"][field] = value
    else:
        ref[field] = value
    zww._references.append(ref)
    return ref


class TestZoteroWrap:

    # __init__

    def test_init(self, zw0_shared, shared_directory, cache_filename):
        """Test the creation of a ZoteroWrap instance."""
        assert zw0_shared.cache_path == os.path.join(shared_directory, cache_filename)
        assert zw0_shared.reference_types == []
        assert zw0_shared.reference_templates == {}
        assert zw0_shared._references == []

    # initialize

    def test_initialize_cache(self, mocker, zw0):
        """When there are data cached."""
        mocker.patch("nat.zotero_wrap.ZoteroWrap.load_cache")
        zw0.initialize()
        # TODO Use assert_called_once() with Python 3.6+.
        nat.zotero_wrap.ZoteroWrap.load_cache.assert_called_once_with()

    def test_initialize_distant(self, mocker, zw0):
        """When there are no data cached."""
        mocker.patch("nat.zotero_wrap.ZoteroWrap.load_distant")
        zw0.initialize()
        # TODO Use assert_called_once() with Python 3.6+.
        nat.zotero_wrap.ZoteroWrap.load_distant.assert_called_once_with()

    # cache

    def test_cache(self, zw0_shared, references, reference_types, reference_templates):
        """Test ZoteroWrap.cache()."""
        zw0_shared._references = references
        zw0_shared.reference_types = reference_types
        zw0_shared.reference_templates = reference_templates
        zw0_shared.cache()
        assert os.path.getsize(zw0_shared.cache_path) > 0

    # load_cache

    # Should be executed after test_cache().
    def test_load_cache(self, zw0_shared):
        """Test ZoteroWrap.load_cache()."""
        zw0_shared.load_cache()
        assert zw0_shared._references == REFERENCES
        assert zw0_shared.reference_types == REFERENCE_TYPES
        assert zw0_shared.reference_templates == REFERENCE_TEMPLATES

    # load_distant

    def test_load_distant(self, monkeypatch, zw0, references, reference_types, reference_templates):
        """Test ZoteroWrap.load_distant()."""
        scope = "nat.zotero_wrap.ZoteroWrap."
        monkeypatch.setattr(scope + "get_references", lambda _: references)
        monkeypatch.setattr(scope + "get_reference_types", lambda _: reference_types)
        monkeypatch.setattr(scope + "get_reference_templates", lambda _, x: reference_templates)
        zw0.load_distant()
        assert zw0._references == REFERENCES
        assert zw0.reference_types == REFERENCE_TYPES
        assert zw0.reference_templates == REFERENCE_TEMPLATES
        assert os.path.getsize(zw0.cache_path) > 0

    # create_local_reference

    @mark.parametrize("zww", [
        param(lazy_fixture("zw"), id="initialized"),
        param(lazy_fixture("zw0"), id="not_initialized")
    ])
    def test_create_local_reference(self, zww, reference):
        """When a ZoteroWrap instance has several references or none."""
        reference_count = zww.reference_count()
        zww.create_local_reference(reference)
        assert zww.reference_count() == reference_count + 1
        assert zww._references[-1] == reference
        assert os.path.getsize(zww.cache_path) > 0

    # create_distant_reference

    def test_create_distant_reference_successful(self, monkeypatch, zw0, reference):
        """When Zotero.create_items() has been successful."""
        creation_status = {
            "failed": {},
            "success": {"0": reference["key"]},
            "successful": {"0": reference},
            "unchanged": {}
        }
        monkeypatch.setattr("nat.zotero_wrap.ZoteroWrap.validate_reference_data", lambda _, x: None)
        monkeypatch.setattr("pyzotero.zotero.Zotero.create_items", lambda _, x: creation_status)
        assert zw0.create_distant_reference(reference["data"]) == reference

    def test_create_distant_reference_unsuccessful(self, monkeypatch, zw0, reference):
        """When Zotero.create_items() hasn't been successful."""
        # NB: Creation status expected when unsuccessful hasn't been observed.
        monkeypatch.setattr("nat.zotero_wrap.ZoteroWrap.validate_reference_data", lambda _, x: None)
        monkeypatch.setattr("pyzotero.zotero.Zotero.create_items", lambda _, x: {})
        with raises(nat.zotero_wrap.CreateZoteroItemError):
            zw0.create_distant_reference(reference["data"])

    def test_create_distant_reference_invalid(self, monkeypatch, mocker, zw0, reference):
        """When ZoteroWrap.validate_reference_data() hasn't been successful."""
        # NB: Exception raised at the validate_reference_data() level isn't captured.
        def raise_exception(_, x):
            raise pyzotero.zotero_errors.InvalidItemFields
        monkeypatch.setattr("pyzotero.zotero.Zotero.check_items", raise_exception)
        mocker.patch("pyzotero.zotero.Zotero.create_items")
        with raises(nat.zotero_wrap.InvalidZoteroItemError):
            zw0.create_distant_reference(reference["data"])
        # TODO Use assert_not_called() with Python 3.5+.
        assert not pyzotero.zotero.Zotero.create_items.called

    # update_local_reference

    def test_update_local_reference(self, zw, reference):
        """When a ZoteroWrap instance has several references."""
        references = deepcopy(zw._references)
        reference_count = zw.reference_count()
        index = reference_count // 2
        zw.update_local_reference(index, reference)
        changed = [new for old, new in zip(references, zw._references) if old != new]
        assert zw.reference_count() == reference_count
        assert zw._references[index] == reference
        assert len(changed) == 1
        assert os.path.getsize(zw.cache_path) > 0

    def test_update_local_reference_empty(self, zw0, reference):
        """When a ZoteroWrap instance has no references."""
        with raises(IndexError):
            zw0.update_local_reference(0, reference)
        assert zw0.reference_count() == 0
        assert len(os.listdir(os.path.dirname(zw0.cache_path))) == 0

    # update_distant_reference

    def test_update_distant_reference(self, monkeypatch, mocker, zw0, reference):
        """Test ZoteroWrap.update_distant_reference()."""
        monkeypatch.setattr("nat.zotero_wrap.ZoteroWrap.validate_reference_data", lambda _, x: None)
        mocker.patch("pyzotero.zotero.Zotero.update_item")
        zw0.update_distant_reference(reference)
        # TODO Use assert_called_once() with Python 3.6+.
        pyzotero.zotero.Zotero.update_item.assert_called_once_with(reference)

    def test_update_distant_reference_invalid(self, monkeypatch, mocker, zw0, reference):
        """When ZoteroWrap.validate_reference_data() hasn't been successful."""
        # NB: Exception raised at the validate_reference_data() level isn't captured.
        def raise_exception(_, x):
            raise pyzotero.zotero_errors.InvalidItemFields
        monkeypatch.setattr("pyzotero.zotero.Zotero.check_items", raise_exception)
        mocker.patch("pyzotero.zotero.Zotero.update_item")
        with raises(nat.zotero_wrap.InvalidZoteroItemError):
            zw0.update_distant_reference(reference)
        # TODO Use assert_not_called() with Python 3.5+.
        assert not pyzotero.zotero.Zotero.update_item.called

    # validate_reference_data

    def test_validate_reference_data(self, monkeypatch, zw0, reference):
        """When Zotero.check_items() isn't successful."""
        def raise_exception(_, x):
            raise pyzotero.zotero_errors.InvalidItemFields
        monkeypatch.setattr("pyzotero.zotero.Zotero.check_items", raise_exception)
        with raises(nat.zotero_wrap.InvalidZoteroItemError):
            zw0.validate_reference_data(reference["data"])

    # get_references

    def test_get_references(self, mocker, zw0):
        """Test ZoteroWrap.get_references()."""
        mocker_top = mocker.patch("pyzotero.zotero.Zotero.top")
        mocker.patch("pyzotero.zotero.Zotero.everything")
        zw0.get_references()
        # TODO Use assert_called_once() with Python 3.6+.
        pyzotero.zotero.Zotero.top.assert_called_once_with()
        pyzotero.zotero.Zotero.everything.assert_called_once_with(mocker_top())

    # get_reference_types

    def test_get_reference_types(self, monkeypatch, zw0, item_types):
        """Test ZoteroWrap.get_reference_types()."""
        monkeypatch.setattr("pyzotero.zotero.Zotero.item_types", lambda _: item_types)
        assert zw0.get_reference_types() == REFERENCE_TYPES

    # get_reference_templates

    def test_get_reference_templates(self, monkeypatch, zw0, reference_types):
        """Test ZoteroWrap.get_reference_templates()."""
        def patch(_, ref_type):
            from tests.zotero.data import GET_REFERENCE_TEMPLATES
            index = reference_types.index(ref_type)
            return GET_REFERENCE_TEMPLATES[index]
        monkeypatch.setattr("nat.zotero_wrap.ZoteroWrap.get_reference_template", patch)
        assert zw0.get_reference_templates(reference_types) == REFERENCE_TEMPLATES

    # get_reference_template

    @mark.parametrize("ref_type, patched, expected", TEMPLATES_TEST_DATA)
    def test_get_reference_template(self, monkeypatch, zw0, ref_type, patched, expected):
        """Test ZoteroWrap.get_reference_template() for each known cases."""
        monkeypatch.setattr("pyzotero.zotero.Zotero.item_template", lambda _, x: patched)
        assert zw0.get_reference_template(ref_type) == expected

    # get_reference

    def test_get_reference(self, mocker, zw0, reference):
        """Test ZoteroWrap.get_reference()."""
        reference_key = reference["key"]
        mocker.patch("pyzotero.zotero.Zotero.item")
        zw0.get_reference(reference_key)
        pyzotero.zotero.Zotero.item.assert_called_once_with(reference_key)

    # reference_count

    @mark.parametrize("zww, expected", [
        param(lazy_fixture("zw"), len(REFERENCES), id="initialized"),
        param(lazy_fixture("zw0"), 0, id="not_initialized")
    ])
    def test_reference_count(self, zww, expected):
        """When a ZoteroWrap instance has several references or none."""
        assert zww.reference_count() == expected

    # reference_data

    def test_reference_data(self, zw0, reference):
        """Test ZoteroWrap.reference_data()."""
        zw0._references.append(reference)
        assert zw0.reference_data(0) == reference["data"]

    # reference_extra_field

    @mark.parametrize("value, expected", [
        param(PMID_STR, (PMID, ""), id="one"),
        param(PMID_STR + "\nPMCID: PMC1234567", (PMID, "PMC1234567"), id="several"),
        param("", ("", ""), id="empty")
    ])
    def test_reference_extra_field(self, zw0, value, expected):
        """When a reference has one, several, or no extra field(s)."""
        init(zw0, "extra", value)
        assert zw0.reference_extra_field("PMID", 0) == expected[0]
        assert zw0.reference_extra_field("PMCID", 0) == expected[1]

    # reference_type

    def test_reference_type(self, zw0):
        """Test ZoteroWrap.reference_type()."""
        value = "journalArticle"
        init(zw0, "itemType", value)
        assert zw0.reference_type(0) == value

    # reference_key

    def test_reference_key(self, zw0):
        """Test ZoteroWrap.reference_key()."""
        value = "01ABC3DE"
        init(zw0, "key", value, is_data_subfield=False)
        assert zw0.reference_key(0) == value

    # reference_doi

    def test_reference_doi(self, zw0):
        """When a reference has a DOI."""
        init(zw0, "DOI", DOI)
        assert zw0.reference_doi(0) == DOI

    def test_reference_doi_extra(self, zw0, reference_book):
        """When a reference has a DOI as an extra field (not a 'journalArticle')."""
        reference_book["data"]["extra"] = DOI_STR
        zw0._references.append(reference_book)
        assert zw0.reference_doi(0) == DOI

    def test_reference_doi_without(self, zw0):
        """When a reference has no DOI (dedicated field or in 'extra')."""
        reference = init(zw0, "DOI", "")
        reference["extra"] = ""
        assert zw0.reference_doi(0) == ""

    # reference_pmid

    @mark.parametrize("value, expected", [
        param(PMID_STR, PMID, id="with"),
        param("", "", id="without"),
    ])
    def test_reference_pmid(self, zw0, value, expected):
        """When a reference has a PMID as an extra field or none."""
        init(zw0, "extra", value)
        assert zw0.reference_pmid(0) == expected

    # reference_unpublished_id

    @mark.parametrize("value, expected", [
        param(UPID_STR, UPID, id="with"),
        param("", "", id="without"),
    ])
    def test_reference_unpublished_id(self, zw0, value, expected):
        """When a reference has an UNPUBLISHED ID as an extra field or none."""
        init(zw0, "extra", value)
        assert zw0.reference_unpublished_id(0) == expected

    # reference_id

    def test_reference_id_doi(self, zw0):
        """When a reference has a DOI."""
        init(zw0, "DOI", DOI)
        assert zw0.reference_id(0) == DOI

    def test_reference_id_doi_extra(self, zw0, reference_book):
        """When a reference has a DOI as an extra field (not a 'journalArticle')."""
        reference_book["data"]["extra"] = DOI_STR
        zw0._references.append(reference_book)
        assert zw0.reference_id(0) == DOI

    @mark.parametrize("value, expected", [
        param(PMID_STR, "PMID_" + PMID, id="PMID"),
        param(UPID_STR, "UNPUBLISHED_" + UPID, id="UNPUBLISHED_ID")
    ])
    def test_reference_id_extra(self, zw0, value, expected):
        """When a reference has a PMID or a UNPUBLISHED ID as an extra field."""
        init(zw0, "extra", value)
        assert zw0.reference_id(0) == expected

    def test_reference_id_without(self, zw0):
        """When a reference has no ID (DOI, PMID, UNPUBLISHED ID)."""
        reference = init(zw0, "DOI", "")
        reference["extra"] = ""
        assert zw0.reference_id(0) == ""

    # reference_title

    def test_reference_title(self, zw0):
        """When a reference has a title."""
        value = "Journal Article"
        init(zw0, "title", value)
        assert zw0.reference_title(0) == value

    # reference_creator_surnames

    @mark.parametrize("value, expected", [
        param(CREATORS[:1], ["AuthorLastA"], id="one_author"),
        param(CREATORS[:2], ["AuthorLastA", "AuthorLast-B"], id="two_authors"),
        param(CREATORS[3:-1], ["EditorLastA", "EditorLast-B"], id="several_not_authors"),
        param(CREATORS[:-1], ["AuthorLastA", "AuthorLast-B", "AuthorLastC"], id="several_mixed"),
        param(CREATORS[-1:], [], id="no_last_name"),
    ])
    def test_reference_creator_surnames(self, zw0, value, expected):
        """Test reference_creator_surnames().

        When a reference has one creator of type 'author'.
        When a reference has two creators of type 'author'.
        When a reference has several creators which aren't of type 'author'.
        When a reference has several creators of type 'author' and not.
        When a reference has one creator of type 'author' described with 'name'.
        """
        init(zw0, "creators", value)
        assert zw0.reference_creator_surnames(0) == expected

    # reference_creator_surnames_str

    @mark.parametrize("value, expected", [
        param(CREATORS[:1], "AuthorLastA", id="one_author"),
        param(CREATORS[:2], "AuthorLastA, AuthorLast-B", id="two_authors"),
        param(CREATORS[-1:], "", id="no_last_name"),
    ])
    def test_reference_creator_surnames_str(self, zw0, value, expected):
        """Test reference_creator_surnames_str().

        When a reference has one creator of type 'author'.
        When a reference has two creators of type 'author'.
        When a reference has one creator of type 'author' described with 'name'.
        """
        init(zw0, "creators", value)
        assert zw0.reference_creator_surnames_str(0) == expected

    # reference_date

    @mark.parametrize("value, expected", [
        param(DATE, DATE, id="with"),
        param("", "", id="empty")
    ])
    def test_reference_date(self, zw0, value, expected):
        """When a reference has a date or none."""
        init(zw0, "date", value)
        assert zw0.reference_date(0) == expected

    # reference_year

    @mark.parametrize("value, expected", [
        param(DATE, 2017, id="recognized"),
        param("9 avr. 2017", 2017, id="unrecognized"),
        param("", "", id="without")
    ])
    def test_reference_year(self, zw0, value, expected):
        """Test reference_year().

        When a reference has a year recognized by dateutil.parser.parse().
        When a reference has a year not recognized by dateutil.parser.parse().
        When a reference has no year (because no date).
        """
        init(zw0, "date", value)
        assert zw0.reference_year(0) == expected

    # reference_journal

    def test_reference_journal(self, zw0):
        """When a reference has a journal."""
        value = "The Journal of Journals"
        init(zw0, "publicationTitle", value)
        assert zw0.reference_journal(0) == value

    def test_reference_journal_without(self, zw0, reference_book):
        """When a reference has no journal (not a 'journalArticle')."""
        zw0._references.append(reference_book)
        assert zw0.reference_journal(0) == "(book)"

    # reference_index

    def test_reference_index_one_found(self, zw0):
        """When a reference in the reference list has the searched reference ID."""
        init(zw0, "extra", PMID_STR)
        init(zw0, "DOI", DOI)
        init(zw0, "extra", UPID_STR)
        assert zw0.reference_index(DOI) == 1

    def test_reference_index_several_found(self, zw0):
        """When there are duplicates in the reference list (same reference ID)."""
        init(zw0, "DOI", DOI)
        init(zw0, "extra", PMID_STR)
        init(zw0, "extra", PMID_STR)
        assert zw0.reference_index("PMID_" + PMID) == 1

    def test_reference_index_not_found(self, zw0):
        """When no reference in the reference list has the searched reference ID."""
        init(zw0, "extra", PMID_STR)
        init(zw0, "extra", UPID_STR)
        exception_str = "^ID: {}$".format(DOI)
        with raises(nat.zotero_wrap.ReferenceNotFoundError, match=exception_str):
            zw0.reference_index(DOI)

    # reference_creators_citation

    @mark.parametrize("value, expected", [
        param(CREATORS[:1], "AuthorLastA (2017)", id="one_author"),
        param(CREATORS[:2], "AuthorLastA and AuthorLast-B (2017)", id="two_authors"),
        param(CREATORS[:3], "AuthorLastA et al. (2017)", id="three_authors"),
        param(CREATORS[-1:], "", id="no_last_name"),
    ])
    def test_reference_creators_citation(self, zw0, value, expected):
        """Test reference_creators_citation().

        When a reference with an ID and a date has one creator.
        When a reference with an ID and a date has two creators.
        When a reference with an ID and a date has three creators.
        When a reference with an ID and a date has one creator described with 'name'.
        """
        reference = init(zw0, "DOI", DOI)
        reference["data"]["date"] = DATE
        reference["data"]["creators"] = value
        assert zw0.reference_creators_citation(DOI) == expected

    @mark.parametrize("value, expected", [
        param(CREATORS[:3], "AuthorLastA et al. ()", id="three_authors"),
        param(CREATORS[-1:], "", id="no_last_name"),
    ])
    def test_reference_creators_citation_year_without(self, zw0, value, expected):
        """When a reference has no year (because no date)."""
        reference = init(zw0, "DOI", DOI)
        reference["data"]["date"] = ""
        reference["data"]["creators"] = value
        assert zw0.reference_creators_citation(DOI) == expected
