# -*- coding: utf-8 -*-
"""
Created on Tue Aug 15 15:33:25 2017

@author: oreilly
"""

from .modelingParameter import getParameterTypeNameFromID

# Equivalence rules. These are define such that
# parameterEquivalenceRules[idFrom][idTo] is giving a rule to convert
# values from an entity idFrom to an entity idTo. This rule is specified as 
# a lambda function that that has to be applies to the values of the 
# given parameters.
parameterEquivalenceRules = {}

#"BBP-131005":volume_brain_region
#"BBP-131006":volume_unilateral_brain_region
parameterEquivalenceRules["BBP-131005"] = {"BBP-131006":lambda x: x/2}
parameterEquivalenceRules["BBP-131006"] = {"BBP-131005":lambda x: x*2}



class EquivalenceFinder:
    
    def __init__(self, condition):
        self.condition = condition


    def run(self):
        # Apply rules for parameter equivalences
        return self.applyParameterEquivalence(self.condition)
        
    
    def applyParameterEquivalence(self, condition):
        
        for idFrom in parameterEquivalenceRules:
            for idTo in parameterEquivalenceRules[idFrom]:
                condition.addEquivalences("Parameter type ID", idFrom, idTo, parameterEquivalenceRules[idFrom][idTo])
                condition.addEquivalences("Parameter name", 
                                          getParameterTypeNameFromID(idFrom), 
                                          getParameterTypeNameFromID(idTo), 
                                          parameterEquivalenceRules[idFrom][idTo])
        
        return condition