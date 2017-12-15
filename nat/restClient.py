# -*- coding: utf-8 -*-
"""
Created on Sun Jun  5 13:08:43 2016

@author: oreilly
"""

import requests   
import json
import os
import webbrowser
from bs4 import BeautifulSoup as bs
import io
from zipfile import ZipFile
import warnings


class RESTClientError(Exception):
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super(RESTClientError, self).__init__(message)


class RESTImportPDFErr(RESTClientError):
    def __init__(self, message):
        # Call the base class constructor with the parameters it needs
        super(RESTImportPDFErr, self).__init__(message)
        
        
class RESTClient:

    def __init__(self, serverURL):
        self.serverURL = serverURL

    def getContext(self, paperId, contextLength, annotStart, annotStr):
                
        response = requests.post(self.serverURL + "get_context", 
                                 json=json.dumps({"paperId"      : paperId, 
                                                  "annotStr"     : annotStr,
                                                  "contextLength": contextLength,
                                                  "annotStart"   : annotStart}))

        response = json.loads(response.content.decode("utf8"))
        
        if not "context" in response:
            print(warnings.warn(response["message"]))
            return ""
        return response["context"]        
        



    def importPDF(self, localPDF, paperId, pathDB):
        files = {"file": (os.path.basename(localPDF), open(localPDF, 'rb'), 'application/octet-stream'),
         "json": (None, json.dumps({"paperId": paperId}), 'application/json')}
 
        response = requests.post(#"http://httpbin.org/post", 
                                 self.serverURL + "import_pdf", 
                                 files=files, stream=True)

        if response.status_code == 200:
            zipDoc = ZipFile(io.BytesIO(response.content)) 
            zipDoc.extractall(pathDB)
            
        elif response.status_code == 201:            
            # Need to run OCR.   
            errMsg = "Optical character recognition needs to be run on this paper. " +\
                     "The process has been launched, but this process may take some" +\
                     " time (i.e., in the order of 10 minutes)."
            raise RESTImportPDFErr(errMsg)            
          
        else:
            path = os.path.abspath("error_log.html")
            url = 'file://' + path            
            soup=bs(response.content)                #make BeautifulSoup
            prettyHTML=soup.prettify()   #prettify the html
            with open(path, 'w') as f:
                f.write(prettyHTML)
            webbrowser.open(url)            

            raise AttributeError("REST server returned an error number " + 
                                 str(response.status_code) +
                                 "\Response content: " + str(response.content) +
                                 "\nRequest sent to the URL: " + self.serverURL + "import_pdf" +
                                 "\nContent of it 'files' argument: " + str(files))






    def checkOCRFinished(self, paperId, pathDB=None):
        files = {"json": (None, json.dumps({"paperId": paperId}), 'application/json')}
 
        response = requests.post(self.serverURL + "check_OCR_finished", 
                                 json=json.dumps({"paperId" : paperId}))

        if response.status_code == 200:
            if not pathDB is None:
                zipDoc = ZipFile(io.BytesIO(response.content)) 
                zipDoc.extractall(pathDB)
            return True            
            
        elif response.status_code == 201:
            return False
            
        else:
            path = os.path.abspath("error_log.html")
            url = 'file://' + path            
            soup=bs(response.content)                #make BeautifulSoup
            prettyHTML=soup.prettify()   #prettify the html
            with open(path, 'w') as f:
                f.write(prettyHTML)
            webbrowser.open(url)            

            raise AttributeError("REST server returned an error number " + 
                                 str(response.status_code) +
                                 "\Response content: " + str(response.content) +
                                 "\nRequest sent to the URL: " + self.serverURL + "import_pdf" +
                                 "\nContent of it 'files' argument: " + str(files))




    def checkSimilarity(self, localPDF, paperId):
        files = {"file": (os.path.basename(localPDF), open(localPDF, 'rb'), 'application/octet-stream'),
                 "json": (None, json.dumps({"paperId": paperId}), 'application/json')}
 
        response = requests.post(#"http://httpbin.org/post",
                                 self.serverURL + "check_similarity",
                                 files=files)
        return response.content





from glob import glob
def checkSimilarities(dbPath):
    # FIXME Delayed refactoring. Define only once the REST server URL.
    client = RESTClient("https://bbpteam.epfl.ch/neurocurator/api/v1.0/")

    intra = []
    inter = []
    for f1 in glob(os.path.join(dbPath, "*.pdf")):
        for f2 in glob(os.path.join(dbPath, "*.pdf")):
            try:
                print(f1, f2)
                response = client.checkSimilarity(f1, os.path.basename(f2)[:-4])
                if f1 == f2:
                    intra.append(float(response))
                else:
                    inter.append(float(response))
            except ValueError:
                pass

    return intra, inter




def checkImportPDF(localPDF, paperId):
    # FIXME Delayed refactoring. Define only once the REST server URL.
    client = RESTClient("https://bbpteam.epfl.ch/neurocurator/api/v1.0/")
    response = json.loads(client.importPDF(localPDF, paperId).decode("utf8"))
    #client.removePDF(localPDF)
    return response

if __name__ == "__main__":
    from qtNeurolexTree import TreeData
    
    #checkSimilarities("/mnt/curator_DB/")
    paperId  = "10.3389/fncel.2016.00168"
    localPDF = "test.pdf" 
    response = checkImportPDF(localPDF, paperId)
    print(response)
    if response["status"] == "success":
        with open("test.txt", "w", encoding="utf8") as f:
            f.write(response["textFile"])
    else:
        raise ValueError(response["message"])        
    
