import logging


from scrapers.ao3.utils_requests import read_credentials
from scrapers.ao3.work_tag_scraper import AO3PopularTagScraper

if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.INFO,  # Switch to logging.INFO for less output
                        format="%(levelname)s - %(message)s")

    # Read the user's credentials
    username, password = read_credentials()

    # Use said credentials...
    wrangle_scraper = AO3PopularTagScraper(username=username, password=password)

    # Wrangle all work tags known to not be wrangled yet
    wrangle_scraper.wrangle_top_200_work_tags()

    wrangle_scraper.close_connection()

    logging.info('Done adding top 200 most popular tags and their wrangled aliases to the db.')
    logging.info('ficscraper successfully finished running.')