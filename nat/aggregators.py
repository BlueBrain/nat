from nat.modelingParameter import getParameterTypeIDFromName, getParameterTypeNameFromID

class SampleAggregator:
    
    def __init__(self, paramId=None, paramName=None, grouping=None, method="mean"):
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
        self.grouping           = grouping
        self.method             = method
        self.usedParamInstances = []
    
    def __str__(self):
        return "SampleAggregator(paramName=" + self.paramName + \
               ", grouping=" + str(self.grouping) + \
               ", method=" + str(self.method) + ")"

    def values(self, sample):
        
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
       
        self.usedParamInstances = [param.id for param in sample.sampleDF.loc[indices, "obj_parameter"]]

        data = sample.sampleDF.iloc[indices]
        values = data["Values"].astype(float).values
        data.loc[:, "Values"] = values
        fields = ["Values"]
        fields.extend(self.grouping)
        values = data[fields].groupby(self.grouping).aggregate(self.method)
        return {index:row.values[0] for index, row in values.iterrows()}

        
