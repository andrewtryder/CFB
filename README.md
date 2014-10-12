[![Build Status](https://travis-ci.org/reticulatingspline/CFB.svg?branch=master)](https://travis-ci.org/reticulatingspline/CFB)

# Limnoria plugin for CFB (College Football)

## Introduction

There are at least 3 plugins floating around for WA. One of the big differences with each variant from users
is the differences in output due to the verbosity from how WA answers questions. Some answers can be
10+ lines and easily flood a channel, either having the bot flood off or getting it banned from a channel.
WA's API also has some input options that can be handy, along with some verbose "error" messages that can help
the user, which the other plugins do not utilize. I wanted to use the getopts power and make some configuration
options to display the data in a more friendly manner.

## Install

You will need a working Limnoria bot on Python 2.7 for this to work.

Go into your Limnoria plugin dir, usually ~/supybot/plugins and run:

```
git clone https://github.com/reticulatingspline/CFB
```

To install additional requirements, run:

```
pip install -r requirements.txt 
```

Next, load the plugin:

```
/msg bot load CFB
```

## About

All of my plugins are free and open source. When I first started out, one of the main reasons I was
able to learn was due to other code out there. If you find a bug or would like an improvement, feel
free to give me a message on IRC or fork and submit a pull request. Many hours do go into each plugin,
so, if you're feeling generous, I do accept donations via Amazon or browse my [wish list](http://amzn.com/w/380JKXY7P5IKE).

I'm always looking for work, so if you are in need of a custom feature, plugin or something bigger, contact me via GitHub or IRC.