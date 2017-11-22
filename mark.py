import re
import json

def buildMarkov(text):
        print 'Splitting text'
        textAsSymbols = re.split(r'\s+', text)
        print 'Building unique symbol dictionary'
        chain = {}
        for s in textAsSymbols:
                if not s in chain:
                        chain[s] = {}
        
        print 'Building successive symbol dictionaries'
        for i in xrange(len(textAsSymbols) - 1):
                symbol = textAsSymbols[i]
                nextSymbol = textAsSymbols[i+1]
                if nextSymbol in chain[symbol]:
                        chain[symbol][nextSymbol] += 1
                else:
                        chain[symbol][nextSymbol] = 1
        print 'Done'
        return chain

inFilename = 'gutenberg-mobydick.txt'
inf = open(inFilename, 'r')
text = inf.read()
inf.close()

outf = open('mark.json', 'w+')
outf.write(json.dumps(buildMarkov(text)))
outf.close()
