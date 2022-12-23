# -*- coding: utf-8 -*-
import argparse
import logging

import csv

from scrapers.ao3.bookmark_scraper import AO3BookmarkScraper
from scrapers.ao3.utils_requests import read_credentials


def set_up_parser():
    parser = argparse.ArgumentParser(
        prog='scrape_bookmarks.py',
        description='Scrapes an AO3 user\'s bookmarks using their login credentials.',
        epilog='https://github.com/thehaou/ficscraper#contact-info'
    )
    parser.add_argument('-p', '--pages',
                        help='Number of bookmark pages to be scraped. There are 20 works per page on AO3.'
                             'EX: to scrape the 100 most recent bookmarks, we\'d ask to fetch 100/20 = 5 pages:'
                             '  ./ficscraper_cli.sh -s bookmarks --pages 5'
                             'By default ficscraper will try to fetch ALL pages.')
    parser.add_argument('-e', '--end_date',
                        help='Sets the upper limit for the time range to scrape fics in. Takes precedence over --pages.'
                             'Format is yyyyMMdd (year-month-date).'
                             'EX: to scrape 5 pages of bookmarks no older than Dec 31, 2022 AO3-server-time:'
                             '  ./ficscraper_cli.sh -s bookmarks --pages 5 --end_date=20221231'
                             'By default ficscraper will not impose an end_date limit (collects all fic prior to start_date)'
                        )
    parser.add_argument('-s', '--start_date',
                        help='Sets the lower limit for the time range to scrape fics in.'
                             'Format is yyyyMMdd (year-month-date).'
                             'EX: to scrape all bookmarks starting on or after Jan 1, 2022 AO3-server-time:'
                             '  ./ficscraper_cli.sh -s bookmarks --start_date=20220101'
                             'By default ficscraper will not impose any start date limit (collects all fics up to end_date')
    return parser


if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.INFO,  # Switch to logging.INFO for less output
                        format="%(levelname)s - %(message)s")

    # Set up parser
    logging.info('Parsing arguments...')
    parser = set_up_parser()
    args = parser.parse_args()

    # Read the user's credentials
    username, password = read_credentials()

    # Use said credentials...
    ao3_scraper = AO3BookmarkScraper(username, password)

    # Scrape user's bookmarks
    fics_dict, bookmarks_json = ao3_scraper.process_bookmarks()

    # Export user's bookmarks to JSON
    with open('output/jsons/bookmarks.json', 'w') as f:
        f.write(bookmarks_json)
    logging.info('Done outputting bookmarks\' json (you can find it in output/jsons)')

    # Export user's bookmarks to various CSV
    for fics_data_kind in fics_dict.keys():
        # Check that there's stuff to write, first of all
        if not fics_dict[fics_data_kind]:
            logging.info('No scraped data found for data kind {}, moving on to the next'.format(fics_data_kind))
            continue

        with open('output/csvs/{}.csv'.format(fics_data_kind), 'w') as f:
            write = csv.writer(f)
            # First write headers
            write.writerow(fics_dict[fics_data_kind][0].keys())

            # Then write all the entries
            write.writerows([fic.values() for fic in fics_dict[fics_data_kind]])

    logging.info('Done outputting bookmarks\' csvs (you can find them in output/csvs)')
    logging.info('ficscraper successfully finished running.')
