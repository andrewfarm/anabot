import pytumblr
import random
from pprint import pprint
import keys
import json
import re
from multiprocessing import Process
import time
from requests.exceptions import ConnectionError
from requests.exceptions import SSLError
import sys
from copy import deepcopy

from stripogram import html2text

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

def createAnagram(letters, chain, s1=None, s2=None, recursion=1, printCurr=False, soFar=None):
#        print 'createAnagram(<letters>, <chain>, s1=\'%s\', s2=\'%s\', recursion=%d' % (s1, s2, recursion)
        try:
                if (s1 is None) or (s2 is None):
                        dict = deepcopy(chain)
                else:
                        dict = deepcopy(chain[s1][s2])
        except KeyError:
                print 'Error with deepCopy (Unexpected KeyError)'
                sys.exit(0) #any other exit code will cause Ana to exit
        while True:
                if (s1 is None) or (s2 is None):
                        nexts1 = random.choice(dict.keys())
                        next = random.choice(dict[nexts1].keys())
                        dict[nexts1].pop(next)
                        if len(dict[nexts1]) == 0:
                                dict.pop(nexts1)
                        if printCurr:
                                nextSoFar = next
                else:
                        nexts1 = s2
                        next = randNext(dict)
                        dict.pop(next)
                        if printCurr:
                                nextSoFar = soFar + ' ' + next
                                sys.stdout.write("\033[K") #clear the console line
                                print nextSoFar
                                sys.stdout.write("\033[K") #clear the console line
                                print 'Current chain length: %d' % (recursion - 1)
                                sys.stdout.write("\033[F") #move cursor to start of last line
                                sys.stdout.write("\033[F") #move cursor to start of last line
                remainingLetters = removeWord(clean(next), letters)
                if remainingLetters is not None: #the word fits in the list letters
                        if len(remainingLetters) == 0: #base case: the word uses the last of the letters
                                return next
                        if printCurr:
                                rest = createAnagram(remainingLetters, chain, s1=nexts1, s2=next, recursion=recursion + 1, printCurr=True, soFar=nextSoFar)
                        else:
                                rest = createAnagram(remainingLetters, chain, s1=nexts1, s2=next, recursion=recursion + 1)
                        if rest is not None: #found an anagram!
                                return next + ' ' + rest
                if len(dict) == 0:
                        return None

postLimitShort = 10
postLimitLong = 30
timeout = 60
waitInterval = 0

version = '0.8'

print '===== Starting Anabot v' + version + ' ====='

arFilename = 'already-reblogged.txt'
createARFile = open(arFilename, 'a+')
createARFile.close()
readARFile = open(arFilename, 'r')
alreadyReblogged = [int(line.strip()) for line in readARFile.readlines()]
readARFile.close()

tagBlacklistFilename = 'tag-blacklist.txt'
tagBlacklistFile = open(tagBlacklistFilename, 'r')
tagBlacklist = [line.strip() for line in tagBlacklistFile.readlines()]
tagBlacklistFile.close()

print 'Reading Markov data'
markovChainFilename = 'mark.json'
markovChainFile = open(markovChainFilename, 'r')
markovChainJSON = markovChainFile.read()
markovChainFile.close()
markovChain = json.loads(markovChainJSON)
print 'Done'

def reblog(post, reblogComment):
        alreadyReblogged.append(post['id'])
        appendARFile = open(arFilename, 'a+')
        appendARFile.write('%d\n' % post['id'])
        appendARFile.close()
        client.reblog('anagram-robot.tumblr.com', id=post['id'], reblog_key=post['reblog_key'], tags=['anagram'], state='queue', comment=reblogComment + '<br><br><small>- Anagram robot ' + version + '. I find anagrams for stuff. I know I don\'t always make sense, but I\'m getting better!</small>')

