# -*- coding: utf-8 -*-
import logging
import sys

import csv
import configparser

# Set up logging
from src.scrapers.ao3.AO3Scraper import AO3Scraper

logging.basicConfig(level=logging.DEBUG,  # Switch to logging.INFO for less output
                    # format=''
                    )


if __name__ == '__main__':
    sys.setrecursionlimit(5000)  # Be careful not to segfault...
    logging.debug('system recursion depth is...')
    logging.debug(sys.getrecursionlimit())  # 1000 is default... but this is dying for some reason

    config = configparser.ConfigParser()
    config.read('SETUP.INI')

    # ao3
    username = config.get('ao3', 'username')
    password = config.get('ao3', 'password')
    ao3_scraper = AO3Scraper(username, password)

    # Save multiprocessing for some other time - pickling bs4 is pain and I don't want to deal with it right now.
    # Maybe we should do multiprocessing per page over in AO3Scraper instead?
    fics_dict = ao3_scraper.process_bookmarks()

    # Convert to CSV here?
    for fics_data_kind in fics_dict.keys():
        with open('output/csvs/{}.csv'.format(fics_data_kind), 'w+') as f:
            write = csv.writer(f)
            # First write headers
            write.writerow(fics_dict[fics_data_kind][0].keys())

            # Then write all the entries
            write.writerows([fic.values() for fic in fics_dict[fics_data_kind]])
