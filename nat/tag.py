#!/usr/bin/python3

__author__ = 'oreilly'
__email__  = 'christian.oreilly@epfl.ch'

from .tagUtilities import nlx2ks
#from .ontoManager import OntoManager
#from .ontoServ import getCuriesFromLabel

class Tag:
    
    ## TODO: remove this line once tag ids have been corrected in all annotatiuons
    #ontoMng  = OntoManager()
    #treeData = ontoMng.trees 
    #dicData  = ontoMng.dics    
    #
    #invDicData = {val:(nlx2ks[key] if key in nlx2ks else key) for key, val in dicData.items()}
    #invDicData['Thalamus geniculate nucleus (lateral) principal neuron'] = 'NIFCELL:nlx_cell_20081203'
    #invDicData["Young rat"] = "nlx_organ_109041"
    #invDicData["Thalamus geniculate nucleus (lateral) interneuron"] = "NIFCELL:nifext_46"
    #invDicData["Temperature"] = "PATO:0000146"
    #invDicData["Sleep"] = "GO:0030431"
    #invDicData['Burst firing pattern'] = "nlx_78803"
    #invDicData['Cat'] = 'NIFORG:birnlex_113'
    #invDicData['Thalamus reticular nucleus cell'] = 'NIFCELL:nifext_45'
    #invDicData['Afferent'] = "NIFGA:nlx_anat_1010"
    #invDicData['Morphology'] = 'PATO:0000051'
    ##    
    
    def __init__(self, id, name):
        if not isinstance(id, str):
            raise TypeError("The 'id' parameter need to be of type 'str'. Type passed: " + str(type(id)))
        if not isinstance(name, str):
            raise TypeError("The 'name' parameter need to be of type 'str'. Type passed: " + str(type(name)))

        id = nlx2ks[id] if id in nlx2ks else id
        
        ## TODO: remove this line once tag ids have been corrected in all annotatiuons   
        #if not Tag.dicData[id] == name:
        #    try:
        #        if not name in Tag.invDicData:
        #            curies = getCuriesFromLabel(name)
        #            Tag.invDicData[name] = curies[0]
        #            
        #        print("Incompatibility between in " + str(id) + ":" + str(name) + ". Correcting to " + 
        #              str(Tag.invDicData[name]) + ":" + str(Tag.dicData[Tag.invDicData[name]]))
        #        id = Tag.invDicData[name]
        #        name = Tag.dicData[id]
        #    except:
        #        raise                 
        ######
            
        self.id = id
        self.name = name


    def __repr__(self):
        return str(self.toJSON())

    def __str__(self):
        return str(self.toJSON())

    def toJSON(self):
        return {"id":self.id, "name":self.name}

    @staticmethod
    def fromJSON(jsonString):
        return Tag(jsonString["id"], jsonString["name"])


class RequiredTag(Tag):
    def __init__(self, id, name, rootId):

        super(RequiredTag, self).__init__(id, name)

        if not isinstance(rootId, str):
            raise TypeError

        self.rootId, self.modifier = RequiredTag.processTagRoot(rootId)
        self.optional = "OPTIONAL" in self.modifier
        self.noLoad   = "NOLOAD" in self.modifier


    @staticmethod
    def processTagRoot(rootId):
        if "||" in rootId:
            modifier, rootId = rootId.split("||")
        else:
            modifier = ""        
        return rootId, modifier


    def __repr__(self):
        return str(self.toJSON())

    def __str__(self):
        return str(self.toJSON())

    def toJSON(self):
        if self.modifier == "":
            rootId = self.rootId
        else:
            rootId = self.modifier + "||" + self.rootId
        return {"id":self.id, "name":self.name, "rootId":rootId}

    @staticmethod
    def fromJSON(jsonString):
        return RequiredTag(jsonString["id"], jsonString["name"], jsonString["rootId"])



