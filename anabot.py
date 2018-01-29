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
import os.path

from stripogram import html2text

POST_LIMIT_SHORT = 10
POST_LIMIT_LONG = 30
TIMEOUT = 60
WAIT_INTERVAL = 0

VERSION_STRING = '1.1'

MARKOV_FILENAME = 'mark.json'
AR_FILENAME = 'already-reblogged.txt'
TAG_BLACKLIST_FILENAME = 'tag-blacklist.txt'
STATS_FILENAME = 'stats.json'

def checkAPIErrors(response):
        if 'errors' in response:
                if type(response) is dict:
                        for error in post['errors']:
                                print 'Error: ' + error['title'] + ': ' + error['detail']
                else:
                        print response
                        print 'Unknown API error'
                        sys.exit(1)

def runText(text):
        print 'Creating anagram'
        markovChain = loadMarkovChain()
        anagram = createAnagram([c for c in sys.argv[text] if c.isalpha()], markovChain)
        if anagram is not None:
                anagram = anagram[0].upper() + anagram[1:]
                print 'Anagram found:'
                print anagram
        else:
                print '404 Anagram not found'

def runPost(client, url, postID):
        response = client.posts(url + '.tumblr.com', id=postID)
        checkAPIErrors(response)
        with response as post:
                if canTry(post):
                        markovChain = loadMarkovChain()
                        ana(response['posts'][0], bodyNeedsCleaning=True)

'''Connects to Tumblr's REST API. If the connection is successful, returns a TumblrRestClient object. If not, prints an error message and exits. Throws ConnectionError'''
def connect():
        print 'Connecting to Tumblr'
        client = pytumblr.TumblrRestClient(keys.consumerKey, keys.consumerSecret, keys.token, keys.tokenSecret)
        cinfo = client.info()
        if 'errors' in cinfo:
                for error in cinfo['errors']:
                        print 'Error: ' + error['title'] + ': ' + error['detail']
                print '!!! Could not authenticate user. !!!'
                sys.exit(2)
        print 'Authorization successful.'
        return client

def loadAlreadyReblogged():
        if os.path.exists(AR_FILENAME):
                readARFile = open(AR_FILENAME, 'r')
                alreadyReblogged = [int(line.strip()) for line in readARFile.readlines()]
                readARFile.close()
        else:
                alreadyReblogged = []
        return alreadyReblogged

def saveAlreadyReblogged():
        appendARFile = open(AR_FILENAME, 'a+')
        appendARFile.write('%d\n' % post['id'])
        appendARFile.close()

def loadTagBlacklist():
        tagBlacklistFile = open(TAG_BLACKLIST_FILENAME, 'r')
        tagBlacklist = [line.strip() for line in tagBlacklistFile.readlines()]
        tagBlacklistFile.close()
        return tagBlacklist

def loadStats():
        if os.path.exists(STATS_FILENAME):
                readStatsFile = open(STATS_FILENAME, 'r')
                stats = json.loads(readStatsFile.read())
                readStatsFile.close()
        else:
                stats = {
                        'tagsSearched': 0,
                        'postsSearched': 0,
                        'postsWithBLTags': 0,
                        'postsTried': 0,
                        'postsAnagrammed': 0
                }
        return stats

def saveStats(stats):
        writeStatsFile = open(STATS_FILENAME, 'w+')
        writeStatsFile.write(json.dumps(stats))
        writeStatsFile.close()

def loadMarkovChain():
        print 'Reading Markov data'
        markovChainFile = open(MARKOV_FILENAME, 'r')
        markovChain = json.loads(markovChainFile.read())
        markovChainFile.close()
        print 'Done (%d unique symbols)' % len(markovChain)
        return markovChain

'''Returns true if post is a dict object and has a 'body' attribute. Otherwise, prints an error message and returns false.'''
def canTry(post):
        if type(post) is not dict:
                print 'Unexpected post format'
                return False
        if not 'body' in post:
                print 'No body attribute'
                return False
        return True

def shouldTry(post, alreadyReblogged, tagBlacklist, postLimitShort, postLimitLong, stats=None):
        if post['id'] in alreadyReblogged:
                print 'Already reblogged'
                return False
        body = post['body']
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
                                if type(stats) is dict:
                                        stats['postsWithBLTags'] += 1
                                        saveStats(stats)
                                print 'Post tagged with #' + tag
                                return False
        return True

def reblog(post, reblogComment):
        client.reblog('anagram-robot.tumblr.com', id=post['id'], reblog_key=post['reblog_key'], tags=['anagram'], state='queue', comment=reblogComment + '<br><br><small>- Anagram robot ' + VERSION_STRING + '. I find anagrams for stuff. I know I don\'t always make sense, but I\'m getting better!</small>')
        alreadyReblogged.append(post['id'])
        saveAlreadyReblogged()

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

#'''Chooses a random state from the states in nextDict based on their frequencies'''
#def randNext(nextDict):
#        totalFreq = 0
#        for next in nextDict:
#                totalFreq += nextDict[next]
#        rand = int(random.random() * totalFreq)
#        cumulativeFreq = 0
#        for next in nextDict:
#                cumulativeFreq += nextDict[next]
#                if cumulativeFreq >= rand:
#                        return next

