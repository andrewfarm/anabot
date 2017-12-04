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
        print '> Building successive symbol dictionaries'
        for i in xrange(len(textAsSymbols) - 2):
                s1 = textAsSymbols[i]
                s2 = textAsSymbols[i+1]
                next = textAsSymbols[i+2]
                if not s1 in chain:
                        chain[s1] = {}
                if not s2 in chain[s1]:
                        chain[s1][s2] = {}
                if next in chain[s1][s2]:
                        chain[s1][s2][next] += 1
                else:
                        chain[s1][s2][next] = 1
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
