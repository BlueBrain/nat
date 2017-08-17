# -*- coding: utf-8 -*-
"""
Created on Thu Aug 17 16:27:25 2017

@author: oreilly
"""

import quantities as pq
from abc import abstractmethod
from copy import deepcopy
import numpy as np


statisticList  = ["raw", "mean", "median", "mode", "sem", "sd",  "var",
                  "CI_01", "CI_02.5", "CI_5", "CI_10", "CI_90", "CI_95",
                  "CI_97.5", "CI_99", "N", "min", "max", "other",
                  "deviation", "average"]


def unitIsValid(unit):
    try:
        pq.Quantity(1, unit)
    except:
        return False
    return True



class Values:

    @staticmethod
    def fromJSON(jsonString):
        if jsonString["type"] == "simple":
            return ValuesSimple.fromJSON(jsonString)
        elif jsonString["type"] == "compounded" or jsonString["type"] == "compound":
            return ValuesCompound.fromJSON(jsonString)
        else:
            raise ValueError

    @abstractmethod
    def toJSON(self):
        raise NotImplementedError


    @abstractmethod
    def __matOperator__(self, other, operatorFct):
        raise NotImplementedError

    @abstractmethod
    def rescale(unit):
        raise NotImplementedError


    def __mul__(self, other):
        return self.__matOperator__(other, "__mul__")

    def __truediv__(self, other):
        return self.__matOperator__(other, "__truediv__")

    def __add__(self, other):
        return self.__matOperator__(other, "__add__")

    def __sub__(self, other):
        return self.__matOperator__(other, "__sub__")





class ValuesSimple(Values):

    def __init__(self, values = None, unit= "dimensionless", statistic = "raw"):
        if not isinstance(unit, str):
            raise TypeError
        if not unitIsValid(unit):
            raise ValueError
        if not statistic in statisticList:
            raise ValueError("Invalid statistic '" + statistic +
                             "'. Statistics should take one of the following values: ",
                             str(statisticList))

        self.__values  = []

        if not values is None:
            self.values    = values
            
        self.unit      = unit
        self.statistic = statistic


    def applyTransform(self, rule):
        self.__values = [rule(value) for value in self.__values]


    @property
    def values(self):
        return self.__values
       
    @values.setter
    def values(self, values):
        if not isinstance(values, (list, np.ndarray)):
            raise TypeError("Expected type for values is list, received type: " + str(type(values)))              
        self.__values = [float(val) for val in values]
        
        

    @staticmethod
    def fromJSON(jsonString):
        return ValuesSimple(jsonString["values"], jsonString["unit"], jsonString["statistic"])

    def toJSON(self):
        return {"type": "simple", "values": self.values, "unit": self.unit, "statistic":self.statistic}

    def __str__(self):
        return str(self.toJSON())

    def __repr__(self):
        return str(self.toJSON())

    def text(self, withUnit=False):
        if len(self.values) == 1:
            valueTxt = str(self.values[0])
        else:
            valueTxt = str(self.values)

        if withUnit:
            return valueTxt + " " + self.textUnit()
        else:
            return valueTxt



    def textUnit(self):
        return self.unit



    def centralTendancy(self):
        if len(self.values) == 1:
            return self.values[0]
        else:
            return np.mean(self.values)
            
            
            


    def rescale(self, unit):
        retVal = deepcopy(self)
        if isinstance(unit, str):
            if self.unit != unit:
                quant = pq.Quantity(self.values, self.unit).rescale(unit)
                retVal.values = np.array(quant).tolist() #quant.base
                retVal.unit   = str(quant.dimensionality)
        return retVal


    def __matOperator__(self, other, operatorFct):

        if isinstance(other, (int, float)):
            values = np.array(self.values)
        elif isinstance(other, (pq.Quantity, ParameterInstance)):
            values = pq.Quantity(self.values, self.unit)
        else:
            raise TypeError

        functionList = {'__mul__': values.__mul__,
                        '__truediv__': values.__truediv__,
                        '__add__': values.__add__,
                        '__sub__': values.__sub__}

        retVal = deepcopy(self)
        if isinstance(other, (int, float)):
            retVal.values = functionList[operatorFct](other)
        elif isinstance(other, (pq.Quantity)):
            quant = functionList[operatorFct](other)
            retVal.values = quant.base
            retVal.unit   = str(quant.dimensionality)

        return retVal




