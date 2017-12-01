#!/usr/bin/python3

__authors__ = ["Pierre-Alexandre Fonta", "Christian O'Reilly"]
__maintainer__ = "Pierre-Alexandre Fonta"

import os
import pickle
import re
from collections import OrderedDict
from datetime import datetime

from dateutil.parser import parse
from pyzotero.zotero import Zotero


class ZoteroWrap:

    CACHE_REFERENCE_LIST = "references"
    CACHE_REFERENCE_TYPES = "reference_types"
    CACHE_REFERENCE_TEMPLATES = "reference_templates"

    def __init__(self, library_id, library_type, api_key, working_directory):
        cache_filename = library_id + "-" + library_type + "-" + api_key + ".pkl"
        self.cache_path = os.path.join(working_directory, cache_filename)
        # reference_types and reference_templates must have the same ordering.
        self.reference_types = []
        self.reference_templates = {}
        self._zotero_lib = Zotero(library_id, library_type, api_key)
        self._references = []

    # Load / Refresh / Save methods section.

    def initialize(self):
        try:
            self.load_cache()
        except FileNotFoundError:
            self.load_distant()

    def load_cache(self):
        print("Load cached Zotero database...")
        with open(self.cache_path, "rb") as f:
            cache = pickle.load(f)
            self._references = cache[self.CACHE_REFERENCE_LIST]
            self.reference_types = cache[self.CACHE_REFERENCE_TYPES]
            self.reference_templates = cache[self.CACHE_REFERENCE_TEMPLATES]
        print("Cached Zotero database loaded.")

    def load_distant(self):
        print("Loading distant Zotero database...")
        self._references = self.get_references()
        self.reference_types = self.get_reference_types()
        self.reference_templates = self.get_reference_templates(self.reference_types)
        print("Distant Zotero database loaded.")
        self.cache()

    def cache(self):
        with open(self.cache_path, "wb") as f:
            cache = {self.CACHE_REFERENCE_LIST: self._references,
                     self.CACHE_REFERENCE_TYPES: self.reference_types,
                     self.CACHE_REFERENCE_TEMPLATES: self.reference_templates}
            pickle.dump(cache, f)

    def create_local_reference(self, valid_ref):
        self._references.append(valid_ref)
        self.cache()

    def create_distant_reference(self, ref_data):
        self.validate_reference_data(ref_data)
        creation_status = self._zotero_lib.create_items([ref_data])
        try:
            created_key = creation_status["success"]["0"]
            return created_key
        except KeyError:
            raise CreateZoteroItemError

    def update_local_reference(self, index, valid_ref):
        self._references[index] = valid_ref
        self.cache()

    def update_distant_reference(self, ref):
        self.validate_reference_data(ref["data"])
        # NB: Existing fields not present will be left unmodified.
        self._zotero_lib.update_item(ref)

    def validate_reference_data(self, ref_data):
        try:
            # NB: Data are cached after the first API call.
            self._zotero_lib.check_items([ref_data])
        except KeyError:
            raise InvalidZoteroItemError

    def get_references(self):
        # Takes time...
        return self._zotero_lib.everything(self._zotero_lib.top())

    def get_reference_types(self):
        # NB: Data are cached after the first API call.
        item_types = self._zotero_lib.item_types()
        return sorted([x["itemType"] for x in item_types])

    def get_reference_templates(self, ref_types):
        """Return the templates for the given types in an ordered dictionary."""
        return OrderedDict({x: self.get_reference_template(x) for x in ref_types})

    def get_reference_template(self, ref_type):
        """Return the template for the given type in an ordered dictionary."""
        # NB: Data are cached after the first API call.
        template = self._zotero_lib.item_template(ref_type)
        return OrderedDict(sorted(template.items(), key=lambda x: x[0]))

    def get_reference(self, ref_key):
        return self._zotero_lib.item(ref_key)

    # Public @properties surrogates section.

    def reference_count(self):
        return len(self._references)

    def reference_data(self, index):
        return self._references[index]["data"]

    def reference_key(self, index):
        return self._references[index]["key"]

    def reference_id(self, index):
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
        return self.reference_data(index).get("DOI", self.reference_extra_field("DOI", index))

    def reference_pmid(self, index):
        return self.reference_extra_field("PMID", index)

    def reference_unpublished_id(self, index):
        return self.reference_extra_field("UNPUBLISHED", index)

    def reference_title(self, index):
        return self.reference_data(index)["title"]

    def reference_creator_surnames_str(self, index):
        creator_surnames = self.reference_creator_surnames(index)
        if creator_surnames:
            return ", ".join(creator_surnames)
        else:
            return ""

    def reference_creator_surnames(self, index):
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

    def reference_date(self, index):
        return self.reference_data(index)["date"]

    def reference_year(self, index):
        # TODO Use meta:parsedDate field instead?
        ref_date = self.reference_date(index)
        try:
            # Use datetime.min for a common representation of missing fields.
            return parse(ref_date, default=datetime.min).year
        except ValueError:
            matched = re.search(r"\d{4}", ref_date)
            if matched:
                return int(matched.group())
            else:
                return ""

    def reference_journal(self, index):
        # TODO Change the column name "Journal" to an other?
        ref_type = self.reference_type(index)
        if ref_type == "journalArticle":
            return self.reference_data(index)["publicationTitle"]
        else:
            return "({})".format(ref_type)

    def reference_type(self, index):
        return self.reference_data(index)["itemType"]

    def reference_extra_field(self, field, index):
        """Return the value associated with the field "field", otherwise ""."""
        ref_data = self.reference_data(index)
        if "extra" in ref_data:
            extra_fields = ref_data["extra"].split("\n")
            field_id = field + ":"
            matched = next((x for x in extra_fields if x.startswith(field_id)), None)
            if matched:
                return matched.replace(field_id, "", 1).strip()
        return ""

    # Public methods section.

    def reference_index(self, ref_id):
        try:
            indexes = range(len(self._references))
            return next((i for i in indexes if self.reference_id(i) == ref_id))
        except StopIteration:
            raise ReferenceNotFoundError("ID: " + ref_id)

    def reference_creators_citation(self, ref_id):
        # FIXME Delayed refactoring. Use a row number instead.
        index = self.reference_index(ref_id)
        creators = self.reference_creator_surnames(index)
        year = self.reference_year(index)
        creator_count = len(creators)
        if creator_count == 0:
            return ""
        if creator_count == 1:
            return "{}, ({})".format(creators[0], year)
        elif creator_count == 2:
            return "{} and {}, ({})".format(creators[0], creators[1], year)
        else:
            return "{} et al., ({})".format(creators[0], year)


class CreateZoteroItemError(Exception):
    """Raise if Zotero.create_items() fails."""

    pass


class InvalidZoteroItemError(Exception):
    """Raise if Zotero.check_items() fails."""

    pass


class ReferenceNotFoundError(Exception):

    pass