'''Returns True if Ana was successful, False if they weren't'''
def ana(post, bodyNeedsCleaning=False):
        if type(post) is not dict:
                print 'Unexpected post format'
                return False
        if post['id'] in alreadyReblogged:
                print 'Already reblogged'
                return False
        if not 'body' in post:
                print 'No body attribute'
                return False
        body = post['body']
        if bodyNeedsCleaning:
                body = html2text(body)
        postLetters = [c for c in body.lower() if c.isalpha()]
        if len(postLetters) < postLimitShort:
                print body
                print 'Too short'
                return False
        if len(postLetters) > postLimitLong:
                print body[:postLimitLong-1] + '...'
                print 'Too long'
                return False
        for tag in post['tags']:
                tag = tag.lower()
                for blacklistedTag in tagBlacklist:
                        if tag == blacklistedTag:
                                print 'Post tagged with #' + tag
                                return False
        print body

        anagram = createAnagram(postLetters, markovChain)
        if anagram is not None:
                anagram = anagram[0].upper() + anagram[1:]
                reblog(post, anagram)
                print anagram
                return True

        print '404 Anagram not found'
        return False

if len(sys.argv) > 1:
        if sys.argv[1] == '--text':
                if len(sys.argv) > 2:
                        print 'Creating anagram'
                        anagram = createAnagram([c for c in sys.argv[2] if c.isalpha()], markovChain)
                        if anagram is not None:
                                anagram = anagram[0].upper() + anagram[1:]
                                print 'Anagram found:'
                                print anagram
                        else:
                                print 'No anagrams found.'
                        sys.exit(0)
                else:
                        print 'Usage: anabot.py [--text <text>]'
                        sys.exit(1)
        elif sys.argv[1] == '--post':
                pass
        else:
                print 'Unknown option ' + sys.argv[1]
                sys.exit(1)

try:
        print 'Connecting to Tumblr'
        client = pytumblr.TumblrRestClient(keys.consumerKey, keys.consumerSecret, keys.token, keys.tokenSecret)
        cinfo = client.info()
        if 'errors' in cinfo:
                for error in cinfo['errors']:
                        print 'Error: ' + error['title'] + ': ' + error['detail']
                print '!!! Could not authenticate user. !!!'
                sys.exit(2)
        print 'Authorization successful.'
except ConnectionError:
        print '!!! Could not connect to Tumblr. !!!'
        sys.exit(1)

if len(sys.argv) > 1:
        if sys.argv[1] == '--post':
                if len(sys.argv) > 3:
                        response = client.posts(sys.argv[2] + '.tumblr.com', id=int(sys.argv[3]))
                        if 'errors' in response:
                                for error in response['errors']:
                                        print 'Error: ' + error['title'] + ': ' + error['detail']
                                sys.exit(1)
                        ana(response['posts'][0], bodyNeedsCleaning=True)
                        sys.exit(0)
                else:
                        print 'Usage: anabot.py [--post <blog> <post id>]'
                        sys.exit(1)
        else:
                print 'Unknown option ' + sys.argv[1]
                sys.exit(1)

while True:
        tag = clean(random.choice(markovChain.keys()))
        print '===== Searching tag: ' + tag + ' ====='
        try:
                for post in client.tagged(tag, filter='text'):
                        if 'errors' in post:
                                if type(post) is dict:
                                        for error in post['errors']:
                                                print 'Error: ' + error['title'] + ': ' + error['detail']
                                else:
                                        print post
                                        print 'Unknown error retrieving tagged posts'
                                sys.exit(1)
                        p = Process(target=ana, name='Ana', args=(post,))
                        p.start()
                        p.join(timeout)
                        if p.is_alive():
                                print 'Timed out'
                                p.terminate()
                                p.join()
                        else:
                                if p.exitcode != 0:
                                        if p.exitcode == -11:
                                                print 'Error: unexpected segfault'
                                        else:
                                                print 'anabot: process terminated with exit code %d' % p.exitcode
                                                sys.exit(p.exitcode)
                time.sleep(waitInterval)
        except SSLError:
                print 'Connection error'
