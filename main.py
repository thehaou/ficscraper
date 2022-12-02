# -*- coding: utf-8 -*-
import logging
import multiprocessing
import queue
import sys
import time

import configparser

from scraper.AO3Scraper import AO3Scraper

# Globals - put these in a class later!
ao3_lists = {'work_row_list', 'author_row_list', 'fandom_row_list', 'archive_warning_row_list', 'other_tag_row_list',
             'series_row_list', 'ao3_char_row_list'}
global_dict = {}

# Set up logging
logging.basicConfig(level=logging.DEBUG,  # Switch to logging.INFO for less output
                    # format=''
                    )


def process_queue_data(origin_tag, row_list):
    logging.debug('processing queue data ' + origin_tag + '...')
    if origin_tag not in global_dict:
        logging.debug('setting ' + origin_tag)
        global_dict[origin_tag] = row_list
        logging.debug('new length: ' + str(len(global_dict[origin_tag])))
    else:
        logging.debug('extending ' + origin_tag)
        global_dict[origin_tag].extend(row_list)
        logging.debug('new length: ' + str(len(global_dict[origin_tag])))


if __name__ == '__main__':
    sys.setrecursionlimit(5000)  # Be careful not to segfault...
    logging.debug('system recursion depth is...')
    logging.debug(sys.getrecursionlimit())  # 1000 is default... but this is dying for some reason

    config = configparser.ConfigParser()
    config.read('SETUP.INI')

    # set up multiprocessing queue
    q = multiprocessing.Queue()

    # ao3
    username = config.get('ao3', 'username')
    password = config.get('ao3', 'password')
    ao3_scraper = AO3Scraper(username, password, q)

    # create processes
    # , args=(user_html_mobile_link, q)
    ao3 = multiprocessing.Process(target=ao3_scraper.process_bookmarks)

    liveprocs = [ao3]

    ao3.start()

    # try pulling
    while liveprocs:
        try:
            while 1:
                process_queue_data(q.get(False))
        except queue.Empty:
            pass

        time.sleep(0.5)  # Give tasks a chance to put more data in
        if not q.empty():
            continue
        liveprocs = [p for p in liveprocs if p.is_alive()]

    ao3.join()

    # No guarantee about which one finishes first
    logging.debug('queue joined')
