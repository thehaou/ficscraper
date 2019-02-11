# -*- coding: utf-8 -*-
import ConfigParser
import Queue
import multiprocessing
import sys
import time

from postgresql.PostgresqlConnector import PostgresqlConnector
from scraper.AO3Scraper import AO3Scraper

from scraper.FFNDesktopScraper import FFNDesktopScraper
from scraper.FFNMobileScraper import FFNMobileScraper

# Globals - put these in a class later!
ffn_lists = {'work_row_list', 'author_row_list', 'fandom_row_list', 'ffn_genre_row_list', 'ffn_char_row_list'}
ao3_lists = {'work_row_list', 'author_row_list', 'fandom_row_list', 'archive_warning_row_list', 'other_tag_row_list',
             'series_row_list', 'ao3_char_row_list'}
global_dict = {}


def process_queue_data((origin_tag, row_list)):
    print 'processing queue data ' + origin_tag + '...'
    if origin_tag not in global_dict:
        print 'setting ' + origin_tag
        global_dict[origin_tag] = row_list
        print 'new length: ' + str(len(global_dict[origin_tag]))
    else:
        print 'extending ' + origin_tag
        global_dict[origin_tag].extend(row_list)
        print 'new length: ' + str(len(global_dict[origin_tag]))


def cross_reference_ffn():
    # update() is mutating
    for list_name in ffn_lists:
        union_set = global_dict.get('desktop ' + list_name).union(global_dict.get('mobile ' + list_name)
                                                                  .difference(global_dict.get('desktop ' + list_name)))
        print 'new union set of ' + list_name + ' has ' + str(len(union_set)) + ' entries'
        del global_dict['desktop ' + list_name]
        del global_dict['mobile ' + list_name]

        if list_name not in global_dict:
            global_dict[list_name] = union_set
        else:
            print 'extending ' + list_name
            global_dict[list_name].extend(list(union_set))
            print 'new length: ' + str(len(global_dict[list_name]))


if __name__ == '__main__':
    sys.setrecursionlimit(5000)  # Be careful not to segfault...
    print 'system recursion depth is...'
    print sys.getrecursionlimit()  # 1000 is default... but this is dying for some reason

    config = ConfigParser.RawConfigParser()
    config.read('SETUP.INI')

    # set up multiprocessing queue
    q = multiprocessing.Queue()

    # ao3
    username = config.get('ao3', 'username')
    password = config.get('ao3', 'password')
    ao3_scraper = AO3Scraper(username, password, q)

    # fanfiction.net
    user_html_link = config.get('ffn', 'user_html_link')
    user_html_mobile_link = config.get('ffn', 'user_html_mobile_link')
    ffn_desktop_scraper = FFNDesktopScraper(user_html_link, q)
    ffn_mobile_scraper = FFNMobileScraper(user_html_mobile_link, q)

    # postgresql
    hostname = config.get('database', 'hostname')
    username = config.get('database', 'username')
    password = config.get('database', 'password')
    database = config.get('database', 'database')
    db_connector = PostgresqlConnector(hostname, username, password, database)

    # create processes
    # , args=(user_html_mobile_link, q)
    ao3 = multiprocessing.Process(target=ao3_scraper.process_bookmarks)
    ffn_desktop = multiprocessing.Process(target=ffn_desktop_scraper.process_fanfiction_dot_net_desktop)
    ffn_mobile = multiprocessing.Process(target=ffn_mobile_scraper.process_fanfiction_dot_net_mobile)

    liveprocs = [ao3, ffn_desktop, ffn_mobile]

    ao3.start()
    ffn_desktop.start()
    ffn_mobile.start()

    # try pulling
    while liveprocs:
        try:
            while 1:
                process_queue_data(q.get(False))
        except Queue.Empty:
            pass

        time.sleep(0.5)  # Give tasks a chance to put more data in
        if not q.empty():
            continue
        liveprocs = [p for p in liveprocs if p.is_alive()]

    ao3.join()
    ffn_desktop.join()
    ffn_mobile.join()

    # No guarantee about which one finishes first
    print 'queue joined'

    # Now cross-reference works with the same work_id; choose desktop over mobile
    cross_reference_ffn()

    # TODO: check for dupes across ffn & ao3

    # db_connector.processPostgresql(ao3_lists, global_dict)
    db_connector.processPostgresql(ffn_lists.union(ao3_lists), global_dict)
