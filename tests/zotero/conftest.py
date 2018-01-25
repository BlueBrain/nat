__author__ = "Pierre-Alexandre Fonta"
__maintainer__ = "Pierre-Alexandre Fonta"

from copy import deepcopy

from pytest import fixture

from nat.zotero_wrap import ZoteroWrap
from tests.zotero.data import (REFERENCES, REFERENCE_TYPES, REFERENCE_TEMPLATES,
                               ARTICLE_TEMPLATE, BOOK_TEMPLATE, ITEM_TYPES)


# Fixture for the data which might be changed during a test.


@fixture
def references():
    """Return references of type 'journalArticle'."""
    return deepcopy(REFERENCES)


@fixture
def reference_types():
    """Return the expected reference types from get_reference_types()."""
    return deepcopy(REFERENCE_TYPES)


@fixture
def reference_templates():
    """Return the expected reference templates from get_reference_templates()."""
    return deepcopy(REFERENCE_TEMPLATES)


@fixture
def reference():
    """Return a reference of type 'journalArticle' with a dedicated 'key'."""
    ref = deepcopy(ARTICLE_TEMPLATE)
    ref["data"]["title"] = "Journal Article"
    ref["key"] = "01KEY2AZ"
    return ref


@fixture
def reference_book():
    """Return a reference of type 'book'."""
    return deepcopy(BOOK_TEMPLATE)


@fixture
def item_types():
    """Return the expected item_types from Zotero.item_types()."""
    return deepcopy(ITEM_TYPES)


# Fixtures related to the ZoteroWrap instances.


LIBRARY_ID = "id"
LIBRARY_TYPE = "type"
API_KEY = "key"


@fixture
def cache_filename():
    """Return the name of the file used for caching the ZoteroWrap data."""
    return "{}-{}-{}.pkl".format(LIBRARY_ID, LIBRARY_TYPE, API_KEY)


@fixture(scope="class")
def shared_directory(tmpdir_factory):
    """Return a temporary directory shared by all the methods of the test class."""
    return str(tmpdir_factory.mktemp("zotero"))


# Fixtures for the ZoteroWrap instances.


@fixture
def zw(tmpdir, references, reference_types, reference_templates):
    """Return an initialized ZoteroWrap instance with a temporary directory."""
    zww = ZoteroWrap(LIBRARY_ID, LIBRARY_TYPE, API_KEY, str(tmpdir))
    zww._references = references
    zww.reference_types = reference_types
    zww.reference_templates = reference_templates
    return zww


@fixture
def zw0(tmpdir):
    """Return a non initialized ZoteroWrap instance with a temporary directory."""
    return ZoteroWrap(LIBRARY_ID, LIBRARY_TYPE, API_KEY, str(tmpdir))


@fixture
def zw0_shared(shared_directory):
    """Return a non initialized ZoteroWrap instance with a shared temporary directory."""
    return ZoteroWrap(LIBRARY_ID, LIBRARY_TYPE, API_KEY, shared_directory)
