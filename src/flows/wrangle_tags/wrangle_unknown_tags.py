import logging
import configparser

# Set up logging
from scrapers.ao3.tag_wrangler import AO3TagWrangler
from sqlite.constants import ROOT_DIR

logging.basicConfig(level=logging.DEBUG,  # Switch to logging.INFO for less output
                    # format=''
                    )


if __name__ == '__main__':
    config = configparser.ConfigParser()
    config.read(ROOT_DIR + '/SETUP.INI')

    # ao3
    username = config.get('ao3', 'username')
    password = config.get('ao3', 'password')
    wrangle_scraper = AO3TagWrangler(username=username, password=password)

    wrangle_scraper.wrangle_all_unknown_work_tags()

    wrangle_scraper.close_connection()
