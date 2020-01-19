# Anabot, your friendly neighborhood anagram robot

A Tumblr Markov bot that (spoilers) makes anagrams

## What are all these files?

links.txt contains links to all the online books I have at some point used for training.
tag-blacklist.txt contains a list of tags that Anabot avoids.

## Which snake do I use

I use Python 2.7.

## How to do

Mark.py contains a python script that builds a markov chain with the training text and outputs it in mark.json. Anabot.py contains the actual Tumblr bot.

For obvious reasons, this bot cannot run with all features without the login information. However, you can still use

```
python anabot.py --text '<some text, for instance: Raisins Are Delicious>'
```

in order to find an an anagram for input text, using Anabot's predictive-text anagram-finding algorithm.
