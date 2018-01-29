__authors__ = ["Pierre-Alexandre Fonta", "Christian O'Reilly"]
__maintainer__ = "Pierre-Alexandre Fonta"

import os
import pickle
import re
from collections import OrderedDict

from dateutil.parser import parse
from pyzotero.zotero import Zotero
from pyzotero.zotero_errors import InvalidItemFields


class ZoteroWrap:

    CACHE_REFERENCE_LIST = "references"
    CACHE_REFERENCE_TYPES = "reference_types"
    CACHE_REFERENCE_TEMPLATES = "reference_templates"

    def __init__(self, library_id, library_type, api_key, directory):
        cache_filename = "{}-{}-{}.pkl".format(library_id, library_type, api_key)
        self.cache_path = os.path.join(directory, cache_filename)
        # reference_types and reference_templates must have the same ordering.
        self.reference_types = []
        self.reference_templates = {}
        self._zotero_lib = Zotero(library_id, library_type, api_key)
        self._references = []

    # Data I/O methods section.

    def initialize(self):
        """Load the cached Zotero data, or retrieve them if there is none."""
        try:
            self.load_cache()
        except FileNotFoundError:
            self.load_distant()

    def load_cache(self):
        """Load the cached Zotero data."""
        print("Loading cached Zotero data...")
        with open(self.cache_path, "rb") as f:
            cache = pickle.load(f)
            self._references = cache[self.CACHE_REFERENCE_LIST]
            self.reference_types = cache[self.CACHE_REFERENCE_TYPES]
            self.reference_templates = cache[self.CACHE_REFERENCE_TEMPLATES]
        print("Cached Zotero data loaded.")

    def load_distant(self):
        """Load the distant Zotero data."""
        print("Loading distant Zotero data...")
        self._references = self.get_references()
        self.reference_types = self.get_reference_types()
        self.reference_templates = self.get_reference_templates(self.reference_types)
        print("Distant Zotero data loaded.")
        self.cache()

    def cache(self):
        """Cache the Zotero data."""
        with open(self.cache_path, "wb") as f:
            cache = {self.CACHE_REFERENCE_LIST: self._references,
                     self.CACHE_REFERENCE_TYPES: self.reference_types,
                     self.CACHE_REFERENCE_TEMPLATES: self.reference_templates}
            pickle.dump(cache, f)

    def create_local_reference(self, ref):
        """Append the reference at the end of the reference list and cache it."""
        self._references.append(ref)
        self.cache()

    def create_distant_reference(self, ref_data):
        """Validate and create the reference in Zotero and return the created item."""
        self.validate_reference_data(ref_data)
        creation_status = self._zotero_lib.create_items([ref_data])
        try:
            created_item = creation_status["successful"]["0"]
            return created_item
        except KeyError as e:
            print(creation_status)
            raise CreateZoteroItemError from e

    def update_local_reference(self, index, ref):
        """Replace the reference in the reference list and cache it."""
        self._references[index] = ref
        self.cache()

    def update_distant_reference(self, ref):
        """Validate and update the reference in Zotero.

        Existing fields not present will be left unmodified.
        """
        self.validate_reference_data(ref["data"])
        self._zotero_lib.update_item(ref)

    def validate_reference_data(self, ref_data):
        """Validate the reference data.

        Zotero.check_items() caches data after the first API call.
        """
        try:
            self._zotero_lib.check_items([ref_data])
        except InvalidItemFields as e:
            raise InvalidZoteroItemError from e

    def get_references(self):
        """Return all references in the Zotero database. Takes time..."""
        return self._zotero_lib.everything(self._zotero_lib.top())

    def get_reference_types(self):
        """Return the reference types.

        Zotero.item_types() caches data after the first API call.
        """
        item_types = self._zotero_lib.item_types()
        return sorted([x["itemType"] for x in item_types])

    def get_reference_templates(self, ref_types):
        """Return the reference templates for the types as an ordered dictionary."""
        return OrderedDict([(x, self.get_reference_template(x)) for x in ref_types])

    def get_reference_template(self, ref_type):
        """Return the reference template for the type as an ordered dictionary.

        Zotero.item_template() caches data after the first API call.
        """
        template = self._zotero_lib.item_template(ref_type)
        return OrderedDict(sorted(template.items(), key=lambda x: x[0]))

    def get_reference(self, ref_key):
        """Return the reference for the key."""
        return self._zotero_lib.item(ref_key)

    # Public @properties surrogates section.

    def reference_count(self):
        """Return the number of references."""
        return len(self._references)

    def reference_data(self, index):
        """Return the 'data' field of the reference."""
        return self._references[index]["data"]

    def reference_extra_field(self, field, index):
        """Return the value of the field in 'extra', otherwise ''."""
        ref_data = self.reference_data(index)
        extra_fields = ref_data["extra"].split("\n")
        field_id = field + ":"
        matched = next((x for x in extra_fields if x.startswith(field_id)), None)
        if matched:
            return matched.replace(field_id, "", 1).strip()
        else:
            return ""

    def reference_type(self, index):
        """Return the reference type."""
        return self.reference_data(index)["itemType"]

    def reference_key(self, index):
        """Return the reference key."""
        return self._references[index]["key"]

    def reference_id(self, index):
        """Return the reference ID (locally defined)."""
        # TODO Include ISBN and ISSN?
        doi = self.reference_doi(index)
        if doi:
            return doi
        else:
            pmid = self.reference_pmid(index)
            if pmid:
                return "PMID_" + pmid
            else:
                unpublished_id = self.reference_unpublished_id(index)
                if unpublished_id:
                    return "UNPUBLISHED_" + unpublished_id
        return ""

    def reference_doi(self, index):
        """Return the reference DOI."""
        return self.reference_data(index).get("DOI", self.reference_extra_field("DOI", index))

    def reference_pmid(self, index):
        """Return the reference PMID."""
        return self.reference_extra_field("PMID", index)

    def reference_unpublished_id(self, index):
        """Return the reference UNPUBLISHED ID."""
        return self.reference_extra_field("UNPUBLISHED", index)

    def reference_title(self, index):
        """Return the reference title."""
        return self.reference_data(index)["title"]

    def reference_creator_surnames(self, index):
        """Return as a list the surnames of the reference creators (locally defined)."""
        # TODO Not true, ex: ISBN 978-1-4398-3778-8. Return all creator types?
        # Academic books published as a collection of chapters contributed by
        # different authors have editors but not authors at the level of the
        # book (as opposed to the level of a chapter).
        creators = self.reference_data(index)["creators"]
        creator_types = [x["creatorType"] for x in creators]
        if "author" in creator_types:
            return [x["lastName"] for x in creators if x["creatorType"] == "author"]
        else:
            return [x["lastName"] for x in creators]

    def reference_creator_surnames_str(self, index):
        """Return as a string the surnames of the reference creators (locally defined)."""
        return ", ".join(self.reference_creator_surnames(index))

    def reference_date(self, index):
        """Return the reference publication date."""
        return self.reference_data(index)["date"]

    def reference_year(self, index):
        """Return the reference publication year."""
        # TODO Use meta:parsedDate field instead?
        ref_date = self.reference_date(index)
        try:
            # NB: datetime.year returns an int.
            return parse(ref_date).year
        except ValueError:
            matched = re.search(r"\d{4}", ref_date)
            if matched:
                return int(matched.group())
            else:
                return ""

    def reference_journal(self, index):
        """Return the reference journal name."""
        # TODO Change the column name 'Journal' to an other?
        ref_type = self.reference_type(index)
        if ref_type == "journalArticle":
            return self.reference_data(index)["publicationTitle"]
        else:
            return "({})".format(ref_type)

    # Public methods section.

    def reference_index(self, ref_id):
        """Return the first reference with this ID."""
        try:
            indexes = range(self.reference_count())
            return next(i for i in indexes if self.reference_id(i) == ref_id)
        except StopIteration as e:
            raise ReferenceNotFoundError("ID: " + ref_id) from e

    def reference_creators_citation(self, ref_id):
        """Return for citation the creator surnames (locally defined) and the publication year."""
        # FIXME Delayed refactoring. Use an index instead of an ID.
        index = self.reference_index(ref_id)
        creators = self.reference_creator_surnames(index)
        year = self.reference_year(index)
        creator_count = len(creators)
        if creator_count == 1:
            return "{} ({})".format(creators[0], year)
        elif creator_count == 2:
            return "{} and {} ({})".format(creators[0], creators[1], year)
        else:
            return "{} et al. ({})".format(creators[0], year)


class CreateZoteroItemError(Exception):
    """Raise if Zotero.create_items() fails."""

    pass


class InvalidZoteroItemError(Exception):
    """Raise if Zotero.check_items() fails."""

    pass


class ReferenceNotFoundError(Exception):

    pass
