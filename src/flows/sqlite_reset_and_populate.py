# -*- coding: utf-8 -*-
import logging

from sqlite.utils_sqlite import clean_slate_sqlite

if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.INFO,  # Switch to logging.INFO for less output
                        format="%(levelname)s - %(message)s")
    clean_slate_sqlite()

    logging.info('Done resetting & populating sqlite db (you can find it under src/sqlite/ao3_yir.db).'                                  
                 '\nIf you have experience with querying, you can use the sqlite CLI to run ad hoc stats:'
                 '\n\n\thttps://sqlite.org/cli.html\n'
                 '\nSome general-purposes fic-stat functions are available under src/sqlite/sqlite_stats.py as well.'
                 '\nYou can also now run flows that rely on sqlite being populated, such as AO3 year-in-review:'
                 '\n\n\t./ficscraper_cli.sh --generate year_in_review 2022\n')
    logging.info('ficscraper successfully finished running.')
