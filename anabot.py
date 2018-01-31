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
from bs4 import BeautifulSoup

POST_LIMIT_SHORT = 10
POST_LIMIT_LONG = 30
TIMEOUT = 60
WAIT_INTERVAL = 0

VERSION_STRING = '1.2'

MARKOV_FILENAME = 'mark.json'
AR_FILENAME = 'already-reblogged.txt'
TAG_BLACKLIST_FILENAME = 'tag-blacklist.txt'
STATS_FILENAME = 'stats.json'

debug = False

def checkAPIErrors(response):
        if 'errors' in response:
                if type(response) is dict:
                        for error in post['errors']:
                                print 'Error: ' + error['title'] + ': ' + error['detail']
                else:
                        print response
                        print 'Unknown API error'
                        sys.exit(1)

def runTextMode(text):
        markovChain = loadMarkovChain()
        print 'Creating anagram for "' + text + '"'
        anagram = createAnagram([c for c in text if c.isalpha()], markovChain)
        if anagram is not None:
                anagram = anagram[0].upper() + anagram[1:]
                print 'Anagram found:'
                print anagram
        else:
                print '404 Anagram not found'

def runPostMode(client, url, postID):
        response = client.posts(url, id=postID)
        checkAPIErrors(response)
        if canTry(response):
                markovChain = loadMarkovChain()
                ana(response['posts'][0], bodyNeedsCleaning=True)

def isOriginal(textpost):
        #TODO currently returns false for posts without a trail attribute (e.g. chat posts) or with an empty trail list
        return (('trail' in textpost) and
                (len(textpost['trail']) > 0) and
                ('is_current_item' in textpost['trail'][0]))

def runBlogMode(client, url):
        batchSize = 20
        offset = 0
        response = client.posts(url, offset=offset)
        checkAPIErrors(response)
        
        markovChain = loadMarkovChain()
        alreadyReblogged = loadAlreadyReblogged()
        tagBlacklist = loadTagBlacklist()
        
        while len(response['posts']) > 0:
                try:
                        for post in response['posts']:
                                if canTry(post) and isOriginal(post) and shouldTry(post, alreadyReblogged, tagBlacklist, POST_LIMIT_SHORT, POST_LIMIT_LONG, bodyNeedsCleaning=True):
                                        runAnaProcess(post, markovChain, alreadyReblogged, bodyNeedsCleaning=True)
                except SSLError:
                        print 'Connection error'
                offset += batchSize
                response = client.posts(url, offset=offset)
                checkAPIErrors(response)

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

def saveAlreadyReblogged(postID):
        appendARFile = open(AR_FILENAME, 'a+')
        appendARFile.write('%d\n' % postID)
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

def lastParagraph(text):
        ptags = BeautifulSoup(text, 'html.parser').find_all('p')
        if len(ptags) == 0:
                return None
        else:
                return ptags[-1].get_text()

def getLetters(text):
        return [c for c in text.lower() if c.isalpha()]

def shouldTry(post, alreadyReblogged, tagBlacklist, postLimitShort, postLimitLong, bodyNeedsCleaning=False, stats=None):
        if post['id'] in alreadyReblogged:
                print 'Already reblogged'
                return False
        body = post['body']
        if bodyNeedsCleaning:
                body = lastParagraph(body)
                if body is None:
                        print 'No paragraph tags found'
                        return False
        postLetters = getLetters(body)
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

def createAnagram(letters, chain, s1=None, s2=None, recursion=1, soFar=None):
#def createAnagram(letters, chain, s1=None, s2=None):
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

                        if debug:
                                nextSoFar = nexts2
                else:
                        nexts1 = s2
                        nexts2 = random.choice(symbols.keys())
                        symbols.pop(nexts2)

                        if debug:
                                nextSoFar = soFar + ' ' + nexts2
                                sys.stdout.write("\033[K") #clear the console line
                                print nextSoFar
                                sys.stdout.write("\033[K") #clear the console line
                                print 'Current chain length: %d' % (recursion - 1)
                                sys.stdout.write("\033[F") #move cursor to start of last line
                                sys.stdout.write("\033[F") #move cursor to start of last line
                remainingLetters = removeWord(clean(nexts2), letters)
                if remainingLetters is not None: #the word fits in the list letters
                        if len(remainingLetters) == 0: #base case: the word uses the last of the letters
                                return nexts2
                        if debug:
                                rest = createAnagram(remainingLetters, chain, s1=nexts1, s2=nexts2, recursion=recursion + 1, soFar=nextSoFar)
                        else:
                                rest = createAnagram(remainingLetters, chain, s1=nexts1, s2=nexts2)
