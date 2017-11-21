import re
import json

def uniq(s):
        u = []
        for elem in s:
                if not elem in u:
                        u.append(elem)
        return u

def buildMarkov(text):
        print 'Splitting text'
        textAsSymbols = re.split(r'\s+', text)
        print 'Building unique symbol list'
        symbols = uniq(textAsSymbols)
        print 'Building successive symbol list'
        print 'This may take a while...'
        strings = []
        for i in xrange(len(symbols)):
                strings.append([])
        for i in xrange(len(textAsSymbols) - 1):
                symbolIndex = symbols.index(textAsSymbols[i])
                strings[symbolIndex].append(textAsSymbols[i+1])
        print 'Done'
        return strings

inFilename = 'gutenberg-mobydick.txt'
inf = open(inFilename, 'r')
text = inf.read()
inf.close()

outf = open('mark.json', 'w+')
outf.write(json.dumps(buildMarkov(text)))
outf.close()
