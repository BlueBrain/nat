# -*- coding: utf-8 -*-
"""
Created on Mon Aug 29

@author: oreilly
"""

import numpy as np
from .modelingParameter import getParameterTypeNameFromID


class AggregatedIndex:
    
    def __init__(self, index, value, ids):
        self.index = index
        self.value = value
        self.ids   = ids
        
    def toJSON(self):
        json = {"index":self.index,
                "value":self.value,
                "ids"  :self.ids}        
        return json

        
    @staticmethod
    def fromJSON(jsonParams):
        return AggregatedIndex(jsonParams["index"], jsonParams["value"],  jsonParams["ids"])
        
        

class SampleAggregator:
    
    def __init__(self, paramId=None, paramName=None, groupingFactors=None, 
                 method="mean", categoryGrouping=None):
        if not paramName is None:
            if not paramId is None:
                if getParameterTypeNameFromID(paramId) != paramName:
                    raise ValueError("Parameters paramId and paramName "
                                    + "passed to SampleAggregator.__init__() are incompatible.")
        else:
            if paramId is None:
                raise ValueError("At least one of the attribute paramName and paramId "
                                    + "passed to SampleAggregator.__init__() most not be None.")
            paramName = getParameterTypeNameFromID(paramId)        
        
        self.paramName          = paramName
        if categoryGrouping is None:
            self.groupingFactors = []
        else:
            self.groupingFactors    = groupingFactors
        self.method             = method
        self.categoryGrouping   = categoryGrouping
        #self.usedParamInstances = []
        self.aggreatedLst       = []
    
    def __str__(self):
        return "SampleAggregator(paramName=" + self.paramName + \
               ", groupingFactors=" + str(self.groupingFactors) + \
               ", method=" + str(self.method) + \
               ", categoryGrouping=" + str(self.categoryGrouping) + ")"

    def values(self, sample=None):
        if not sample is None:
            self.aggregate(sample)
            
        return {aggIndex.index:aggIndex.value for aggIndex in self.aggreatedLst}
        
        
        
    def aggregate(self, sample):

        indices = []
        for index, row in sample.sampleDF.iterrows():
            if not row["isValid"]:
                continue
            
            if self.paramName != getParameterTypeNameFromID(row["obj_parameter"].typeId):
                print("Not the right parameter.")
                continue
        
            try:
                float(row["Values"]) 
                indices.append(index)
            except:          
                statusStr = "Cannot be converted to a float value implicitly.\n"
                row["isValid"]   = False
                row["statusStr"] += statusStr                
       
        #self.usedParamInstances = [param.id for param in sample.sampleDF.loc[indices, "obj_parameter"]]

        data = sample.sampleDF.iloc[indices].copy()
        
        for catGroup in self.categoryGrouping:
            for valuesToReplace in catGroup[1:]:
                condition = np.ones(data.shape[0])
                for key, value in zip(self.groupingFactors, valuesToReplace):                  
                    condition *= data[key] == value
                for key, value in zip(self.groupingFactors, catGroup[0]):   
                    data.loc[condition.astype(bool), key] = value
        
        values = data["Values"].astype(float).values
        data.loc[:, "Values"]  = values
        data.loc[:, "paramId"] = [param.id for param in sample.sampleDF.loc[indices, "obj_parameter"]]

        fields = ["Values", "paramId"]
        fields.extend(self.groupingFactors)
        values = data[fields].groupby(self.groupingFactors).aggregate({"Values":self.method, 
                                                                "paramId":lambda ids: tuple([id for id in ids])})
        
        self.aggreatedLst = [AggregatedIndex(index, row["Values"], row["paramId"]) 
                                      for index, row in values.iterrows()]

        
    @staticmethod
    def fromJSON(jsonParams):
        obj = SampleAggregator(paramName=jsonParams["paramName"], 
                               groupingFactors=jsonParams["groupingFactors"], 
                               method=jsonParams["method"],
                               categoryGrouping=jsonParams["categoryGrouping"] )
        obj.aggreatedLst = [AggregatedIndex.fromJSON(aggJSON) for aggJSON in jsonParams["aggreatedLst"]]
        return obj



    def toJSON(self):
        json = {"paramName":self.paramName,
                "groupingFactors": self.groupingFactors,
                "method": self.method,
                "categoryGrouping": self.categoryGrouping,
                "aggreatedLst":[aggIndex.toJSON() for aggIndex in self.aggreatedLst]}

        return json

