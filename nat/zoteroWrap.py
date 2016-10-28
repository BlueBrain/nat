#!/usr/bin/python3

__author__ = "Christian O'Reilly"

import pickle
from pyzotero import zotero
import os

class ZoteroWrap:

    def __init__(self, checkIdFct):

        self.refList = []

    def loadCachedDB(self, libraryId, libraryrType, apiKey):
        try:
            fileName = os.path.join(os.path.dirname(__file__), libraryId + 
                                    "-" + libraryrType + "-" + apiKey + ".pkl")            
            with open(fileName, 'rb') as f:
                self.refList = pickle.load(f)
        except:
            self.refreshDB(libraryId, libraryrType, apiKey)


    def refreshDB(self, libraryId, libraryrType, apiKey):
        zotLib = zotero.Zotero(libraryId, libraryrType, apiKey)
        self.refList = [i['data'] for i in zotLib.everything(zotLib.top())]

        fileName = os.path.join(os.path.dirname(__file__), libraryId + 
                                "-" + libraryrType + "-" + apiKey + ".pkl")   
        with open(fileName, 'wb') as f:
            pickle.dump(self.refList, f)

    def getID(self, index):
        return self.getID_fromRef(self.refList[index])


    def getID_fromRef(self, ref):
        DOI = self.getDOI_fromRef(ref)
        PMID = self.getPMID_fromRef(ref)
        if DOI != "":
            return DOI
        elif PMID != "":
            return "PMID_" + PMID
        else:
            return ""    


    def getDOI(self, index):
        return self.getDOI_fromRef(self.refList[index])

    def getDOI_fromRef(self, ref):

        # Standard way
        if "DOI" in ref:
            if ref["DOI"] != "":
                return ref["DOI"]

        # Some book chapter as a DOI but Zotero does not have DOI field
        # for book chapter type of publication. In these case, the DOI
        # can be added to the extra field as done for the PMID in pubmed.
        if "extra" in ref:
            for line in ref["extra"].split("\n"):
                if "DOI" in line:
                    return line.split("DOI:")[1].strip()

        return ""


    def getPMID(self, index):
        return self.getPMID_fromRef(self.refList[index])

    def getPMID_fromRef(self, ref):
        try:
            for line in ref["extra"].split("\n"):
                if "PMID" in line:
                    return line.split("PMID:")[1].strip()
            return ""
        except KeyError:
            return ""



