`ficscraper.db` comes populated with aliases for the 200 most popular tags on AO3. The rest of the tables are empty by default.

You can interact with the database via [sqlite's command-line-interface (CLI)](https://sqlite.org/cli.html).

For example, when I run against my own AO3 stats:

* Work on the `fiscraper` venv
```commandline
$ workon ficscraper
(ficscraper) $
```

* Start up sqlite cli
```commandline
(ficscraper) $ sqlite3 ficscraper.db
SQLite version 3.39.4 2022-09-07 20:51:41
Enter ".help" for usage hints.
sqlite> 
```

* Calculate total # of words read across all bookmarked fics from 1/1/2022 to 12/31/2022:
```shell
sqlite> SELECT sum(word_count) as total_word_count
...> FROM works
...> WHERE date_bookmarked >= 1641024000 AND date_bookmarked < 1672560000;

28332434
```

* Calculate the 5 largest fics read in 2022 based on bookmarks (and include author information):
```shell
sqlite> SELECT works.title, works.word_count, authors.author_id
   ...> FROM works
   ...> INNER JOIN authors on works.work_id = authors.work_id
   ...> WHERE date_bookmarked >= 1641024000 AND date_bookmarked < 1672560000
   ...> ORDER BY word_count DESC
   ...> LIMIT 5;
marigolds|602525|colbub
Just gonna let em hate|367672|StarryKitty013
Pity of the World|330787|appending_fic
The Lost and Forgotten|272413|Litcraz
The Prince of Clowns|268893|CrazyJanaCat
```

* Calculate my top 10 largest fandoms of ALL TIME based on how many works I've bookmarked from them:
```shell
sqlite> SELECT fandom_name, count(work_id) as num_fics
   ...> FROM fandoms
   ...> GROUP BY fandom_name 
   ...> ORDER BY num_fics DESC
   ...> LIMIT 10;
Batman - All Media Types|573
Harry Potter - J. K. Rowling|362
Final Fantasy VII|226
DCU|187
Batman (Comics)|178
Batman v Superman: Dawn of Justice|177
Superman - All Media Types|161
Star Wars - All Media Types|127
Compilation of Final Fantasy VII|115
Star Wars Prequel Trilogy|104
```

* Figure out what the first fic I read was for each of my top 5 big fandoms this year, AND when I bookmarked that fic
```shell
sqlite> SELECT fandoms.fandom_name, min(works.date_bookmarked) as first_bookmark, count(works.work_id) as num_works, sum(works.word_count) as total_wc, title, works.work_id, authors.author_id
   ...>     FROM works
   ...>     INNER JOIN fandoms ON works.work_id = fandoms.work_id
   ...>     INNER JOIN authors on works.work_id = authors.work_id
   ...>     WHERE date_bookmarked >= 1641024000 AND date_bookmarked < 1672560000    
   ...>     GROUP BY fandoms.fandom_name
   ...>     ORDER BY total_wc DESC
   ...> LIMIT 10;
Batman - All Media Types|1656630000|573|8058963|repetitio est mater studiorum|31849066|distortopia
Harry Potter - J. K. Rowling|1641600000|143|4814767|Standby to Standby|35995084|ClasslessTulip
Star Wars - All Media Types|1648422000|109|4405808|War Drums|34917937|intermundia
Star Wars Prequel Trilogy|1648422000|91|3113133|War Drums|34917937|intermundia
Star Wars: The Clone Wars (2008) - All Media Types|1648422000|60|2567849|Lex Talionis|23970436|intermundia
```

* Calculate my top 3 tags per rating category on AO3, across all time
```shell
sqlite> WITH tag_counts_cte AS
   ...> (
   ...> SELECT cr, tag_id, num_occ, ROW_NUMBER() OVER (
   ...> PARTITION BY cr
   ...> ORDER BY num_occ DESC ) row_number
   ...> FROM (    
   ...> SELECT
   ...> works.content_rating as cr,
   ...> wrangled_work_tags.wrangled_tag_id as tag_id,
   ...> COUNT(works.work_id) as num_occ                 
   ...> FROM works    
   ...> INNER JOIN work_tags ON works.work_id = work_tags.work_id
   ...> INNER JOIN wrangled_work_tags ON work_tags.work_tag_id = wrangled_work_tags.work_tag_id     
   ...> GROUP BY works.content_rating, wrangled_work_tags.wrangled_tag_id
   ...> ORDER BY num_occ DESC
   ...> )        
   ...> )
   ...> SELECT cr, tag_id, num_occ
   ...> FROM tag_counts_cte
   ...> WHERE row_number <= 3
   ...> ORDER BY cr DESC;
T|Alternate Universe - Canon Divergence|135
T|Angst|104
T|Fluff|83
M|Angst|102
M|Alternate Universe - Canon Divergence|86
M|Hurt/Comfort|59
G|Fluff|47
G|Humor|31
G|Alternate Universe - Canon Divergence|30
E|<redacted>|<redacted>
E|<redacted>|<redacted>
E|<redacted>|<redacted>
|Angst|20
|Alternate Universe - Canon Divergence|15
|Hurt/Comfort|15
```

* Exit/quit sqlite
```shell
sqlite> .quit
(ficscraper) $
```

* Stop using the `ficscraper` venv
```commandline
(ficscraper) $ deactivate
$
```

The world is your oyster. Or the `ficscraper.db` is, anyways.