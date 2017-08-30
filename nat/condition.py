# -*- coding: utf-8 -*-
"""
Created on Tue Aug 15 15:27:37 2017

@author: oreilly
"""

from .modelingParameter import getParameterTypeNameFromID
from .variable import NumericalVariable, Variable
from .equivalenceFinder import parameterEquivalenceRules

def checkAnnotation(annotation, key, value):

    if key == "Annotation type":
        return annotation.type == value  
        
    elif key == "Publication ID":        
        return annotation.pubId == value    
        
    elif key == "Annotation ID":        
        return annotation.ID == value    
        
    elif key == "Has parameter":        
        return (len(annotation.parameters) > 0) == bool(value)   
        
    elif key == "Tag name":        
        for tag in annotation.tags:
            if tag.name == value:
                return True
        return False        
        
    elif key == "Author":        
        for author in annotation.authors:
            if author == value:
                return True
        return False        
        
    else:
        raise ValueError("Parameter key '" + str(key) + "' is not available for search.")







def checkParameter(parameter, annotation, key, value):

    if key == "Parameter name":
        return getParameterTypeNameFromID(parameter.description.depVar.typeId) == value  
        
    elif key == "Parameter instance ID":        
        return parameter.id == value
        
    elif key == "Result type":        
        return parameter.description.type == value        
        
    elif key == "Unit":
        if isinstance(parameter.description.depVar, Variable):
            return parameter.description.depVar.unit == value
        elif isinstance(parameter.description.depVar, NumericalVariable):
            return parameter.description.depVar.values.textUnit() == value
        else:
            raise TypeError
            
    elif key == "Required tag name":
        for tag in parameter.requiredTags:
            if tag.name == value:
                return True
        return False
        
    elif key == "Annotation ID":
        return annotation.annotId == value        

        
    elif key == "Publication ID":
        return annotation.pubId == value      
        
    elif key == "Tag name":
        for tag in annotation.tags:
            if tag.name == value:
                return True
        return False
        
    elif key == "Keyword":        
        raise NotImplemented
    else:
        raise ValueError("Parameter key '" + str(key) + "' is not available for search.")





class Condition:

    def apply_param(self, parameters):
        return parameters
        

    def apply_annot(self, annotations):
        return annotations
                
    def addEquivalences(self, key, valueFrom, valueTo, rule):
        pass

    @staticmethod
    def fromJSON(jsonParams):
        return globals()[jsonParams["type"]].fromJSON(jsonParams)



class ConditionAtom(Condition):
    def __init__(self, key, value):
        if not isinstance(key, str):
            raise TypeError
        if not isinstance(value, str):
            raise TypeError

        # A search key            
        self.key          = key
        
        # The values that the items corresponding the the specified search key
        # should be equal to.
        self.value        = value
        
        # List of equivalences that should be applied to the specified pair
        # of (key, value)
        self.equivalences = []
        
    def __str__(self):

        values = [self.value]

        # Add the results matching the conditions after the application of the 
        # equivalence rules.
        values.extend([valueFrom for valueFrom, valueTo, rule in self.equivalences])

        if len(values) == 1:
            return "'" + self.key + "'=='" + self.value + "'"
        else:
            return "'" + self.key + "' in " + str(values)



    def addEquivalences(self, key, valueFrom, valueTo, rule):

        if self.key == key and self.value == valueTo:
            # The equivalence applies
            self.equivalences.append((valueFrom, valueTo, rule))            


    def apply_param(self, parameters):

        # Get the results matching the condition               
        results =  {param:annot for param, annot in parameters.items() 
                            if checkParameter(param, annot, self.key, self.value)}  
                            
        # Add the results matching the conditions after the application of the 
        # equivalence rules.
        for valueFrom, valueTo, rule in self.equivalences:
            additionnalResults = {param.applyTransform(self.key, valueFrom, valueTo, rule):annot 
                                    for param, annot in parameters.items() 
                                    if checkParameter(param, annot, self.key, valueFrom)}
            
            results.update(additionnalResults)
        return results
                                
        
    def apply_annot(self, annotations):
        return [annot for annot in annotations 
                            if checkAnnotation(annot, self.key, self.value)]

    @staticmethod
    def fromJSON(jsonParams):
        if jsonParams["type"] != "ConditionAtom":
            raise TypeError("Invalid object type.")
        obj = ConditionAtom(jsonParams["key"], jsonParams["value"])
        for equivalence in jsonParams["equivalences"]:
            rule = parameterEquivalenceRules[equivalence["valueFrom"]][equivalence["valueTo"]]
            obj.addEquivalences(jsonParams["key"], 
                                equivalence["valueFrom"], 
                                equivalence["valueTo"], 
                                rule)
        return obj


    def toJSON(self):
        def jsonEquivalence(equiv):
            # We don't put in the JSON the rule because to import it, it would
            # requires running eval() on JSON string containing code, which
            # cause security issues.
            return {"valueFrom":equiv[0], "valueTo":equiv[1]}
        
        json = {"type"        : "ConditionAtom",
                "key"         : self.key,
                "value"       : self.value,
                "equivalences": [jsonEquivalence(equiv) for equiv in self.equivalences]}

        return json






