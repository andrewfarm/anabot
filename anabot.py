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
from copy import deepcopy

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

def createAnagram(letters, chain, s1=None, s2=None, recursion=1):
#        print 'createAnagram(<letters>, <chain>, s1=\'%s\', s2=\'%s\', recursion=%d' % (s1, s2, recursion)
        if (s1 is None) or (s2 is None):
                dict = deepcopy(chain)
        else:
                dict = deepcopy(chain[s1][s2])
        while True:
                if (s1 is None) or (s2 is None):
                        nexts1 = random.choice(dict.keys())
                        next = random.choice(dict[nexts1].keys())
                        dict[nexts1].pop(next)
                        if len(dict[nexts1]) == 0:
                                dict.pop(nexts1)
                else:
                        nexts1 = s2
                        next = randNext(dict)
                        dict.pop(next)
                remainingLetters = removeWord(clean(next), letters)
                if remainingLetters is not None: #the word fits in the list letters
                        if len(remainingLetters) == 0: #base case: the word uses the last of the letters
                                return next
                        rest = createAnagram(remainingLetters, chain, s1=nexts1, s2=next, recursion=recursion+1)
                        if rest is not None: #found an anagram!
                                return next + ' ' + rest
                if len(dict) == 0:
                        return None

postLimitShort = 10
postLimitLong = 30
timeout = 60
waitInterval = 0

version = '0.6'

print '===== Starting Anabot v' + version + ' ====='

arFilename = 'already-reblogged.txt'
createARFile = open(arFilename, 'a+')
createARFile.close()
readARFile = open(arFilename, 'r')
alreadyReblogged = [int(line.strip()) for line in readARFile.readlines()]
readARFile.close()

markovChainFilename = 'mark.json'
markovChainFile = open(markovChainFilename, 'r')
markovChainJSON = markovChainFile.read()
markovChainFile.close()
markovChain = json.loads(markovChainJSON)

def reblog(post, reblogComment):
        alreadyReblogged.append(post['id'])
        appendARFile = open(arFilename, 'a+')
        appendARFile.write('%d\n' % post['id'])
        appendARFile.close()
        client.reblog('anagram-robot.tumblr.com', id=post['id'], reblog_key=post['reblog_key'], tags=('anagram',), state='published', comment='<em>' + reblogComment + '</em><br><br><small>- Anagram robot ' + version + '. I find anagrams for stuff. I know I don\'t always make sense, but I\'m getting better!</small>')

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
                        else:
                                if p.exitcode != 0:
                                        print 'anabot: process terminated with exit code %d' % p.exitcode
                                        sys.exit(p.exitcode)
                time.sleep(waitInterval)
        except SSLError:
                print 'Connection error'
