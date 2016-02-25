# todo/questions
# - fix makeContour fn. (the except line doesn't fix
#   the problem.)
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
# - csvToDF: instead of skipHeaderRows as an argument, 
#   there should be a fn to figure out which initial rows
#   aren't columns of data, and trim them. 
# - "tooFar" in splitContour should come from a statistical
#   analysis of the curve.
# - splitContours returns multiple contours with the same
#   key. is this a problem?
# - why is test_curveFromTuples passing???
# - why is test_splitContour failing???

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import shutil
import re #from re import sub
import math
import unittest
import copy # from copy import copy

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

# -------------------------------------------------------------
# utilities and functions for working with the data structures.
# -------------------------------------------------------------
# List-of Tuples -> Curve
def curveFromTuples(tuples):
    xs = []
    ys = []
    [xs.append(tup[0]) for tup in tuples]
    [ys.append(tup[1]) for tup in tuples]
    curve = np.array([xs,ys])
    return curve

# Curve -> List-of Tuples
def tuplesFromCurve(curve):
    lst = []    
    [lst.append(float(entry)) for entry in np.nditer(curve)]
    splitPoint = int(len(lst)/2)
    lstTup = list(zip(lst[:splitPoint], lst[splitPoint:]))
    return lstTup

# Tuple Tuple -> Number
def distance(pt1, pt2):
    return math.sqrt((pt2[0] - pt1[0]) ** 2 + (pt2[1] - pt1[1]) ** 2)

# -------------------------------------------------------------
# Topography -> Topography 
# checks if contours in a topography have big jumps / intersect
# etc. removes segments from those contours.
# prints which contours were altered.
def cutJumps(topography):
    # create a copy of topography to modify.
    newTopography = copy.copy(topography)
    for key in newTopography:
        newTopography[key] = splitContour(newTopography[key])
    return newTopography

# Contour -> List-of Contours
# breaks a contour into a list of contours at a point (if any)
# where a big jump occurs. 
def splitContour(contour):
    print("the problem is ... " , contour, " type is ... " , type(contour))
    curve = contour.curve    
    numPts = curve.shape[1]
    tooFar = 5
    accumulator = []
    lstCurves = []
    # make a list of curves. the for loop
    # breaks off a new curve whenever the tooFar
    # criterion is broken.
    for i in range(0, numPts - 1):
        point = (curve[0,i], curve[1,i])
        nextPoint = (curve[0,i + 1], curve[1,i + 1])
        accumulator.append(point)
        if distance(point, nextPoint) > tooFar:
            accumulator.append(point)            
            lstCurves.append(curveFromTuples(accumulator))
            accumulator = []
    # add the final point and final curve.
    lastPoint = (curve[0, numPts - 1], curve[1, numPts - 1])
    accumulator.append(lastPoint)
    lstCurves.append(curveFromTuples(accumulator))
    # turn lstCurves into a list of contours.
    lstContours = []
    for curve in lstCurves:
        lstContours.append(Contour(contour.key, contour.value, curve))
    # print-outs for testing:
    for c in lstContours:
        print("the key is ... ")
        print(c.key)
        print("the value is ... ")
        print(c.value) 
        print("the curve is ... ")
        print(c.curve)  
    print (lstContours)
    return lstContours

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
    df = csvToDF(fileName, 4)
    topography = dict([(key, makeContour(df, key)) for key in listKeys(df)])
    #topography = cutJumps(dict([(key, makeContour(df, key)) for key in listKeys(df)]))         
    return topography

x=makeTopography("test data.csv")
# -------------------------------------------------------------
curve1 = np.array([[1, 2, 3, 4, 4, 0], [1, 2, 3, 4, 0, 0]])
curve2 = np.array([[5, 6, 7, 5], [0, 0, 1, 1]])
curve3 = np.array([[1.5, 2.5, 3.5, 12, 13, 13.5, 20, 22], \
                    [1.5, 2.75, 3.9, 13, 14, 15,  24, 21]])
myContour1 = Contour(1, 10, curve1)
myContour2 = Contour(2, 11, curve2)
myContour3 = Contour(3, 13, curve3)
myTop = {1 : myContour1, 2 : myContour2, 3 : myContour3}

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
        return [curveFromKey(key) for key in keys]
        
    # FUNCTION BODY of plotContours
    allCurves = makeArrays(desiredKeys(plotThese, notThese))
    drawOneCurve = lambda curve: plt.plot(curve[0,:], curve[1,:], "b--")
    # type check is needed because cutJumps returns lists of Curves.
    # this is a tacked on solution; when I added cutJumps, some keys
    # in a topography now had a list of arrays, rather than an array
    # associated with them.
    checkTypeDrawOneCurve = lambda curve: drawOneCurve(curve) \
                                            if type(curve) == np.ndarray \
                                            else [drawOneCurve for element in curve]
    [checkTypeDrawOneCurve for curve in allCurves]  
    plt.show()

#plotContours([1,2], [], myTop)






# Topography -> List-of Values -> Dictionary (Value-Color pairs)
# color scheme.


# -----------------------------------------------------------
# unit tests
# -----------------------------------------------------------
# note: these unit tests are not at all complete. they don't 
# cover any unusual or boundary cases.
class Tests(unittest.TestCase):
    def setUp(self):
        self.curve1 = np.array([[1, 2, 3, 4, 4, 0], [1, 2, 3, 4, 0, 0]])
        self.curve2 = np.array([[5, 6, 7, 5], [0, 0, 1, 1]])
        self.curve3 = np.array([[1.5, 2.5, 3.5, 12, 13, 13.5, 20, 22], \
                            [1.5, 2.75, 3.9, 13, 14, 15,  24, 21]])
        self.splitCurve3a = np.array([[1.5, 2.5, 3.5], [1.2, 2.75, 3.9]])
        self.splitCurve3b = np.array([[12,13,13.5], [13,14,15]])
        self.splitCurve3c = np.array([[20,22], [24,21]])
        self.myContour1 = Contour(1, 10, curve1)
        self.myContour2 = Contour(2, 11, curve2)
        self.myContour3 = Contour(3, 13, curve3)
        self.myTop = {1 : myContour1, 2 : myContour2}
        self.sampleTuples = [(1, 2), (3, 4), (5, 6)]
        self.sampleCurve = np.array([[1, 3, 5], [2, 4, 6]])
    def test_distance(self):
        self.assertEqual(distance((3,0),(0,4)), 5)
    def test_curveFromTuples(self):
        self.assertEqual(curveFromTuples(self.sampleTuples).any(), \
                        self.sampleCurve.any())
    def test_splitContour(self):
        self.assertEqual(splitContour(myContour3), Contour(3, 13, \
                            [Contour(3, 13, self.splitCurve3a), \
                            Contour(3, 13, self.splitCurve3b), \
                            Contour(3, 13, self.splitCurve3c)]))

unittest.main()

