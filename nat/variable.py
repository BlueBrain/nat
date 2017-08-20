# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 16:28:27 2017

@author: oreilly
"""

from .values import Values, statisticList

class NumericalVariable:

    def __init__(self, typeId, values):
        if not isinstance(typeId, str):
            raise TypeError
        if not isinstance(values, Values):
            raise TypeError


        self.typeId = typeId
        self.values = values

    @staticmethod
    def fromJSON(jsonString):
        return NumericalVariable(jsonString["typeId"], Values.fromJSON(jsonString["values"]))

    def toJSON(self):
        return {"typeId": self.typeId, "values": self.values.toJSON()}

    def __str__(self):
        return str(self.toJSON())

    def __repr__(self):
        return str(self.toJSON())

    def transformTypeId(self, valueFrom, valueTo, rule):
        if self.typeId != valueFrom:
            raise ValueError("Cannot transform this value since it is not of the right type.")
        
        self.typeId = valueTo
        self.values.applyTransform(rule)
 

    def centralTendancy(self, type, returnStat=False):
        return self.values.centralTendancy(type=type, returnStat=returnStat)      
        
    def size(self, type, returnStat=False):
        return self.values.size(type=type, returnStat=returnStat) 
        
    def deviation(self, type, returnStat=False):
        return self.values.deviation(type=type, returnStat=returnStat)       

     

class Variable:

    def __init__(self, typeId, unit, statistic):
        self.typeId    = typeId
        self.unit      = unit
        self.statistic = statistic

    @staticmethod
    def fromJSON(jsonString):
        if not jsonString["statistic"] in statisticList:
            raise ValueError("Invalid statistic (" + jsonString["statistic"] + "). Statistics should take one of the following values: ", str(statisticList))

        return Variable(jsonString["typeId"], jsonString["unit"], jsonString["statistic"])

    def toJSON(self):
        return {"typeId": self.typeId, "unit": self.unit, "statistic":self.statistic}

    def __str__(self):
        return str(self.toJSON())

    def __repr__(self):
        return str(self.toJSON())


    def transformTypeId(self, valueFrom, valueTo, rule):
        raise NotImplementedError("Transforms have not been implemented for analytical variables.")

    def centralTendancy(self, type, returnStat=False):
        return None
        
    def size(self, type, returnStat=False):
        return None
        
    def deviation(self, type, returnStat=False):
        return None
        