import pytumblr
import keys
client = pytumblr.TumblrRestClient(keys.consumerKey, keys.consumerSecret, keys.token, keys.tokenSecret)
client.create_text('anagram-robot.tumblr.com', state='private', body='test', tags=('anagram',))
