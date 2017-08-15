# -*- coding: utf-8 -*-
"""
Created on Mon Aug 14 12:28:29 2017

@author: oreilly
"""

from quantities import Quantity
#from ontoManager import OntoManager
from .treeData import getChildren


    
class AgeResolver:
    
    ageEquivalence = {}
    
    ##### Rat
    # Rats become sexually mature at age 6 weeks, but reach social maturity several months later at about 5 to 6 months of age (Adams and Boice 1983). In adulthood, each rat month is roughly equivalent to 2.5 human years (Ruth 1935).
    # Domestic rats live about 2 to 3.5 years (Pass and Freeth 1993).    
    ageEquivalence["NIFORG:birnlex_160"] = {
        #Adult
        "NIFORG:birnlex_681": [Quantity(5, "month"), Quantity(3.5, "years")],
    }
        
    #ontoMng = OntoManager(recomputer=True)

    
    @staticmethod
    def resolve_fromIDs(speciesId, ageCategoryId, unit=None, typeValue=""):
        
        def resolve_age(ageCatDict, ageCategoryId):  
            for ageCategoryId2 in ageCatDict:
                #ontoMng.
                if ageCategoryId2 == ageCategoryId:
                    return ageCatDict[ageCategoryId]
                    
            return None

        def resolve_species_age(speciesId, ageCategoryId):
            for speciesId2 in AgeResolver.ageEquivalence:
                #ontoMng.
                if speciesId2 == speciesId:
                    return resolve_age(AgeResolver.ageEquivalence[speciesId2], ageCategoryId)
                    
                if speciesId in getChildren(speciesId2):
                    return resolve_age(AgeResolver.ageEquivalence[speciesId2], ageCategoryId)
    
            return None    

        age = resolve_species_age(speciesId, ageCategoryId)
        if age is None:
            return None
        
        if typeValue == "min":
            age = age[0]
        elif typeValue == "max":
            age = age[1]
        elif typeValue == "median":
            age = (age[1]+age[0])/2.0
    
        if not unit is None:
            if isinstance(age, list):
                return [a.rescale(unit) for a in age]
            else:
                return age.rescale(unit)
        return age


    #def resolve_fromLabels(species, ageCategory)    

    
