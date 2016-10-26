#!/usr/bin/python3

__author__ = "Christian O'Reilly"

import urllib
from bs4 import BeautifulSoup
from dateutil.parser import parse
import re

try:
    from .utils import Id2FileName
except SystemError:
    from nat.utils import Id2FileName

def getPMIDSoup(PMID):
    url = "http://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?tool=neurocurator&email=christian.oreilly@epfl.ch&ids=" + PMID + "&format=json&versions=no"
    return getSoup(url)
 
def getDOISoup(DOI): 
    url = "http://doi.org/api/handles/" + DOI
    return getSoup(url)
 
 
def getSoup(url):
    try:
        with urllib.request.urlopen(url) as response:
           html = response.read()
    except urllib.error.HTTPError:
        return None
    
    return BeautifulSoup(html, "lxml")    
     
 
 
def getIDfromPMID(PMID):
    soup = getPMIDSoup(PMID)
    if soup is None:
        return None
    
    jsonStr = eval(str(soup)[15:-19])
    if jsonStr["status"] == "ok":
        if "doi" in jsonStr["records"][0]:
            return jsonStr["records"][0]["doi"]
        else:
            return "PMID_" + PMID
    else:
        return None

    



def getInfoFromID(ID): 
    if "PMID" in ID:
        idKind, PMID = ID.split("_")
        return getInfoFromPMID(PMID)
    else:
        DOI = Id2FileName(ID)        
        return getInfoFromDOI(DOI)



def getYear(dateStr):
    if dateStr == "":
        return ""
    else:
        try:
            return str(parse(dateStr).year)
        except ValueError:
            return re.search(r'[12]\d{3}', dateStr).group(0)

def getInfoFromPMID(PMID):
    soup = getSoup("https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=pubmed&id=" + PMID + "&retmode=json")
    if soup is None:
        return None

    result = eval(str(soup)[15:-19])["result"]
    if PMID not in result:
        return None
    
    authors = "; ".join([author["name"] for author in result[PMID]["authors"] 
                                        if author["authtype"] == "Author"])
    retData = {"authors":authors,
               "journal":result[PMID]['fulljournalname'],
               "year":getYear(result[PMID]['pubdate']),    
               "issue":result[PMID]['issue'], 
               "volume":result[PMID]['volume'],
               "title":result[PMID]['title']} 

    return retData



def getInfoFromDOI(DOI):
    soup = getSoup("http://api.crossref.org/works/" + DOI)
    if soup is None:
        return None
    soup = str(soup)[15:-18]       
    soup = soup.replace("true", "True")
    soup = soup.replace("false", "False")
    soup = eval(soup)["message"]
    
    authors = "; ".join([author["family"] + ", " + author["given"] for author in soup["author"]])   
    year    = soup["issued"]["date-parts"][0][0]
    #try:
    #    year    = soup["published-print"]["date-parts"][0][0]
    #except KeyError:
    #    print(list(soup.keys()))
    #    print(list(soup["issued"]['date-parts']))
    #    print(list(soup["published-online"]['date-parts']))
    
    retData = {"authors":authors,
               "journal":soup["container-title"][0],
               "year":year,    
               "title":soup["title"][0]}     
    
    retData["issue"]  = soup["issue"] if "issue" in soup else ""
    retData["volume"] = soup["volume"] if "volume" in soup else ""

    return retData 
 



def checkID(ID): 
    if "PMID" in ID:
        return checkPMID(ID)
    else:
        return checkDOI(ID)


def checkPMID(ID):
    idKind, PMID = ID.split("_")
    soup = getPMIDSoup(PMID)
    if soup is None:
        return False
     
    return eval(str(soup)[15:-19])["status"] == "ok"



def checkDOI(DOI):
    DOI = Id2FileName(DOI)
    soup = getDOISoup(DOI)
    if soup is None:
        return False

    # For some reason the "soup" string sometime contrains 
    # dictionnary entries with values that are equare to 
    # 'true' instead of 'True' which cannot be processed
    # by the python's eval function.
    soup = str(soup)[15:-18].replace("true", "True")
    return eval(soup)["responseCode"] == 1




if __name__ == "__main__":
    #print(checkPMID("PMID_3303249260")) # False
    #print(checkPMID("PMID_3309260")) # True
    #print(checkPMID("PMID_26601117")) # True
    #print(checkPMID("PMID_26584868")) # True

    getInfoFromID("PMID_3309260")
    getInfoFromID("10.1126/science.1207502")
    getInfoFromID("10.1371/journal.pone.0107780")
    
    