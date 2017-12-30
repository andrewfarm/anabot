import pytumblr
import keys
client = pytumblr.TumblrRestClient(keys.consumerKey, keys.consumerSecret, keys.token, keys.tokenSecret)
client.create_text('anagram-robot.tumblr.com', state='private', body='This is a test post.', tags=('anagram',))