class ConditionAND(Condition):

    def __init__(self, conditions):
        if not isinstance(conditions, list):
            raise TypeError
        for condition in conditions:
            if not isinstance(condition, Condition):
                raise TypeError
        self.conditions = conditions


    def addEquivalences(self, key, valueFrom, valueTo, rule):
        for condition in self.conditions:
            condition.addEquivalences(key, valueFrom, valueTo, rule)


    def apply_param(self, parameters):
        for condition in self.conditions:
            parameters = condition.apply_param(parameters)
        return parameters      
        
        
    def __str__(self):
        return "(" + " AND ".join([str(condition) for condition in self.conditions]) + ")"


    def apply_annot(self, annotations):
        for condition in self.conditions:
            annotations = condition.apply_annot(annotations)
        return annotations      
        
        
    @staticmethod
    def fromJSON(jsonParams):
        if jsonParams["type"] != "ConditionAND":
            raise TypeError("Invalid object type.")
        return ConditionAND([Condition.fromJSON(cond) for cond in jsonParams["conditions"]])


    def toJSON(self):
        json = {"type"        : "ConditionAND",
                "conditions"  : [cond.toJSON() for cond in self.conditions]}
        return json






            
    
class ConditionOR(Condition):
    
    def __init__(self, conditions):
        if not isinstance(conditions, list):
            raise TypeError
        for condition in conditions:
            if not isinstance(condition, Condition):
                raise TypeError
        self.conditions = conditions

        
    def __str__(self):
        return "(" + " OR ".join([str(condition) for condition in self.conditions]) + ")"


    def addEquivalences(self, key, valueFrom, valueTo, rule):
        for condition in self.conditions:
            condition.addEquivalences(key, valueFrom, valueTo, rule)


    def apply_param(self, parameters):
        paramOut = {}
        for condition in self.conditions:
            parameters = condition.apply_param(parameters)
            paramOut.update(parameters)
        return paramOut              
        
        
    def apply_annot(self, annotations):
        annotOut = []
        for condition in self.conditions:
            annotations = condition.apply_annot(annotations)
            for annot in annotations:
                if not annot in annotOut:
                    annotOut.append(annot)
        return annotOut       
                
        
    @staticmethod
    def fromJSON(jsonParams):
        if jsonParams["type"] != "ConditionOR":
            raise TypeError("Invalid object type.")
        return ConditionOR([Condition.fromJSON(cond) for cond in jsonParams["conditions"]])


    def toJSON(self):
        json = {"type"        : "ConditionOR",
                "conditions"  : [cond.toJSON() for cond in self.conditions]}
        return json

        
        
class ConditionNOT(Condition):

    def __init__(self, condition):
        if not isinstance(condition, Condition):
            raise TypeError
        self.condition = condition

        
    def __str__(self):
        return "NOT (" + str(self.condition) + ")"


    def addEquivalences(self, key, valueFrom, valueTo, rule):
        self.condition.addEquivalences(key, valueFrom, valueTo, rule)


    def apply_param(self, parameters):
        paramToRemove = self.condition.apply_param(parameters)
        for key in paramToRemove:
            del parameters[key]
        return parameters        
        
        
    def apply_annot(self, annotations):
        annotToRemove = self.condition.apply_annot(annotations)
        for annot in annotToRemove:
            annotations.remove(annot)
        return annotations      

        
    @staticmethod
    def fromJSON(jsonParams):
        if jsonParams["type"] != "ConditionNOT":
            raise TypeError("Invalid object type.")
        return ConditionNOT(Condition.fromJSON(jsonParams["condition"]))


    def toJSON(self):
        json = {"type"        : "ConditionNOT",
                "conditions"  : self.conditions.toJSON()}
        return json

        
        
                