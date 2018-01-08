__author__ = "Pierre-Alexandre Fonta"
__maintainer__ = "Pierre-Alexandre Fonta"

from pytest import raises

from nat.zotero_wrap import ReferenceNotFoundError


class TestZoteroWrap:

    # FIXME Monkeypatch PyZotero calls, generate data instead using cached ones.
    # FIXME Parametrize test functions after monkeypatching PyZotero calls.
    # FIXME Comply with PEP 8 line length after test parametrizing test functions.

    # reference_count

    def test_reference_count_zw_initialized(self, zw):
        assert zw.reference_count() == 645

    def test_reference_count_zw_not_initialized(self, zw_not_initialized):
        assert zw_not_initialized.reference_count() == 0

    # reference_data

    def test_reference_data(self, zw, idx):
        # FIXME Find a way not to have this huge dict.
        idx_data = {'DOI': '',
                    'ISSN': '0022-3751',
                    'abstractNote': '1. Neurones enzymatically dissociated from the rat dorsal '
                                    'lateral geniculate nucleus (LGN) were identified as '
                                    'GABAergic local circuit interneurones and geniculocortical '
                                    'relay cells, based upon quantitative analysis of soma '
                                    'profiles, immunohistochemical detection of GABA or glutamic '
                                    'acid decarboxylase, and basic electrogenic behaviour. 2. '
                                    'During whole-cell current-clamp recording, isolated LGN '
                                    'neurones generated firing patterns resembling those in '
                                    'intact tissue, with the most striking difference relating '
                                    'to the presence in relay cells of a Ca2+ action potential '
                                    'with a low threshold of activation, capable of triggering '
                                    'fast spikes, and the absence of a regenerative Ca2+ '
                                    'response with a low threshold of activation in local '
                                    'circuit cells. 3. Whole-cell voltage-clamp experiments '
                                    'demonstrated that both classes of LGN neurones possess at '
                                    'least two voltage-dependent membrane currents which operate '
                                    'in a range of membrane potentials negative to the threshold '
                                    'for generation of Na(+)-K(+)-mediated spikes: the T-type '
                                    'Ca2+ current (IT) and an A-type K+ current (IA). Taking '
                                    'into account the differences in membrane surface area, the '
                                    'average size of IT was similar in the two types of '
                                    'neurones, and interneurones possessed a slightly larger '
                                    'A-conductance. 4. In local circuit neurones, the ranges of '
                                    'steady-state inactivation and activation of IT and IA were '
                                    'largely overlapping (VH = 81.1 vs. -82.8 mV), both currents '
                                    'activated at around -70 mV, and they rapidly increased in '
                                    'amplitude with further depolarization. In relay cells, the '
                                    'inactivation curve of IT was negatively shifted along the '
                                    'voltage axis by about 20 mV compared with that of IA (Vh = '
                                    '-86.1 vs. -69.2 mV), and the activation threshold for IT '
                                    '(at -80 mV) was 20 mV more negative than that for IA. In '
                                    'interneurones, the activation range of IT was shifted to '
                                    'values more positive than that in relay cells (Vh = -54.9 '
                                    'vs. -64.5 mV), whereas the activation range of IA was more '
                                    'negative (Vh = -25.2 vs. -14.5 mV). 5. Under whole-cell '
                                    'voltage-clamp conditions that allowed the combined '
                                    'activation of Ca2+ and K+ currents, depolarizing voltage '
                                    'steps from -110 mV evoked inward currents resembling IT in '
                                    'relay cells and small outward currents indicative of IA in '
                                    'local circuit neurones. After blockade of IA with '
                                    '4-aminopyridine (4-AP), the same pulse protocol produced IT '
                                    'in both types of neurones. Under current clamp, 4-AP '
                                    'unmasked a regenerative membrane depolarization with a low '
                                    'threshold of activation capable of triggering fast spikes '
                                    'in local circuit neurones.(ABSTRACT TRUNCATED AT 400 WORDS)',
                    'accessDate': '2016-10-25T07:48:29Z',
                    'archive': '',
                    'archiveLocation': '',
                    'callNumber': '',
                    'collections': ['7TC2C724', 'TSSBTP2X'],
                    'creators': [{'creatorType': 'author', 'firstName': 'H C',
                                  'lastName': 'Pape'},
                                 {'creatorType': 'author', 'firstName': 'T',
                                  'lastName': 'Budde'},
                                 {'creatorType': 'author', 'firstName': 'R',
                                  'lastName': 'Mager'},
                                 {'creatorType': 'author',
                                  'firstName': 'Z F',
                                  'lastName': 'Kisvárday'}],
                    'date': '1994-8-1',
                    'dateAdded': '2016-10-25T07:48:29Z',
                    'dateModified': '2016-10-25T07:48:29Z',
                    'extra': 'PMID: 7965855\nPMCID: PMC1155662',
                    'issue': 'Pt 3',
                    'itemType': 'journalArticle',
                    'journalAbbreviation': 'J Physiol',
                    'key': 'BSAGS4P8',
                    'language': '',
                    'libraryCatalog': 'PubMed Central',
                    'pages': '403-422',
                    'publicationTitle': 'The Journal of Physiology',
                    'relations': {},
                    'rights': '',
                    'series': '',
                    'seriesText': '',
                    'seriesTitle': '',
                    'shortTitle': '',
                    'tags': [],
                    'title': 'Prevention of Ca(2+)-mediated action potentials in GABAergic local '
                             'circuit neurones of rat thalamus by a transient K+ current.',
                    'url': 'http://www.ncbi.nlm.nih.gov/pmc/articles/PMC1155662/',
                    'version': 631,
                    'volume': '478'}
        assert zw.reference_data(idx) == idx_data

    # reference_extra_field

    def test_reference_extra_field_one(self, zw, idx_extra_one):
        assert zw.reference_extra_field("NONE", idx_extra_one) == ""
        assert zw.reference_extra_field("PMID", idx_extra_one) == "8174288"

    def test_reference_extra_field_several(self, zw, idx_extra_several):
        assert zw.reference_extra_field("NONE", idx_extra_several) == ""
        assert zw.reference_extra_field("PMID", idx_extra_several) == "7965855"
        assert zw.reference_extra_field("PMCID", idx_extra_several) == "PMC1155662"

    def test_reference_extra_field_empty(self, zw, idx_extra_empty):
        assert zw.reference_extra_field("NONE", idx_extra_empty) == ""

    # reference_type

    def test_reference_type(self, zw, idx):
        assert zw.reference_type(idx) == "journalArticle"

    # reference_key

    def test_reference_key(self, zw, idx):
        assert zw.reference_key(idx) == "BSAGS4P8"

    # reference_doi

    def test_reference_doi(self, zw, idx_doi):
        assert zw.reference_doi(idx_doi) == "10.1093/cercor/bhr356"

    def test_reference_doi_extra(self, zw, idx_doi_extra):
        assert zw.reference_doi(idx_doi_extra) == "10.1016/B978-0-12-374245-2.00024-3"

    def test_reference_doi_without(self, zw, idx_doi_without):
        assert zw.reference_doi(idx_doi_without) == ""

    # reference_pmid

    def test_reference_pmid(self, zw, idx_pmid):
        assert zw.reference_pmid(idx_pmid) == "7965855"

    def test_reference_pmid_without(self, zw, idx_pmid_without):
        assert zw.reference_pmid(idx_pmid_without) == ""

    # reference_unpublished_id

    def test_reference_unpublished_id(self, zw, idx_unpublished):
        assert zw.reference_unpublished_id(idx_unpublished) == "5b06d66a-85be-11e7-9105-64006a67e5d0"

    def test_reference_unpublished_id_without(self, zw, idx_unpublished_without):
        assert zw.reference_unpublished_id(idx_unpublished_without) == ""

    # reference_id

    def test_reference_id_doi(self, zw, idx_doi):
        assert zw.reference_id(idx_doi) == "10.1093/cercor/bhr356"

    def test_reference_id_doi_extra(self, zw, idx_doi_extra):
        assert zw.reference_id(idx_doi_extra) == "10.1016/B978-0-12-374245-2.00024-3"

    def test_reference_id_pmid(self, zw, idx_pmid):
        assert zw.reference_id(idx_pmid) == "PMID_7965855"

    def test_reference_id_unpublished(self, zw, idx_unpublished):
        assert zw.reference_id(idx_unpublished) == "UNPUBLISHED_5b06d66a-85be-11e7-9105-64006a67e5d0"

    def test_reference_id_without(self, zw, idx_id_without):
        assert zw.reference_id(idx_id_without) == ""

    # reference_title

    def test_reference_title(self, zw, idx):
        title = ("Prevention of Ca(2+)-mediated action potentials in GABAergic "
                 "local circuit neurones of rat thalamus by a transient K+ current.")
        assert zw.reference_title(idx) == title

    # reference_creator_surnames

    def test_reference_creator_surnames_one_author(self, zw, idx_creators_one_author):
        assert zw.reference_creator_surnames(idx_creators_one_author) == ["Castro-Alamancos"]

    def test_reference_creator_surnames_two_authors(self, zw, idx_creators_two_authors):
        assert zw.reference_creator_surnames(idx_creators_two_authors) == ["Ebner", "Kaas"]

    def test_reference_creator_surnames_several_not_authors(self, zw, idx_creators_several_not_authors):
        assert zw.reference_creator_surnames(idx_creators_several_not_authors) == ["Krieger", "Groh"]

    def test_reference_creator_surnames_several_mixed(self, zw, idx_creators_several_mixed):
        assert zw.reference_creator_surnames(idx_creators_several_mixed) == ["Holmes"]

    # reference_creator_surnames_str

    def test_reference_creator_surnames_str_one(self, zw, idx_creators_one_author):
        assert zw.reference_creator_surnames_str(idx_creators_one_author) == "Castro-Alamancos"

    def test_reference_creator_surnames_str_two(self, zw, idx_creators_two_authors):
        assert zw.reference_creator_surnames_str(idx_creators_two_authors) == "Ebner, Kaas"

    # reference_date

    def test_reference_date(self, zw, idx):
        assert zw.reference_date(idx) == "1994-8-1"

    def test_reference_date_empty(self, zw, idx_date_empty):
        assert zw.reference_date(idx_date_empty) == ""

    # reference_year

    def test_reference_year(self, zw, idx_year):
        assert zw.reference_year(idx_year) == 1994

    def test_reference_year_unrecognized(self, zw, idx_year_unrecognized):
        assert zw.reference_year(idx_year_unrecognized) == 2017

    def test_reference_year_without(self, zw, idx_year_without):
        assert zw.reference_year(idx_year_without) == ""

    # reference_journal

    def test_reference_journal(self, zw, idx_journal):
        assert zw.reference_journal(idx_journal) == "The Journal of Physiology"

    def test_reference_journal_without(self, zw, idx_journal_without):
        assert zw.reference_journal(idx_journal_without) == "(book)"

    # reference_index

    def test_reference_index_one_found(self, zw, ref_index_one_found):
        # FIXME Break if source data change. Will not after parametrization.
        assert zw.reference_index(ref_index_one_found) == 278

    def test_reference_index_several_found(self, zw, ref_index_several_found):
        # Reference found at indexes 11 and 138.
        # FIXME Break if source data change. Will not after parametrization.
        assert zw.reference_index(ref_index_several_found) == 11

    def test_reference_index_not_found(self, zw, ref_index_not_found):
        exception_str = "^ID: {}$".format(ref_index_not_found)
        with raises(ReferenceNotFoundError, match=exception_str):
            zw.reference_index(ref_index_not_found)

    # reference_creators_citation

    def test_reference_creators_citation_one_author(self, zw, ref_creators_one_author):
        assert zw.reference_creators_citation(ref_creators_one_author) == "Castro-Alamancos (2002)"

    def test_reference_creators_citation_two_authors(self, zw, ref_creators_two_authors):
        assert zw.reference_creators_citation(ref_creators_two_authors) == "Ebner and Kaas (2015)"

    def test_reference_creators_citation_three_authors(self, zw, ref_creators_three_authors):
        assert zw.reference_creators_citation(ref_creators_three_authors) == "Huguenard et al. (1991)"

    def test_reference_creators_citation_index_not_found(self, zw, ref_index_not_found):
        with raises(ReferenceNotFoundError):
            zw.reference_creators_citation(ref_index_not_found)

    def test_reference_creators_citation_year_unrecognized(self, zw, idx_year_unrecognized):
        ref_id = zw.reference_id(idx_year_unrecognized)
        assert zw.reference_creators_citation(ref_id) == "Schwalger et al. (2017)"

    def test_reference_creators_citation_year_without(self, zw, idx_year_without):
        ref_id = zw.reference_id(idx_year_without)
        assert zw.reference_creators_citation(ref_id) == "Makinson et al. ()"

    def test_reference_creators_citation_several_not_authors(self, zw, idx_creators_several_not_authors):
        ref_id = zw.reference_id(idx_creators_several_not_authors)
        assert zw.reference_creators_citation(ref_id) == "Krieger and Groh (2015)"

    def test_reference_creators_citation_several_mixed(self, zw, idx_creators_several_mixed):
        ref_id = zw.reference_id(idx_creators_several_mixed)
        assert zw.reference_creators_citation(ref_id) == "Holmes (2014)"
