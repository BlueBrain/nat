# -*- coding: utf-8 -*-
"""
Created on Wed Mar 16 12:12:13 2016

@author: oreilly
"""

import os
from copy import copy
from glob import glob
from os.path import basename


def data_directory():
    """Return the absolute path to the directory containing the package data."""
    package_directory = os.path.abspath(os.path.dirname(__file__))
    return os.path.join(package_directory, "data")


def data_path(filename):
    """Return the absolute path to a file in the directory containing the package data."""
    return os.path.join(data_directory(), filename)



# See http://www.w3schools.com/tags/ref_urlencode.asp for list of encoders

# Records associated with publications are saved with a file name using the ID
# However, ID (e.g., DOI) may contain the forward slash ("/") character which is not allowed
# in file names. It is therefore replaced by the character hereby specified 
# everytime the ID has to be used for naming files.
encoders                 = {} 
encoders["forwardSlash"] = ("/", "%2F")
encoders["colon"]        = (":", "%3A")
encoders["greater"]      = (">", "%3E")
encoders["smaller"]      = ("<", "%3C")
encoders["doubleQuote"]  = ('"', "%22")
encoders["hash"]         = ("#", "%23")
encoders["space"]        = (" ", "%20")
encoders["iterog"]       = ("?", "%3F")
encoders["curlyStart"]   = ("{", "%7B")
encoders["curlyEnd"]     = ("}", "%7D")
encoders["hat"]          = ("^", "%5E")
encoders["squareStart"]  = ("[", "%5B")
encoders["squareEnd"]    = ("]", "%5D")
encoders["grave"]        = ("`", "%60")
encoders["bar"]          = ("|", "%7C")
encoders["backSlash"]    = ("\\", "%5C")
encoders["plus"]         = ("+", "%2B")

# When Zotero imports from pubmed, it uses the "&lt;" for "<" and "&gt;" for ">"
# so we also replace these.
encoders["zotLT" ]       = ("&lt;", "%_3C_")
encoders["zotGT" ]       = ("&gt;", "%_3E_")

def Id2FileName(ID):
    # Replacement characters according to http://www.doi.org/factsheets/DOIProxy.html#rest-api
    # but "%" signs must be replaced first since they are involved in the other replaced characters.
    #if '%' in ID:
    #    ID = ID.replace('%', '%25')    
    
    for key, (symbol, replacement) in encoders.items():
        #if 
        #assert(not replacement in ID)
        ID = ID.replace(symbol, replacement)
    return ID



def fileName2Id(fileName):
    for key, (symbol, replacement) in encoders.items():
        #assert(not symbol in fileName)
        #if symbol in [">", "<"]:
        #    # We don't use these symbols. We use instead the &gt; and &lt; encoders.
        #    continue
        fileName = fileName.replace(replacement, symbol)
    return fileName
    
    
    
def reprocessFileNames(path = "/home/oreilly/curator_DB/"):
    for f in glob(path + "*"):   
        f_in  = basename(f)
        f_out = copy(f_in) 
        for key, (symbol, replacement) in encoders.items():
            f_out = f_out.replace(symbol, replacement)
            if f_in != f_out:
                print(f_in, " ===> ", f_out)
                os.rename(path + f_in, 
                          path + f_out)


from .zotero_wrap import ZoteroWrap
def test_ID_conversion():        
    library_type = "group"
    api_key = "4D3rDZsAVBd139alqoVZBKOO"
    library_id = "427244"
    work_dir = data_directory()
    zot_wrap = ZoteroWrap(library_id, library_type, api_key, work_dir)
    # TODO Implement an offline mode. Catch PyZoteroError.
    zot_wrap.initialize()
    # FIXME Delayed refactoring. _references is private.
    idList = [zot_wrap.reference_id(no) for no in range(len(zot_wrap._references))]
    idList2 = [Id2FileName(id) for id in idList]
    idList3 = [Id2FileName(id) for id in idList2]
    assert(idList2 == idList3)
    idList4 = [fileName2Id(id) for id in idList3]
    idList5 = [fileName2Id(id) for id in idList4]
    assert(idList4 == idList5)
    assert(idList == idList5)


if __name__ == "__main__":
    reprocessFileNames('/home/oreilly/GIT_repos/nat/notebooks/neurocuratorDB/')