def clean(symbol):
        return ''.join([l for l in symbol.lower() if l.isalpha()])

#def createAnagram(letters, chain, s1=None, s2=None, recursion=1, printCurr=True, soFar=None):
def createAnagram(letters, chain, s1=None, s2=None):
        #        print 'createAnagram(<letters>, <chain>, s1=\'%s\', s2=\'%s\', recursion=%d' % (s1, s2, recursion)
        try:
                if (s1 is None) or (s2 is None):
                        symbols = chain
                else:
                        symbols = chain[s1][s2].copy() #copy the dictionary of possible next symbols
        except KeyError as ke:
                print 'KeyError: ' + str(ke)
                sys.exit(0) #any other exit code will cause Ana to exit
        while True:
                if (s1 is None) or (s2 is None):
                        nexts1 = random.choice(symbols.keys())
                        nexts2 = random.choice(symbols[nexts1].keys())

#                        if printCurr: #debug
#                                nextSoFar = nexts2
                else:
                        nexts1 = s2
                        nexts2 = random.choice(symbols.keys())
                        symbols.pop(nexts2)

#                        if printCurr: #debug
#                                nextSoFar = soFar + ' ' + nexts2
#                                sys.stdout.write("\033[K") #clear the console line
#                                print nextSoFar
#                                sys.stdout.write("\033[K") #clear the console line
#                                print 'Current chain length: %d' % (recursion - 1)
#                                sys.stdout.write("\033[F") #move cursor to start of last line
#                                sys.stdout.write("\033[F") #move cursor to start of last line
                remainingLetters = removeWord(clean(nexts2), letters)
                if remainingLetters is not None: #the word fits in the list letters
                        if len(remainingLetters) == 0: #base case: the word uses the last of the letters
                                return nexts2
#                        if printCurr: #debug
#                                rest = createAnagram(remainingLetters, chain, s1=nexts1, s2=nexts2, recursion=recursion + 1, printCurr=True, soFar=nextSoFar)
#                        else:
#                                rest = createAnagram(remainingLetters, chain, s1=nexts1, s2=nexts2, recursion=recursion + 1)
                        rest = createAnagram(remainingLetters, chain, s1=nexts1, s2=nexts2)
                        if rest is not None: #found an anagram!
                                return nexts2 + ' ' + rest
                if len(symbols) == 0:
                        return None

'''Returns True if Ana was successful, False if they weren't'''
def ana(post, markovChain, stats=None, bodyNeedsCleaning=False):
        if type(stats) is dict:
                stats['postsTried'] += 1
                saveStats(stats)
        body = post['body']
        postLetters = [c for c in body.lower() if c.isalpha()]
        print body

        anagram = createAnagram(postLetters, markovChain)
        if anagram is not None:
                anagram = anagram[0].upper() + anagram[1:]
                reblog(post, anagram)
                if type(stats) is dict:
                        stats['postsAnagrammed'] += 1
                        saveStats(stats)
                print 'Anagram found:'
                print anagram
                return True
        
        print '404 Anagram not found'
        return False

def runAnaProcess(post, markovChain, stats=None, bodyNeedsCleaning=False):
        p = Process(target=ana, name='Ana', args=(post, markovChain, stats, bodyNeedsCleaning))
        p.start()
        p.join(TIMEOUT)
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
        stats.update(loadStats())

print '===== Starting Anabot v' + VERSION_STRING + ' ====='

# check for command-line options
if len(sys.argv) > 1:
        if sys.argv[1] == '--text':
                if len(sys.argv) > 2:
                        runText(sys.argv[2])
                        sys.exit(0)
                else:
                        print 'Usage: anabot.py [--text <text>]'
                        sys.exit(1)
        elif sys.argv[1] == '--post':
                pass # will deal with this option later
        else:
                print 'Unknown option ' + sys.argv[1]
                sys.exit(1)

# all futher features require a Tumblr API client
client = None
try:
        client = connect()
except ConnectionError:
        print '!!! Could not connect to Tumblr. !!!'
        sys.exit(1)

# handle rest of command-line options
if len(sys.argv) > 1:
        if sys.argv[1] == '--post':
                if len(sys.argv) > 3:
                        runPost(client, sys.argv[2], sys.argv[3])
                        sys.exit(0)
                else:
                        print 'Usage: anabot.py [--post <blog> <post id>]'
                        sys.exit(1)

# no command-line options (default behavior)

markovChain = loadMarkovChain()
alreadyReblogged = loadAlreadyReblogged()
tagBlacklist = loadTagBlacklist()
stats = loadStats()

while True:
        tag = clean(random.choice(markovChain.keys()))
        print '===== Searching tag: ' + tag + ' ====='
        try:
                response = client.tagged(tag, filter='text')
                checkAPIErrors(response)
                stats['tagsSearched'] += 1
                for post in response:
                        stats['postsSearched'] += 1
                        if canTry(post) and shouldTry(post, alreadyReblogged, tagBlacklist, POST_LIMIT_SHORT, POST_LIMIT_LONG, stats=stats):
                                runAnaProcess(post, markovChain, stats=stats)
                saveStats(stats)
                time.sleep(WAIT_INTERVAL)
        except SSLError:
                print 'Connection error'
