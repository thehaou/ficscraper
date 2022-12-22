import logging
from time import sleep

import requests
from bs4 import BeautifulSoup

from scrapers.ao3 import constants


def setup_ao3_session(username, password):
    # Set up active session for AO3. This section is based off of
    # https://github.com/alexwlchan/ao3/blob/master/src/ao3/users.py
    logging.info('Setting up an active session with AO3...')
    sess = requests.Session()
    req = sess.get(constants.homepage_url)
    soup = BeautifulSoup(req.text, features='html.parser')
    sleep(1.5)  # Try to avoid triggering rate limiting

    authenticity_token = soup.find('input', {'name': 'authenticity_token'})['value']

    req = sess.post(constants.login_url, params={
        'authenticity_token': authenticity_token,  # csrf token
        'user[login]': username,
        'user[password]': password,
        'commit': 'Log in'
    })

    if 'Please try again' in req.text:
        raise RuntimeError(
            'Error logging in to AO3; is your password correct?')

    logging.info('AO3 session set up')
    return sess


def get_req(session, url, retry_num_min=3, extra_info=None):
    count_503 = 0
    while True:
        req = session.get(url)
        sleep(1.5)  # Try to avoid triggering rate limiting

        if req.status_code == 429:
            # https://otwarchive.atlassian.net/browse/AO3-5761
            logging.error("\nAO3 rate limits; we will receive 429 \"Too Many Requests\" if we ask for pages "
                          "too often. We need to wait for several minutes, sorry!")
            extra_info = "; in the middle of trying to process {}".format(extra_info) if extra_info else '...'
            logging.info("Sleeping for 3 min{}"
                         .format(extra_info))
            sleep(60 * retry_num_min)
            continue
        elif req.status_code == 503:
            # Usually this means AO3 is overloaded, but it could also mean maintenance. AO3 usually returns:
            #   Error 503
            #   The page was responding too slowly.
            #   There are so many people using the archive right now, we can't show your page.
            #   Follow <a href="https://twitter.com/ao3_status/">@AO3_Status</a> on Twitter for updates
            #   if this keeps happening.
            # If we hit 503 multiple times in a row, then we should abandon fic-scraping efforts.
            count_503 += 1
            logging.error("Hit 503 {} time(s). AO3 is overloaded OR the site is under maintenance."
                          .format(count_503))
            logging.info("Sleeping for 1 min")
            sleep(60 * 1)

            if count_503 == 5:
                logging.error('ficscraper has hit 503 too many times in a row. Abandoning efforts.')
                logging.error('Please check what\'s wrong with AO3 at https://twitter.com/ao3_status/.')
                raise Exception("Hit 503 5 times")
        else:
            break
    return req
