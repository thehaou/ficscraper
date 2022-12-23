This directory is used by pandas to dedupe the collected fanfiction data `ficscraper` is trying to insert into the sqlite db.

Why do dupes happen? Could be any number of reasons for why AO3 might give us a dupe fic. 
- Maybe you just bookmarked a fic and AO3 hasn't had time to reflect it to you yet, but while processing, AO3 finally propagated the changes.
- Maybe a fic got deleted.
- Maybe it's a different network-related issue.

Learn more about `ficscraper`'s CSV-scraping [here](https://github.com/thehaou/ficscraper/wiki/How-to-Use#-archive-of-our-own-ao3).