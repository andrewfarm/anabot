import pytumblr
import random
from pprint import pprint
import keys
import json
import re
from multiprocessing import Process
import time
from requests.exceptions import SSLError
import sys

postLimitShort = 10
postLimitLong = 30
timeout = 60
waitInterval = 20

version = '0.0'

print '===== Starting Anabot v' + version + ' ====='

'''Returns a copy of textLetters with the letters in word each removed once,
   or None if not all the letters in word exist in textLetters'''
def removeWord(word, textLetters):
        textLetters = list(textLetters) #make a copy of the text
        for letter in word:
                if letter in textLetters:
                        textLetters.remove(letter)
                else:
                        return None
        return textLetters

'''Chooses a random state from the states in nextDict based on their frequencies'''
def randNext(nextDict):
        totalFreq = 0
        for next in nextDict:
                totalFreq += nextDict[next]
        rand = int(random.random() * totalFreq)
        cumulativeFreq = 0
        for next in nextDict:
                cumulativeFreq += nextDict[next]
                if cumulativeFreq >= rand:
                        return next

def clean(symbol):
        return ''.join([l for l in symbol.lower() if l.isalpha()])

def createAnagram(letters, chain, curr=None, recursion=1):
#        print 'recursion: %d\t%s' % (recursion, curr)
        if curr is None:
                alreadyTried = {}
                numTried = 0
                chainSize = len(chain)
                remainingLetters = None
                rest = None
                while (True):
                        curr = random.choice(chain.keys())
                        if not curr in alreadyTried:
                                alreadyTried[curr] = True
                                numTried += 1
                                cleanedCurr = clean(curr)
                                remainingLetters = removeWord(cleanedCurr, letters)
                                if remainingLetters is not None:
                                        percentTried = int(100 * numTried / chainSize)
                                        print '%d: %s' % (percentTried, curr)
                                        if len(remainingLetters) == 0:
                                                return curr[0].upper() + curr[1:]
                                        rest = createAnagram(remainingLetters, chain, curr, recursion=recursion+1)
                                        if rest is not None:
                                                return curr[0].upper() + curr[1:] + ' ' + rest
                        if len(alreadyTried) == len(chain):
                                return None
        else:
                freqs = chain[curr].copy()
                while (True):
                        next = randNext(freqs)
                        freqs.pop(next, None) #TODO next sometimes not found in freqs
                        cleanedNext = clean(next)
                        remainingLetters = removeWord(cleanedNext, letters)
                        if remainingLetters is not None:
                                if len(remainingLetters) == 0:
                                        return next
                                rest = createAnagram(remainingLetters, chain, next, recursion=recursion+1)
                                if rest is not None:
                                        return next + ' ' + rest
                        if len(freqs) == 0:
                                return None
                return 'END'

arFilename = 'already-reblogged.txt'
readARFile = open(arFilename, 'r')
alreadyReblogged = [int(line.strip()) for line in readARFile.readlines()]
readARFile.close()

markovChainFilename = 'mark.json'
markovChainFile = open(markovChainFilename, 'r')
markovChainJSON = markovChainFile.read()
markovChainFile.close()
markovChain = json.loads(markovChainJSON)

def reblog(post, reblogComment):
        alreadyReblogged.append(post['id']);
        appendARFile = open(arFilename, 'a+')
        appendARFile.write('%d\n' % post['id'])
        appendARFile.close()
        client.reblog('anagram-robot.tumblr.com', id=post['id'], reblog_key=post['reblog_key'], tags=('anagram',), state='published', comment='<em>' + reblogComment + '</em><br><br><small>- Anagram robot ' + version + '. I find anagrams for stuff. I know I don\'t make much sense, but I\'m working on that!</small>')

'''Returns True if Ana was successful, False if she wasn't'''
def ana(post):
        if post['id'] in alreadyReblogged:
                print 'Already reblogged'
                return False
        if not 'body' in post:
                print 'No body attribute'
                return False
        print post['body']
        postLetters = [c for c in post['body'].lower() if c.isalpha()]
        if (len(postLetters) < postLimitShort) or (len(postLetters) > postLimitLong):
                print 'Too short or long'
                return False
        
        anagram = createAnagram(postLetters, markovChain)
        if anagram is not None:
                reblog(post, anagram)
                print anagram
                return True

        print '404 Anagram not found'
        return False

try:
        client = pytumblr.TumblrRestClient(keys.consumerKey, keys.consumerSecret, keys.token, keys.tokenSecret)
except:
        print '!!! Could not connect to Tumblr. !!!'
while True:
        tag = clean(random.choice(markovChain.keys()))
        print '===== Searching tag: ' + tag + ' ====='
        try:
                for post in client.tagged(tag, filter='text'):
                        p = Process(target=ana, name='Ana', args=(post,))
                        p.start()
                        p.join(timeout)
                        if p.is_alive():
                                print 'Timed out'
                                p.terminate()
                                p.join()
                time.sleep(waitInterval)
        except SSLError:
                print 'Connection error'
