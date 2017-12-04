import re
import json
import sys
from os import listdir
from os.path import isfile, join

def hasalpha(text):
        for l in text:
                if l.isalpha():
                        return True
        return False

def buildMarkov(text, chain={}):
        print '> Splitting text'
        textAsSymbols = [symbol for symbol in re.split(r'\s+', text) if hasalpha(symbol)]
        print '> Building unique symbol dictionary'
        for s in textAsSymbols:
                if not s in chain:
                        chain[s] = {}
        
        print '> Building successive symbol dictionaries'
        for i in xrange(len(textAsSymbols) - 1):
                symbol = textAsSymbols[i]
                nextSymbol = textAsSymbols[i+1]
                if nextSymbol in chain[symbol]:
                        chain[symbol][nextSymbol] += 1
                else:
                        chain[symbol][nextSymbol] = 1
        print '> Done'
        return chain

def mark(filenames):
        chain = {}
        for filename in filenames:
                print 'Parsing ' + filename
                inf = open(filename, 'r')
                text = inf.read()
                inf.close()
                buildMarkov(text, chain);
        outf = open('mark.json', 'w+')
        outf.write(json.dumps(chain))
        outf.close()

if len(sys.argv) > 1:
        dir = sys.argv[1]
else:
        dir = 'text'
filenames = [join(dir, f) for f in listdir(dir) if isfile(join(dir, f))]
mark(filenames)
