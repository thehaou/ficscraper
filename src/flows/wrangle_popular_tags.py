import logging

import configparser

from scrapers.ao3.work_tag_scraper import AO3PopularTagScraper
from sqlite.constants import ROOT_DIR

if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.INFO,  # Switch to logging.INFO for less output
                        format="%(levelname)s - %(message)s")

    # Read the user's credentials
    logging.info('Reading user\'s credentials...')
    config = configparser.ConfigParser()
    config.read(ROOT_DIR + '/SETUP.INI')
    username = config.get('ao3', 'username')
    password = config.get('ao3', 'password')

    # Use said credentials...
    wrangle_scraper = AO3PopularTagScraper(username=username, password=password)

    # Wrangle all work tags known to not be wrangled yet
    wrangle_scraper.wrangle_top_200_work_tags()

    wrangle_scraper.close_connection()

    logging.info('Done adding top 200 most popular tags and their wrangled aliases to the db.')
    logging.info('ficscraper successfully finished running.')