import pytumblr
import random
from pprint import pprint
import keys

arFilename = 'already-reblogged.txt'
appendARFile = open(arFilename, 'a+')
readARFile = open(arFilename, 'r')
alreadyReblogged = [int(line.strip()) for line in readARFile.readlines()]
readARFile.close()

wordsFilename = 'google-10000-english.txt'
wordsFile = open(wordsFilename, 'r')
words = [line.strip() for line in wordsFile.readlines()]
wordsFile.close()

client = pytumblr.TumblrRestClient(keys.consumerKey, keys.consumerSecret, keys.token, keys.tokenSecret)

def wordFits(word, textLetters):
        textLetters = list(textLetters) #make a copy of the text
        for letter in word:
                if letter in textLetters:
                        textLetters.remove(letter)
                else:
                        return False
        return True

def reblog(post, reblogComment):
        client.reblog('anagram-robot.tumblr.com', id=post['id'], reblog_key=post['reblog_key'], state='published', comment=reblogComment + '<br><br>Hi guys! I\'m a bot! I\'m in development right now so I don\'t really know what I\'m doing<br><br><span style="font-size: 10pt;"><em>- Anagram robot 0.0</em></span>')

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
        if (len(postLetters) < 10) or (len(postLetters) > 60):
                print 'Too short or long'
                return False

        anagram = []
        for w in words:
                while wordFits(w, postLetters):
                        for l in w:
                                postLetters.remove(l)
                        anagram.append(w)
                if (len(postLetters) == 0):
                        random.shuffle(anagram)
                        reblogComment = ' '.join(anagram)
                        print reblogComment
                        reblog(post, reblogComment)
                        alreadyReblogged.append(post['id']);
                        appendARFile.write('%d\n' % post['id'])
                        return True
        print '404 Anagram not found'
        return False

#postToReblog = random.choice(client.tagged('shitpost', filter='text'))
for post in client.tagged('shitpost', filter='text'):
        print ana(post)

appendARFile.close()
