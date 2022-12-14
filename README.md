# 🚢📚🔖 ficscraper ✍💬❤️
[How it works](#supported-fanfiction-websites) • [System requirements](#requirements) • [AO3 Year-In-Review]() • [Roadmap](#roadmap)

---

The goal of `ficscraper` is to provide fanfiction readers with a way to generate & interpret stats on their reading habits on websites that provide none. For example:

* How many words of Harry Potter fanfiction did I read in the year 20XX?
* What is the ranking of authors I've read the most from (either word count or # of fics-wise)?
* For each fandom I read this year, what was the order I started reading them in, and which fic did I read from them first?
* Based on the tags of all the fics I've read, what would my "ideal fic" look like?

(And so on.)

## Supported fanfiction websites
Currently `ficscraper` only supports stats on [Archive of Our Own](https://archiveofourown.org/) (aka AO3). This is due to AO3's rich tagging system that allows significant more flexibility in finding patterns in fics read.

Other fanfiction websites such as [FanFiction.net](https://www.fanfiction.net/) (FFN), [Wattpad](https://www.wattpad.com/), and [Tumblr blogs dedicated to fic writing](https://www.tumblr.com/tagged/fanfiction?sort=top) are considered out-of-scope for this project until I feel `ficscraper`'s AO3 side is sufficiently developed. I more than welcome discussion on implementation of `ficscraper` for other websites though!

## Functionality
`ficscraper` works in three stages:
1. **Extract** user's interactions with fic, such as:
   1. reading history
   2. kudos history
   3. personal bookmarks & tags
2. **Transfer & load** the collected information into SQLite, an extremely handy no-installation-needed/in-memory/embedded database management system.
   1. One could actually stop at this stage if they want to begin running stats on their interactions. See here (TODO) for example queries you can run against SQLite. For users unfamiliar with Python or coding in general, see here (TODO) for a detailed walkthrough on how to get some popular types of stats.
3. **Visualize** certain types of interactions into something nicely readable for humans (and can be shared)!
   1. See here (TODO) for `ficscraper`'s current visualization templates. (It uses templated HTML+CSS with some Python mixed in.)
   2. If you're here to learn how to create your own **AO3-Year-In-Review**, see here (TODO).

## Frequent Q&A
Please submit legitimate bugs/errors with `ficscraper` to Issues (see here (TODO)), and all other suggestsions/questions to Discussions (see here (TODO)).

---

**Q.** Why didn't you make a website and have it run ficscraper for me instead? I don't want to have to do all this coding work, and it'd be nice if I could just login and see my stats rather than have to do upkeep myself.

**A.** A couple key reasons. 

1. I'm setting up a session with AO3 by literally scraping the authentication token and using it for the whole session. Furthermore, I'm requiring plaintext username & passwords to even grab said token. This is frankly way out of my comfort zone to even think about putting on a website - I'm not fluent in implementing website security, and I don't want to be on the hook for your account getting hacked.
2. AO3 rate limits approximately 20 requests per 10 minutes. This is perfectly fine when you're slowly reading through a multichapter fic - it's less fine when there are 200+ pages of bookmarks `ficscraper` is trying to grab. Multiply it out to multiple users and you can quickly see how the throughput of this falls through the floor.

---

**Q.** Why Python 3.9?

**A.** No real reason; it was newish at the time of implementation and bs4 is pretty straightforward to use in Python.

## Requirements
This project runs on Python 3.9. You will unfortunately need to have Python installed.

1. See here (TODO) if you're not a coder and have never touched Python before - this is a step-by-step guide on how to cleanly install it onto your system, whether that be Windows/Mac (aka Unix)/Linux
2. Once you're done installing Python 3.9, see here (TODO) for `ficscraper`'s instructions.

## Roadmap
This is a hobby project I started back in 2018 when I discovered AO3 had axed any plans to make a public API for stats. It was brought back to life in 2022 after being inspired by Spotify Wrapped; I had fallen deep into the Batman iceberg that year and wanted to make my own AO3 Year-In-Review to send my friends.
As such, this will continue to be updated whenever I a) feel the urge b) have the time. Discussion is welcome, as are contributions (though I'd like to review all incoming PRs).

Fanfiction itself is a labor of love and I genuinely hope that `ficscraper` can provide you with some interesting ways to investigate your own personal relationship with it.

### More card templates for AO3 Year-In-Review 
1. Big stat template (eg. total wordcount)
2. Reading personality (5 letters, 10 values, slider representation, different CSS border per result) (ex: multichap/longfic/angst/fandom-loyal/multiship)
3. E/M/T/G/unknown %s
4. Ship-slash (color by ship type)
5. Your Ideal Work (based on tags of fics - requires having tags on fics, though, which is MASSIVE - how to structure??)
6. Timeline of when you got into a fandom throughout the year
7. Bucket template (eg. 0k-2k, 2k-20k, 2k-200k, 200k+)

### Support for ingesting User History
TODO

### Support for figuring out just how far behind you are on subscriptions
History politely tells you when you last visited a fic, and whether or not the fic has been updated since. The Chapter Index for a work (https://archiveofourown.org/works/<work_id>/navigate) tells you exactly when a chapter was uploaded.

Combining the two, `ficscraper` could generate a list of all your in-progress subscriptions and the exact chapter you left off on. This is helpful if you have subscription notifs turned off for some reason (why?) or you subscribed to too many fics, and don't want to look up one-by-one in your notifications for which chapter you left off on.

My personal goal for calculating this stat would be getting this exported visually as a table (either CSV to plug into something like Google sheets), or just an image sorted by # of words left, or perhaps descending order of # of chapters left to read... and so on.

Some pitfalls: AO3 tells you when you last visited; it doesn't tell you when you first subscribed. This stat generation is reliant on you NOT visiting a fic since you subscribed, and once you DO visit again, you read all the way to the most recent chapter.

### Support for ingesting User Collections
TODO

### Support for stats for fanfic writers
TODO

## Contact Info
I'd prefer if discussion was kept to the Discussions tab, but if for some reason you need to contact me directly, my Discord tag is `thehaou#5166`.

## Disclaimer
I am certainly not affiliated with the Organization of Transformative Works in any way - this in an unofficial fan-made repo. 