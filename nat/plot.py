# -*- coding: utf-8 -*-
"""
Created on Wed Aug 16 09:29:00 2017

@author: oreilly
"""

import matplotlib.pyplot as plt
import collections
import numpy as np


def plotTraces(sample, x, panels=None, labels=None, nbCols=2):
    
    # Get all the records as numerical traces so that they can all be plotted
    # using the same logic. 
    sample.reformatAsNumericalTraces(x)

    paramTraces = sample.sampleDF["obj_parameter"].values
    panels      = sample.sampleDF[panels].values
    
    if not labels is None:
        labels = sample.sampleDF[labels].values
    else:
        labels = ["" for i in len(paramTraces)]

    colors = {label:"C" + str(no) for no, label in enumerate(np.unique(labels))}

    def getFigTrace(param, title="", xlim=None, context=None, index=0, label=""):
        if context is None:
            fig, axes = plt.subplots()
        else:
            fig, axarr = context
            if isinstance(axarr, collections.Iterable):
                axes = axarr[int(index/nbCols), np.mod(index, nbCols)]
            else:
                axes = axarr

        if label == "":
            axes.plot(param.indepCentralTendancies(paramName=x), 
                      param.centralTendancy(), '-o')
        else:
            axes.plot(param.indepCentralTendancies(paramName=x), 
                      param.centralTendancy(), '-o', color=colors[label], label=label)        

        if not xlim is None:
            axes.set_xlim(xlim)
        else:
            axes.set_xlim([min(param.indepCentralTendancies(paramName=x)) - 2.5, 
                           max(param.indepCentralTendancies(paramName=x)) + 2.5])

        axes.set_ylabel(param.name + " (" + param.unit + ")")
        axes.set_xlabel(x          + " (" + param.indepUnits[param.indepNames == x] + ")")
        axes.set_title(title)
        axes.legend()
        return fig, axes    


    minX = {}
    maxX = {}

    uniquePanels = np.unique(panels).tolist()
    context = plt.subplots(int(np.ceil(len(uniquePanels)/nbCols)), nbCols, 
                           figsize=(20, 6*int(np.ceil(len(paramTraces)/nbCols))))
    
    for paramTrace, panel, ref in zip(paramTraces, panels, labels):
        no = uniquePanels.index(panel)

        if panel in minX:
            minX[panel] = min(minX[panel], min(paramTrace.indepCentralTendancies(paramName=x)))
            maxX[panel] = max(maxX[panel], max(paramTrace.indepCentralTendancies(paramName=x)))        
        else:
            minX[panel] = min(paramTrace.indepCentralTendancies(paramName=x))
            maxX[panel] = max(paramTrace.indepCentralTendancies(paramName=x))

        minX[panel] -= (maxX[panel] - minX[panel])*0.03
        maxX[panel] += (maxX[panel] - minX[panel])*0.03 

        getFigTrace(paramTrace, xlim=[minX[panel], maxX[panel]], 
                          title=panel, context=context, index=no, label=ref)
                          
    return context