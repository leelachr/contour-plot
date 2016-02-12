# todo/questions
# - fix makeContour fn. (the except line doesn't fix
#   the problem.)
# - is it better coding practice to still make local
#   functions inside one big fn take arguments?
#   or can i just use the arguments to the big fn inside
#   the local fn? does it look cluttered to keep passing
#   arguments?
# - current implementation can't do a color scheme based
#   on contour's value. (due to having one lambda and 
#   using it with a map HOF.)
# - abstract desiredKeys as a setSubtract fn or something.
# - could use preprocessor fn or maybe series.dropna to
#   fix NaN line. (but how to fix it with pandas?)
# - delete working copy file of data after program runs.
# - how can i make a keyword argument, like 
#   csvToDF(fileName, skipRows=3),
#   instead of csvToDF(fileName, 3) ?

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import shutil
import re #from re import sub

# data types: 

class Contour(object): 
    def __init__(self, key=None, value=None, curve = None):
        self.key = key
        self.value = value
        if curve is None: # reason for this if statement: # handy info: http://stackoverflow.com/questions/1495666/how-to-define-a-class-in-python
            self.curve = []
        else:
            self.curve = curve

# a Contour is an instance of the contour class. It contains: 
# - a Key
# - a Curve
# - a Value

# a Curve is a 2xn array.
# interpretation each row is an x,y pair.

# a Key is an Integer.
# interpretation a unique identifier for that contour.

# a Value is a Number. 
# interpretation the z-coordinate of the curve/contour.

# a Topography is a Dictionary, where the key is an
# Integer, and the value is a Contour whose key is 
# that same integer.

# -------------------------------------------------

# .csv -> Topography
# brings the excel data into the program.
# data is ready for use in plotContours and other
# topography processing functions.
def makeTopography(fileName):
    # LOCAL FUNCTIONS
    # .csv -> .csv
    # preprocesses csv. 
    # creates a copy of the original data file with
    # empty lines stripped, i.e. removes lines which
    # contain only \n, \t, " ", or ",".
    # returns filename of the copy.
    def preprocess(fileName):
        name, extension = os.path.splitext(fileName)
        newName = name + "-working copy" + extension
        input = open(fileName, "r")
        output = open(newName, "w")
        for line in input.readlines():
            checkForEmpty = re.sub("\n", "", line)
            checkForEmpty = re.sub(" ", "", checkForEmpty)
            checkForEmpty = re.sub(",", "", checkForEmpty)
            checkForEmpty = re.sub("\t", "", checkForEmpty)
            if checkForEmpty != "":
                output.write(line) 
        input.close()
        output.close()
        return newName
        
    # .csv -> dataframe
    # uses preprocess fn to filter out empty lines.
    # returns pandas dataframe with column labels.
    def csvToDF(fileName, skipHeaderRows):
        newName = preprocess(fileName)
        dataframe = pd.read_csv(newName, sep=',',skiprows=skipHeaderRows, \
                                header=None, names=["key","x","y","value"], 
                                skip_blank_lines=True)
        return dataframe
        
    
    # Dataframe -> List of Integers
    def listKeys(df):
        # find largest key in the dataframe
        sortedByKey = df.sort_values(by="key")
        lastRow = sortedByKey.tail(1)
        maximum = int(lastRow["key"])
        # check integers from 0 to maximum, filtering out those
        # which aren't in the dataframe as keys.
        listOfKeys = list(filter(lambda k: k in df.key, list(range(0,maximum))))
        return listOfKeys        
        
    # Dataframe Integer -> Curve
    # gets x, y pairs with key of int
    # from the data frame.
    def makeContour(df, key):
        try:
            # the line below gets the rows of the input df
            # which have the input key.
            partOfDF = df[df["key"].isin([key])]
            # change curve to a 2xn numpy array, as needed to make a Contour object.
            curve = partOfDF.as_matrix(["x","y"])
            valueColumn = 3
            value = partOfDF.iloc[key,valueColumn]
            return Contour(key,value,curve)
        except:
            print("the key passed into makeContour (2nd argument) is not \
            in the input data")

    # FUNCTION BODY of makeTopography
    df = csvToDF(fileName, 3)
    topography = dict(map(lambda key: (key, makeContour(df, key)), listKeys(df)))
    print(listKeys(df))           
    return topography

x=makeTopography("test data.csv")
# -------------------------------------------------------------
curve1 = np.array([[1, 2, 3, 4, 4, 0], [1, 2, 3, 4, 0, 0]])
curve2 = np.array([[5, 6, 6, 5], [0, 0, 1, 1]])
myContour1 = Contour(1, 10, curve1)
myContour2 = Contour(2, 11, curve2)
myTop = {1 : myContour1, 2 : myContour2}

# ([List-of Key] OR "all") [List-of Key] Topography -> Image
# plots all contours in first list minus contours in second.
# if first argument is "all", adds all contours in the topography
# to the first list. 
def plotContours(plotThese, notThese, topography):
    # LOCAL FUNCTIONS
    # [List-of Key] [List-of Key] -> [List-of Key]
    # removes elements from first list which are in the second list.
    def desiredKeys(plotThese, notThese):
        if plotThese in ["all", "All", "ALL"]:
            result = list(topography.keys())
        elif type(plotThese) == list:
            result = plotThese
        for key in notThese:
            result.remove(key)
        return result

    # Key Topography -> Curve
    # gets the curve of the contour which is associated with the key.
    def curveFromKey(key):#, topography):
        return topography[key].curve
        
    # [List-of Key] Topography -> [List-of 2xn Array]
    # puts curves into whatever data type plot() can use conveniently.
    def makeArrays(keys):#, topography):
        return list(map(lambda key: curveFromKey(key), keys))
        
    # FUNCTION BODY of plotContours
    allCurves = makeArrays(desiredKeys(plotThese, notThese))
    drawOneCurve = lambda curve: plt.plot(curve[0,:], curve[1,:], "b--")   
    list(map(drawOneCurve, allCurves))  
    plt.show()

plotContours([1,2], [], myTop)


# Topography -> Topography (i/o [List-of Key])
# checks if contours in a topography have big jumps / intersect
# etc. removes segments from those contours.
# prints which contours were altered. 

# ? -> ?
# some fn that smooths the curves.
