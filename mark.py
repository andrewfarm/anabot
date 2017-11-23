import re
import json
import sys

def hasalpha(text):
        for l in text:
                if l.isalpha():
                        return True
        return False

def buildMarkov(text, chain={}):
        print 'Splitting text'
        textAsSymbols = [symbol for symbol in re.split(r'\s+', text) if hasalpha(symbol)]
        print 'Building unique symbol dictionary'
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

if len(sys.argv) < 2:
        print 'Usage: mark.py <filename>'
        sys.exit(1)
inf = open(sys.argv[1], 'r')
text = inf.read()
inf.close()

try:
        chainf = open('mark.json', 'r')
        chain = json.loads(chainf.read())
        chainf.close()
except:
        chain = {}

outf = open('mark.json', 'w+')
outf.write(json.dumps(buildMarkov(text, chain)))
outf.close()
