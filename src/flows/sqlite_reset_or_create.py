# -*- coding: utf-8 -*-
import logging

from sqlite.utils_sqlite import clean_slate_sqlite

if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.INFO,  # Switch to logging.INFO for less output
                        format="%(levelname)s - %(message)s")
    clean_slate_sqlite()

    logging.info('Done resetting sqlite db (you can find it under src/sqlite/ficscraper.db).'                                  
                 '\nIt now has completely empty new tables waiting for you to populate them.')
    logging.info('ficscraper successfully finished running.')
