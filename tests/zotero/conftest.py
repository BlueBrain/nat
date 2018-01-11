__author__ = "Pierre-Alexandre Fonta"
__maintainer__ = "Pierre-Alexandre Fonta"

import os

from pytest import fixture

from nat.zotero_wrap import ZoteroWrap


# Common.


LIBRARY_ID = "427244"
LIBRARY_TYPE = "group"
API_KEY = "4D3rDZsAVBd139alqoVZBKOO"
WORK_DIR = os.path.join(os.path.dirname(__file__), "data")


@fixture(scope="class")
def zw():
    """Return an initialized ZoteroWrap instance."""
    zotero_wrap = ZoteroWrap(LIBRARY_ID, LIBRARY_TYPE, API_KEY, WORK_DIR)
    zotero_wrap.load_cache()
    return zotero_wrap


@fixture(scope="class")
def zw_not_initialized():
    """Return a not initialized ZoteroWrap instance."""
    zotero_wrap = ZoteroWrap(LIBRARY_ID, LIBRARY_TYPE, API_KEY, WORK_DIR)
    return zotero_wrap


@fixture(scope="class")
def idx(zw):
    """Return the index of a generic reference.

    It is of type 'journalArticle'.
    It has 'data', 'itemType', 'key', 'title', 'date', 'publicationTitle' fields.
    """
    return zw.reference_index("PMID_7965855")


# reference_extra_field


@fixture(scope="class")
def idx_extra_one(zw):
    """Return the index of a reference with one extra field."""
    return zw.reference_index("PMID_8174288")


@fixture(scope="class")
def idx_extra_several(zw):
    """Return the index of a reference with several extra fields."""
    return zw.reference_index("PMID_7965855")


@fixture(scope="class")
def idx_extra_empty(zw):
    """Return the index of a reference with no extra field."""
    return zw.reference_index("10.1093/cercor/bhr356")


# reference_doi


@fixture(scope="class")
def idx_doi(zw):
    """Return the index of a reference with a DOI."""
    return zw.reference_index("10.1093/cercor/bhr356")


@fixture(scope="class")
def idx_doi_extra(zw):
    """Return the index of a reference with a DOI as an extra field."""
    return zw.reference_index("10.1016/B978-0-12-374245-2.00024-3")


@fixture(scope="class")
def idx_doi_without(zw):
    """Return the index of a reference with no DOI.

    DOI neither in the dedicated field nor as an extra field."""
    return zw.reference_index("PMID_7965855")


# reference_pmid


@fixture(scope="class")
def idx_pmid(zw):
    """Return the index of a reference with a PMID as an extra field."""
    return zw.reference_index("PMID_7965855")


@fixture(scope="class")
def idx_pmid_without(zw):
    """Return the index of a reference with no PMID."""
    return zw.reference_index("10.1093/cercor/bhr356")


# reference_unpublished_id


@fixture(scope="class")
def idx_unpublished(zw):
    """Return the index of a reference with an UNPUBLISHED ID as an extra field."""
    return zw.reference_index("UNPUBLISHED_5b06d66a-85be-11e7-9105-64006a67e5d0")


@fixture(scope="class")
def idx_unpublished_without(zw):
    """Return the index of a reference with no UNPUBLISHED ID."""
    return zw.reference_index("PMID_7965855")


# reference_id


@fixture(scope="class")
def idx_id_without(zw):
    """Return the index of a reference with no ID (DOI, PMID, UNPUBLISHED ID)."""
    return zw.reference_index("")


# reference_creator_surnames
# reference_creator_surnames_str


@fixture(scope="class")
def idx_creators_one_author(zw):
    """Return the index of a reference with one creator of type 'author'."""
    return zw.reference_index("10.1113/jphysiol.2001.013283")


@fixture(scope="class")
def idx_creators_two_authors(zw):
    """Return the index of a reference with two creators of type 'author'."""
    return zw.reference_index("10.1016/B978-0-12-374245-2.00024-3")


@fixture(scope="class")
def idx_creators_several_not_authors(zw):
    """Return the index of a reference with several creators which aren't of type 'author'."""
    return zw.reference_index("10.1007/978-1-4939-2975-7")


@fixture(scope="class")
def idx_creators_several_mixed(zw):
    """Return the index of a reference with several creators of type 'author' and not."""
    return zw.reference_index("10.1007/978-1-4614-7320-6_478-1")


# reference_date


@fixture(scope="class")
def idx_date_empty(zw):
    """Return the index of a reference with no date."""
    return zw.reference_index("10.1016/j.neuron.2017.01.031")


# reference_year


@fixture(scope="class")
def idx_year(zw):
    """Return the index of a reference with a year recognized by dateutil.parser.parse()."""
    return zw.reference_index("PMID_7965855")


@fixture(scope="class")
def idx_year_unrecognized(zw):
    """Return the index of a reference with a year not recognized by dateutil.parser.parse()."""
    return zw.reference_index("10.1371/journal.pcbi.1005507")


@fixture(scope="class")
def idx_year_without(zw):
    """Return the index of a reference with no year (because no date)."""
    return zw.reference_index("10.1016/j.neuron.2017.01.031")


# reference_journal


@fixture(scope="class")
def idx_journal(zw):
    """Return the index of a reference with a journal."""
    return zw.reference_index("PMID_7965855")


@fixture(scope="class")
def idx_journal_without(zw):
    """Return the index of a reference with no journal (because not of type 'journalArticle')."""
    return zw.reference_index("10.1007/978-1-4939-2975-7")


# reference_index


@fixture(scope="class")
def ref_index_one_found():
    """Return the reference ID of a reference in the reference list."""
    return "PMID_7965855"


@fixture(scope="class")
def ref_index_several_found():
    """Return the reference ID of a duplicated reference in the reference list."""
    return "PMID_11116226"


@fixture(scope="class")
def ref_index_not_found():
    """Return the reference ID of a reference not in the reference list."""
    return "PMID_29061702"


# reference_creators_citation


@fixture(scope="class")
def ref_creators_one_author(zw, idx_creators_one_author):
    """Return the reference ID of a reference with one creator of type 'author'."""
    return zw.reference_id(idx_creators_one_author)


@fixture(scope="class")
def ref_creators_two_authors(zw, idx_creators_two_authors):
    """Return the reference ID of a reference with two creators of type 'author'."""
    return zw.reference_id(idx_creators_two_authors)


@fixture(scope="class")
def ref_creators_three_authors():
    """Return the reference ID of a reference with three creators of type 'author'."""
    return "PMID_1662262"
