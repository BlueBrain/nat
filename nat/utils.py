# -*- coding: utf-8 -*-
"""
Created on Wed Mar 16 12:12:13 2016

@author: oreilly
"""

from glob import glob 
from copy import copy
from os.path import basename
import os 



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
encoders["zotLT" ]       = ("&lt;", "%3C")
encoders["zotGT" ]       = ("&gt;", "%3E")




def Id2FileName(ID):
    # Replacement characters according to http://www.doi.org/factsheets/DOIProxy.html#rest-api
    # but "%" signs must be replaced first since they are involved in the other replaced characters.
    if '%' in ID:
        ID = ID.replace('%', '%25')    
    
    for key, (symbol, replacement) in encoders.items():
        #if 
        #assert(not replacement in ID)
        ID = ID.replace(symbol, replacement)
    return ID



def fileName2Id(fileName):
    for key, (symbol, replacement) in encoders.items():
        assert(not symbol in fileName)
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

if __name__ == "__main__":
    reprocessFileNames('/home/oreilly/GIT_repos/nat/notebooks/neurocuratorDB/')