class ValuesCompound(Values):

    def __init__(self, valueLst):
        if not isinstance(valueLst, list):
                raise TypeError
        for value in valueLst:
            if not isinstance(value, ValuesSimple):
                raise TypeError

        self.valueLst    = valueLst


    def applyTransform(self, rule):
        for value in self.valueLst:
            value.applyTransform(rule)



    @staticmethod
    def fromJSON(jsonString):
        return ValuesCompound([Values.fromJSON(v) for v in jsonString["valueLst"]])

    def toJSON(self):
        return {"type": "compound", "valueLst": [v.toJSON() for v in self.valueLst]}

    def __str__(self):
        return str(self.toJSON())

    def __repr__(self):
        return str(self.toJSON())



    def __matOperator__(self, other, operatorFct):

        retVal = deepcopy(self)
        for ind, value in enumerate(retVal.valueLst):
            if value.statistic != "N":
                retVal.valueLst[ind] = value.__matOperator__(other, operatorFct)
        return retVal


    def rescale(self, unit):
        retVal = deepcopy(self)
        for ind, value in enumerate(retVal.valueLst):
            if value.statistic != "N":
                retVal.valueLst[ind] = value.rescale(unit)
        return retVal


    def text(self, withUnit=False):

        stats = [value.statistic for value in self.valueLst]
        if "raw" in stats :
            return self.valueLst[stats.index("raw")].text(withUnit)

        if "sem" in stats :
            dev = "+/- " + self.valueLst[stats.index("sem")].text()
        elif "sd" in stats :
            dev = "+/- " + self.valueLst[stats.index("sd")].text()
        elif "var" in stats :
            dev = "+/- " + self.valueLst[stats.index("var")].text()
        elif "deviation" in stats :
            dev = "+/- " + self.valueLst[stats.index("deviation")].text()
        else:
            dev = ""

        if "min" in stats and "max" in stats :
            inter = "[" + self.valueLst[stats.index("min")].text() + " - " + self.valueLst[stats.index("max")].text() + "]"
        elif "CI_01" in stats and  "CI_99" in stats :
            inter = "[" + self.valueLst[stats.index("CI_01")].text() + " - " + self.valueLst[stats.index("CI_99")].text() + "]"
        elif "CI_02.5" in stats and  "CI_97.5" in stats :
            inter = "[" + self.valueLst[stats.index("CI_02.5")].text() + " - " + self.valueLst[stats.index("CI_97.5")].text() + "]"
        else:
            inter = ""

        if "N" in stats:
            sampSize = "(n=" + self.valueLst[stats.index("N")].text() +")"
        else:
            sampSize = ""

        if "mean" in stats :
            avg = self.valueLst[stats.index("mean")].text()
        elif "median" in stats :
            avg = self.valueLst[stats.index("median")].text()
        elif "mode" in stats :
            avg = self.valueLst[stats.index("mode")].text()
        elif "average" in stats :
            avg = self.valueLst[stats.index("average")].text()
        else:
            avg = ""


        if withUnit:
            return " ".join([avg, dev, inter, sampSize, self.textUnit()])
        else:
            return " ".join([avg, dev, inter, sampSize])


    def textUnit(self):

        stats = [value.statistic for value in self.valueLst]
        unit = ""
        if "raw" in stats :
            return self.valueLst[stats.index("raw")].textUnit()

        if "min" in stats and "max" in stats :
            unit = self.valueLst[stats.index("min")].unit
        elif "CI_01" in stats and  "CI_99" in stats :
            unit = self.valueLst[stats.index("CI_01")].unit
        elif "CI_02.5" in stats and  "CI_97.5" in stats :
            unit = self.valueLst[stats.index("CI_02.5")].unit

        if "mean" in stats :
            unit = self.valueLst[stats.index("mean")].unit
        elif "median" in stats :
            unit = self.valueLst[stats.index("median")].unit
        elif "mode" in stats :
            unit = self.valueLst[stats.index("mode")].unit
        elif "average" in stats :
            unit = self.valueLst[stats.index("average")].unit

        return unit


    def centralTendancy(self):

        stats = [value.statistic for value in self.valueLst]
        if "raw" in stats :
            return self.valueLst[stats.index("raw")].centralTendancy()

        for stat in ["mean", "median", "mode"]:
            if stat in stats :
                return self.valueLst[stats.index(stat)].centralTendancy()


        if "min" in stats and "max" in stats :
            return (self.valueLst[stats.index("min")].centralTendancy() +
                    self.valueLst[stats.index("max")].centralTendancy())/2.0
        if "CI_01" in stats and  "CI_99" in stats :
            return (self.valueLst[stats.index("CI_01")].centralTendancy() +
                    self.valueLst[stats.index("CI_99")].centralTendancy())/2.0
        if "CI_02.5" in stats and  "CI_97.5" in stats :
            return (self.valueLst[stats.index("CI_02.5")].centralTendancy() +
                    self.valueLst[stats.index("CI_97.5")].centralTendancy())/2.0

        return np.nan


    @property
    def unit(self):
        return self.textUnit()