#                        rest = createAnagram(remainingLetters, chain, s1=nexts1, s2=nexts2)
                        if rest is not None: #found an anagram!
                                return nexts2 + ' ' + rest
                if len(symbols) == 0:
                        return None

'''Returns True if Ana was successful, False if they weren't'''
def ana(post, markovChain, alreadyReblogged, stats=None, bodyNeedsCleaning=False):
        if type(stats) is dict:
                stats['postsTried'] += 1
                saveStats(stats)
        body = post['body']
        if bodyNeedsCleaning:
                body = lastParagraph(body)
                if body is None:
                        print 'ana: could not clean body HTML (no paragraph tags found)'
                        return False
        postLetters = getLetters(body)
        print body

        anagram = createAnagram(postLetters, markovChain)
        if anagram is not None:
                anagram = anagram[0].upper() + anagram[1:]
                reblog(post, anagram)
                saveAlreadyReblogged(post['id'])
                if type(stats) is dict:
                        stats['postsAnagrammed'] += 1
                        saveStats(stats)
                print 'Anagram found:'
                print anagram
                return True
        
        print '404 Anagram not found'
        return False

def runAnaProcess(post, markovChain, alreadyReblogged, stats=None, bodyNeedsCleaning=False):
        p = Process(target=ana, name='Ana', args=(post, markovChain, alreadyReblogged, stats, bodyNeedsCleaning))
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
        alreadyReblogged = loadAlreadyReblogged()
        if type(stats) is dict:
                stats.update(loadStats())

print '===== Starting Anabot v' + VERSION_STRING + ' ====='

# check for command-line options
# there is probably a more compact way of writing this - but it will do for now
argc = len(sys.argv)
mode = None #default
modeParams = []
i = 1
while i < argc:
        opt = sys.argv[i]
        if opt == '--text':
                if mode is not None:
                        print 'mode cannot be both \'' + mode + '\' and \'text\''
                        sys.exit(1)
                if i + 1 >= argc:
                        print 'Usage: anabot.py --text <text to anagram>'
                        sys.exit(1)
                mode = 'text'
                modeParams.append(sys.argv[i + 1])
                i += 1
        elif opt == '--post':
                if mode is not None:
                        print 'mode cannot be both \'' + mode + '\' and \'post\''
                        sys.exit(1)
                if i + 2 >= argc:
                        print 'Usage: anabot.py --post <blog url> <post ID>'
                        sys.exit(1)
                mode = 'post'
                modeParams.append(sys.argv[i + 1].lower())
                modeParams.append(int(sys.argv[i + 2]))
                i += 2
        elif opt == '--blog':
                if mode is not None:
                        print 'mode cannot be both \'' + mode + '\' and \'blog\''
                        sys.exit(1)
                if i + 1 >= argc:
                        print 'Usage: anabot.py --blog <blog url>'
                        sys.exit(1)
                mode = 'blog'
                modeParams.append(sys.argv[i + 1].lower())
                i += 1
        elif opt == '-d':
                debug = True
        else:
                print 'Unknown option ' + sys.argv[i]
                sys.exit(1)
        i += 1

# run in text mode
if mode == 'text':
        print 'Running in offline (text-only) mode'
        runTextMode(modeParams[0])
        sys.exit(0)

# all futher features require a Tumblr API client
client = None
try:
        client = connect()
except ConnectionError:
        print '!!! Could not connect to Tumblr. !!!'
        sys.exit(1)

# run in post mode
if mode == 'post':
        print 'Running on post %d from %s.tumblr.com' % (modeParams[1], modeParams[0])
        runPostMode(client, modeParams[0], modeParams[1])
        sys.exit(0)

# run in blog mode
if mode == 'blog':
        print 'Searching %s.tumblr.com' % modeParams[0]
        runBlogMode(client, modeParams[0])
        sys.exit(0)

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
                                runAnaProcess(post, markovChain, alreadyReblogged, stats=stats)
                saveStats(stats)
                time.sleep(WAIT_INTERVAL)
        except SSLError:
                print 'Connection error'
