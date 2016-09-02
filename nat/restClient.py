# -*- coding: utf-8 -*-
"""
Created on Sun Jun  5 13:08:43 2016

@author: oreilly
"""

import requests   
import json
import os
import io
from zipfile import ZipFile

class RESTClient:

    def __init__(self, serverURL):
        self.serverURL = serverURL

    def getContext(self, paperId, contextLength, annotStart, annotStr):
                
        response = requests.post(self.serverURL + "get_context", 
                                 json=json.dumps({"paperId"      : paperId, 
                                                  "annotStr"     : annotStr,
                                                  "contextLength": contextLength,
                                                  "annotStart"   : annotStart}))

        return json.loads(response.content.decode("utf8"))["context"]        
        

        
    def importPDF(self, localPDF, paperId, pathDB):
        files = {"file": (os.path.basename(localPDF), open(localPDF, 'rb'), 'application/octet-stream'),
         "json": (None, json.dumps({"paperId": paperId}), 'application/json')}
 
        response = requests.post(#"http://httpbin.org/post", 
                                 self.serverURL + "import_pdf", 
                                 files=files, stream=True)

        if response.status_code == 200:
            #if response["status"] == "error":
            #    raise AttributeError(response["message"])
                        
            zipDoc = ZipFile(io.BytesIO(response.content)) 
            zipDoc.extractall(pathDB)
        else:
            raise AttributeError("REST server returned an error number " + str(response.status_code))



    def checkSimilarity(self, localPDF, paperId):
        files = {"file": (os.path.basename(localPDF), open(localPDF, 'rb'), 'application/octet-stream'),
                 "json": (None, json.dumps({"paperId": paperId}), 'application/json')}
 
        response = requests.post(#"http://httpbin.org/post",
                                 self.serverURL + "check_similarity",
                                 files=files)
        return response.content





from glob import glob
def checkSimilarities(dbPath):
    client = RESTClient("http://bbpca063.epfl.ch:5000/neurocurator/api/v1.0/")

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
    client = RESTClient("http://bbpca063.epfl.ch:5000/neurocurator/api/v1.0/")
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
    