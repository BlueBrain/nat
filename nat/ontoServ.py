# -*- coding: utf-8 -*-
"""
Created on Wed Jul 13 14:25:57 2016

@author: oreilly
"""

import requests
import os
import pickle

bases = {"KS":"http://matrix.neuinfo.org:9000/scigraph",
         "NIP":"https://nip.humanbrainproject.eu/api/scigraph"}


def getOntoCategory(curie, alwaysFetch=False):
    """
     Accessing web-based ontology service is too long, so we cache the 
     information in a pickle file and query the services only if the info
     has not already been cached. 
    """
    
    fileName = os.path.join(os.path.dirname(__file__), "ontoCategories.bin") 
    if not alwaysFetch:
        try:
            with open(fileName, "rb") as catFile:
                ontoCat = pickle.load(catFile)
                
            if curie in ontoCat:
                return ontoCat[curie]                
        except:
            ontoCat = {}
    
    base = bases["KS"] 
    query = base + "/vocabulary/id/" + curie
    response = requests.get(query)
    if not response.ok:
        ontoCat[curie] = []
    else:

        try:
            concepts = response.json()
        except ValueError:
            print(query)
            print(response)
            raise
        
        if len(concepts["categories"]):
            ontoCat[curie] = concepts["categories"]
        else:
            ontoCat[curie] = []


    try:
        with open(fileName, "wb") as catFile:
            pickle.dump(ontoCat, catFile)
    except:
        pass        

    return ontoCat[curie] 




def getLabelFromCurie(curie):

    for service, base in bases.items():
        query = base + "/vocabulary/id/" + curie
        response = requests.get(query)
        if not response.ok:
            continue
        try:
            concepts = response.json()
        except ValueError:
            print(query)
            print(response)
            raise
        if service == "NIP":
            concepts = concepts["concepts"][0]
        if len(concepts["labels"]):
            return concepts["labels"][0]
    return None


def getCuriesFromLabel(label):

    for service, base in bases.items():
        query = base + "/vocabulary/term/" + label
        response = requests.get(query)
        if not response.ok:
            continue
        try:
            concepts = response.json()
        except ValueError:
            print(query)
            print(response)
            raise
        if service == "NIP":
            concepts = concepts["concepts"][0]
        return [concept["curie"] for concept in concepts]
    return None


def autocomplete(term, service="KS", limit=200):

    base = bases[service]
    query = base + "/vocabulary/autocomplete/" + term + "?limit=" + str(limit)
    response = requests.get(query)
    if not response.ok:
        raise ValueError
    try:
        items = response.json()
    except ValueError:
        print(query)
        print(response)
        raise

    return {item["concept"]["curie"]:item["concept"]["labels"][0] for item in items}


