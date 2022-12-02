# -*- coding: utf-8 -*-
from configparser import ConfigParser
import multiprocessing
import queue
import sys
import time

from scraper.AO3Scraper import AO3Scraper

# Globals - put these in a class later!
ao3_lists = {'work_row_list', 'author_row_list', 'fandom_row_list', 'archive_warning_row_list', 'other_tag_row_list',
             'series_row_list', 'ao3_char_row_list'}
global_dict = {}


def process_queue_data(origin_tag, row_list):
    print('processing queue data ' + origin_tag + '...')
    if origin_tag not in global_dict:
        print('setting ' + origin_tag)
        global_dict[origin_tag] = row_list
        print('new length: ' + str(len(global_dict[origin_tag])))
    else:
        print('extending ' + origin_tag)
        global_dict[origin_tag].extend(row_list)
        print('new length: ' + str(len(global_dict[origin_tag])))


if __name__ == '__main__':
    sys.setrecursionlimit(5000)  # Be careful not to segfault...
    print('system recursion depth is...')
    print(sys.getrecursionlimit())  # 1000 is default... but this is dying for some reason

    config = ConfigParser.RawConfigParser()
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
    print('queue joined')
