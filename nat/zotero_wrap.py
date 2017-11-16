#!/usr/bin/python3

__authors__ = ["Pierre-Alexandre Fonta", "Christian O'Reilly"]
__maintainer__ = "Pierre-Alexandre Fonta"

import os
import pickle
import re
from datetime import datetime

from dateutil.parser import parse
from pyzotero.zotero import Zotero
from pyzotero.zotero_errors import PyZoteroError


class ZoteroWrap:
    """Wrapper around PyZotero to offer a user-oriented interface.

    Helpers instead of objects to get/set reference fields for performance.
    """

    def __init__(self, library_id, library_type, api_key, working_directory):
        cache_filename = library_id + "-" + library_type + "-" + api_key + ".pkl"
        self.cache_path = os.path.join(working_directory, cache_filename)
        self._zotero_lib = Zotero(library_id, library_type, api_key)
        self._references = []

    # load / refresh / save methods section.

    def initialize(self):
        try:
            self.load_cache()
        except FileNotFoundError:
            self.load_distant()

    def load_cache(self):
        with open(self.cache_path, "rb") as f:
            cache = pickle.load(f)
            self._references = cache["references"]
            # FIXME self.itemTypes = cached_db["itemTypes"]
            # FIXME self.itemTemplates = cached_db["itemTemplates"]
            # FIXME self._zotero = cached_db["zotLib"]

    def load_distant(self):
        # Takes time...
        self._references = self._zotero_lib.everything(self._zotero_lib.top())
        self.cache()
        # FIXME self.itemTypes = self.zotero_lib.item_types()
        # FIXME self.itemTemplates = OrderedDict([(t["itemType"], self.zotero_lib.item_template(t["itemType"])) for t in self.itemTypes])

    def cache(self):
        with open(self.cache_path, "wb") as f:
            cache = {"references": self._references}
            pickle.dump(cache, f)
            # FIXME "zotLib": self.zotero_lib,
            # FIXME "itemTypes": self.itemTypes,
            # FIXME "itemTemplates": self.itemTemplates}

    def create_empty_reference(self, ref_type):
        return self._zotero_lib.item_template(ref_type)

    def create_local_reference(self, index, ref):
        """If the reference is valid, add it in the local data and cache them.

        "index" is needed for neurocurator.ZoteroTableModel.insertRow().
        """
        valid_reference = self.valid_reference(ref)
        self._references.insert(index, valid_reference[0])
        self.cache()

    def create_distant_reference(self, index):
        """Add a local and valid reference to the distant Zotero library."""
        valid_reference = self._references[index]
        creation_status = self._zotero_lib.create_items([valid_reference])
        if len(creation_status["success"]) != 1:
            raise CreateZoteroItemError

    def update_local_reference(self, index, ref):
        """If the reference is valid, update it in the local data and cache them.

        Call update_distant_reference() before and handle properly it exception.
        """
        valid_reference = self.valid_reference(ref)
        self._references[index] = valid_reference
        self.cache()

    def update_distant_reference(self, index):
        """Update a local and valid reference in the distant Zotero library."""
        valid_reference = self._references[index]
        try:
            self._zotero_lib.update_item(valid_reference)
        except PyZoteroError:
            raise UpdateZoteroItemError

    def valid_reference(self, ref):
        """Return a valid representation of a reference or raise an exception."""
        try:
            return self._zotero_lib.check_items([ref])
        except KeyError:
            raise InvalidZoteroItemError

    # Public @properties surrogates section.

    def reference_count(self):
        return len(self._references)

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
        reference = self._references[index]
        return reference["data"].get("DOI", self.reference_extra_field("DOI", reference))

    def reference_pmid(self, index):
        reference = self._references[index]
        return self.reference_extra_field("PMID", reference)

    def reference_unpublished_id(self, index):
        reference = self._references[index]
        return self.reference_extra_field("UNPUBLISHED", reference)

    def reference_title(self, index):
        return self._references[index]["data"]["title"]

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
        creators = self._references[index]["data"]["creators"]
        creator_types = [c["creatorType"] for c in creators]
        if "author" in creator_types:
            return [c["lastName"] for c in creators if c["creatorType"] == "author"]
        else:
            return [c["lastName"] for c in creators]

    def reference_date(self, index):
        return self._references[index]["data"]["date"]

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
            return self._references[index]["data"]["publicationTitle"]
        else:
            type_words = [w.lower() for w in re.split("([A-Z][a-z]+)", ref_type) if w]
            return "({})".format(" ".join(type_words))

    def reference_extra_field(self, field, ref):
        """Return the value associated with the field "field", otherwise ""."""
        ref_data = ref["data"]
        if "extra" in ref_data:
            # TODO Check field "extra" formatting.
            extra_fields = ref_data["extra"].split("\n")
            field_id = field + ":"
            matched = next((f for f in extra_fields if f.startswith(field_id)), None)
            if matched:
                return matched.replace(field_id, "", 1).strip()
        return ""

    def set_reference_id(self, index, value):
        # FIXME Implement. See .addToZoteroDlg.IdWgt.setIdToReference().
        # FIXME No direct mapping with Zotero's data!
        raise NotImplementedError

    def set_reference_doi(self, index, value):
        # FIXME Implement.
        raise NotImplementedError

    def set_reference_pmid(self, index, value):
        # FIXME Implement.
        raise NotImplementedError

    def set_reference_unpublished_id(self, index, value):
        # FIXME Implement.
        raise NotImplementedError

    def set_reference_title(self, index, value):
        self._references[index]["data"]["title"] = value

    def set_reference_creators(self, index, value):
        # FIXME Implement.
        raise NotImplementedError

    def set_reference_date(self, index, value):
        # FIXME Implement.
        raise NotImplementedError

    def set_reference_year(self, index, value):
        # FIXME Implement.
        # FIXME No direct mapping with Zotero's data!
        raise NotImplementedError

    def set_reference_journal(self, index, value):
        # FIXME No direct mapping with Zotero's data for types different from "journalArticle"!
        self._references[index]["data"]["publicationTitle"] = value

    # Public methods section.

    def reference_type(self, index):
        return self._references[index]["data"]["itemType"]

    def reference_index(self, ref_id):
        # FIXME See reference_creators_citation().
        try:
            indexes = range(len(self._references))
            return next((i for i in indexes if self.reference_id(i) == ref_id))
        except StopIteration:
            raise ReferenceNotFoundError("ID: " + ref_id)

    def reference_creators_citation(self, ref_id):
        index = self.reference_index(ref_id)  # FIXME Delayed refactoring. See use.
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


class UpdateZoteroItemError(Exception):
    """Raise if Zotero.update_item() fails."""

    pass


class InvalidZoteroItemError(Exception):
    """Raise if Zotero.check_items() fails."""

    pass


class ReferenceNotFoundError(Exception):
    pass
