import logging
import configparser

from scrapers.ao3.tag_wrangler import AO3TagWrangler
from scrapers.ao3.utils_requests import read_credentials
from sqlite.constants import ROOT_DIR


if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.INFO,  # Switch to logging.INFO for less output
                        format="%(levelname)s - %(message)s")

    # Read the user's credentials
    username, password = read_credentials()

    # Use said credentials...
    wrangle_scraper = AO3TagWrangler(username=username, password=password)

    # Wrangle all work tags known to not be wrangled yet
    wrangle_scraper.wrangle_all_unknown_work_tags()

    wrangle_scraper.close_connection()

    logging.info('Done adding un-wrangled tags back to the sqlite db.')
    logging.info('ficscraper successfully finished running.')
