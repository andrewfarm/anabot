import re
import json

def sortedIndex(list, elem, startIndex=None, endIndex=None):
        if startIndex is None:
                startIndex = 0
        if endIndex is None:
                endIndex = len(list) - 1
        if endIndex < startIndex:
                return -1
        pivotIndex = int((startIndex + endIndex) / 2)
        if elem == list[pivotIndex]:
                return pivotIndex
        elif elem < list[pivotIndex]:
                return sortedIndex(list, elem, startIndex, pivotIndex - 1)
        else:
                return sortedIndex(list, elem, pivotIndex + 1, endIndex)

#def insertIntoSorted(list, elem, startIndex=None, endIndex=None):
#        if startIndex is None:
#                startIndex = 0
#        if endIndex is None:
#                endIndex = len(list) - 1
#        if endIndex < startIndex:
#                list.insert(startIndex, elem)
#        else:
#                pivotIndex = int((startIndex + endIndex) / 2)
#                if elem == list[pivotIndex]:
#                        list.insert(pivotIndex + 1, elem)
#                elif elem < list[pivotIndex]:
#                        insertIntoSorted(list, elem, startIndex, pivotIndex - 1)
#                else:
#                        insertIntoSorted(list, elem, pivotIndex + 1, endIndex)

def uniq(sortedList):
        u = []
        curr = None
        for elem in sortedList:
                if elem != curr:
                        curr = elem
                        u.append(elem)
        return u

def buildMarkov(text):
        print 'Splitting text'
        textAsSymbols = re.split(r'\s+', text.lower())
        print 'Sorting symbols'
        sortedText = sorted(textAsSymbols)
        print 'Building unique symbol list'
        symbols = uniq(sortedText)
        
        print 'Building successive symbol list'
        freqs = []
        for i in xrange(len(symbols)):
                freqs.append({})
        for i in xrange(len(textAsSymbols) - 1):
                symbolIndex = sortedIndex(symbols, textAsSymbols[i])
                nextSymbol = textAsSymbols[i+1]
                if nextSymbol in freqs[symbolIndex]:
                        freqs[symbolIndex][nextSymbol] += 1
                else:
                        freqs[symbolIndex][nextSymbol] = 1
        print 'Done'
        markov = {'symbols': symbols, 'freqs': freqs}
        return markov

inFilename = 'gutenberg-mobydick.txt'
inf = open(inFilename, 'r')
text = inf.read()
inf.close()

outf = open('mark.json', 'w+')
outf.write(json.dumps(buildMarkov(text)))
outf.close()
