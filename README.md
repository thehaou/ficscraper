# 🚢📚🔖 ficscraper ✍💬❤️
⚠️ [Getting Started / Installation](https://github.com/thehaou/ficscraper/wiki/Installation) • ❓[How to Use](https://github.com/thehaou/ficscraper/wiki/How-to-Use) • 🙋 [FAQ/Q&A](#frequently-asked-questions) • 📌 [Roadmap](#roadmap)

❄️ [AO3 Year-In-Review](https://github.com/thehaou/ficscraper/wiki/How-to-Use#year-in-review) • 📈 [Ad Hoc Stats](https://github.com/thehaou/ficscraper/tree/master/src/sqlite/)

---

The goal of `ficscraper` is to provide fanfiction readers with a way to generate & interpret stats on their reading habits on websites that provide none. For example:

* How many words of Harry Potter fanfiction did I read in the year 20XX?
* What is the ranking of authors I've read the most from (either word count or # of fics-wise)?
* For each fandom I read this year, what was the order I started reading them in, and which fic did I read from them first?
* Based on the tags of all the fics I've read, what would my "ideal fic" look like?

And so on. Fanfiction itself is a labor of love and I genuinely hope that `ficscraper` can provide you with some interesting ways to investigate your own personal relationship with it.
### Getting Started / Installation 
This repo now has a wiki! Installation instructions [here](https://github.com/thehaou/ficscraper/wiki/Installation).

### How to Use
How-to-use instructions [here](https://github.com/thehaou/ficscraper/wiki/How-to-Use).

### Roadmap
This is a hobby project I started back in 2018 when I discovered AO3 had axed any plans to make a public API for stats. It was brought back to life in 2022 after being inspired by Spotify Wrapped; I had fallen deep into the Batman iceberg that year and wanted to make my own AO3 Year-In-Review to send my friends.

As such, this will continue to be updated whenever I a) feel the urge b) have the time. Discussion is welcome, as are contributions (though I'd like to review all incoming PRs).

The following are vaguely ordered in terms of priority:

#### More card templates for AO3 Year-In-Review
1. Big stat template (eg. total wordcount)
2. Reading personality (5 letters, 10 values, slider representation, different CSS border per result) (ex: multichap/longfic/angst/fandom-loyal/multiship)
3. E/M/T/G/unknown %s
4. Ship-slash (color by ship type)
5. Your Ideal Work (based on tags of fics - requires having tags on fics, though, which is MASSIVE - how to structure??)
6. Timeline of when you got into a fandom throughout the year
7. Bucket template (eg. 0k-2k, 2k-20k, 2k-200k, 200k+)

#### Support for including ranking stats by user-defined bookmark tags
TODO - this is based off of my own personal SS/S/A/B/C ranking system on bookmarks. Include a writeup about why I use this system and how I've gotten mileage out of it.

#### Support for ingesting User History
Most folks don't bookmark. Supporting User History would be big.

(Feature request [here](https://github.com/thehaou/ficscraper/issues/3))

#### Support for figuring out just how far behind you are on subscriptions
History politely tells you when you last visited a fic, and whether or not the fic has been updated since. The Chapter Index for a work (https://archiveofourown.org/works/<work_id>/navigate) tells you exactly when a chapter was uploaded.

Combining the two, `ficscraper` could generate a list of all your in-progress subscriptions and the exact chapter you left off on. This is helpful if you have subscription notifs turned off for some reason (why?) or you subscribed to too many fics, and don't want to look up one-by-one in your notifications for which chapter you left off on.

My personal goal for calculating this stat would be getting this exported visually as a table (either CSV to plug into something like Google sheets), or just an image sorted by # of words left, or perhaps descending order of # of chapters left to read... and so on.

Some pitfalls: AO3 tells you when you last visited; it doesn't tell you when you first subscribed. This stat generation is reliant on you NOT visiting a fic since you subscribed, and once you DO visit again, you read all the way to the most recent chapter.

#### Support for ingesting User Collections
Some folks use collections. Need to gather more info about folks who use these.

#### Support for stats for fanfic writers
Need to look into this. Is there anything scraping can provide that the AO3 Statistics page can't? My gut says no, but it's worth looking into regardless.

### Contact Info
I'd prefer if discussion was kept to the Discussions tab, but if for some reason you need to contact me directly, my Discord tag is `thehaou#5166`.

### Disclaimer
I am certainly not affiliated with the Organization of Transformative Works in any way - this in an unofficial fan-made repo.
