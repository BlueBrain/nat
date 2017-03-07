#!/usr/bin/python3

__author__ = "Christian O'Reilly"

import pickle
from pyzotero import zotero
import os
from collections import OrderedDict

class ZoteroWrap:

    def __init__(self):
        self.refList = []
        self.__zotLib = None

    def loadCachedDB(self, libraryId, libraryType, apiKey):        
        try:
            fileName = os.path.join(os.path.dirname(__file__), libraryId + 
                                    "-" + libraryType + "-" + apiKey + ".pkl")            
            with open(fileName, 'rb') as f:
                pickleObj = pickle.load(f)
                self.__zotLib      = pickleObj["zotLib"] 
                self.refList       = pickleObj["refList"]
                self.itemTypes     = pickleObj["itemTypes"]  
                self.itemTemplates = pickleObj["itemTemplates"]  

            self.libraryId    = libraryId
            self.libraryType  = libraryType
            self.apiKey       = apiKey                
        except:
            self.refreshDB(libraryId, libraryType, apiKey)


    @property 
    def zotLib(self):
        if self.__zotLib is None:
            self.refreshDB(self.libraryId, self.libraryType, self.apiKey)
        return self.__zotLib



    def refreshDB(self, libraryId, libraryType, apiKey):
        self.libraryId    = libraryId
        self.libraryType  = libraryType
        self.apiKey       = apiKey

        self.__zotLib = zotero.Zotero(libraryId, libraryType, apiKey)        
        self.refList = [i['data'] for i in self.__zotLib.everything(self.__zotLib.top())]
        self.itemTypes = self.__zotLib.item_types()
        self.itemTemplates = OrderedDict([(t["itemType"], self.__zotLib.item_template(t["itemType"])) for t in self.itemTypes])
  
        self.savePickle()
                

    def savePickle(self):        
        fileName = os.path.join(os.path.dirname(__file__), self.libraryId + 
                                "-" + self.libraryType + "-" + self.apiKey + ".pkl") 
                        
        with open(fileName, 'wb') as f:
            pickle.dump({"refList":self.refList, 
                         "zotLib":self.__zotLib,
                         "itemTypes":self.itemTypes, 
                         "itemTemplates":self.itemTemplates}, f)
                         

    def getID(self, index):
        return self.getID_fromRef(self.refList[index])


    def getID_fromRef(self, ref):               
        DOI             = self.getDOI_fromRef(ref)
        PMID            = self.getPMID_fromRef(ref)
        UNPUBLISHEDID   = self.getUNPUBLISHEDID_fromRef(ref)
        if DOI != "":
            return DOI
        if PMID != "":
            return "PMID_" + PMID
        if UNPUBLISHEDID != "":
            return "UNPUBLISHED_" + UNPUBLISHEDID            
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

    def getUNPUBLISHEDID(self, index):
        return self.geUNPUBLISHEDMID_fromRef(self.refList[index])

    def getUNPUBLISHEDID_fromRef(self, ref):
        try:
            for line in ref["extra"].split("\n"):
                if "UNPUBLISHED" in line:
                    return line.split("UNPUBLISHED:")[1].strip()
            return ""
        except KeyError:
            return ""
