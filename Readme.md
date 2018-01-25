# Anabot, your friendly neighborhood anagram robot

A Tumblr Markov bot that (spoilers) makes anagrams (using Python and some stuff)

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

## What if it doesn't do???

You can contact me by gathering the jawbone of an arctic hare, the wings of a slightly confused dragonfly, and a twig of parsley (for looks) and burying them under the light of the harvest moon. Or you can submit an issue.
