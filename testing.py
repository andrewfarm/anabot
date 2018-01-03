import pytumblr
import keys
import time
import sys
#client = pytumblr.TumblrRestClient(keys.consumerKey, keys.consumerSecret, keys.token, keys.tokenSecret)
#client.create_text('anagram-robot.tumblr.com', state='private', body='This is a test post.', tags=('anagram',))

for i in range(10):
        print i
        sys.stdout.write("\033[F")
        time.sleep(1)
