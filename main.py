# -*- coding: utf-8 -*-
import ConfigParser
import Queue
import multiprocessing
import time

from postgresql.PostgresqlConnector import PostgresqlConnector
from scraper.AO3Scraper import AO3Scraper

from scraper.FFNDesktopScraper import FFNDesktopScraper
from scraper.FFNMobileScraper import FFNMobileScraper

# Globals - put these in a class later!
ffn_lists = ['work_row_list', 'author_row_list', 'fandom_row_list', 'ffn_genre_row_list', 'ffn_char_row_list']
ao3_lists = []
global_dict = {}


def process_queue_data((origin_tag, row_list)):
    print 'processing queue data ' + origin_tag + '...'
    global_dict[origin_tag] = row_list


def cross_reference_ffn():
    # update() is mutating
    for list_name in ffn_lists:
        union_set = global_dict.get('desktop ' + list_name).union(global_dict.get('mobile ' + list_name)
                                                                  .difference(global_dict.get('desktop ' + list_name)))
        print 'new union set of ' + list_name + ' has ' + str(len(union_set)) + ' entries'
        global_dict[list_name] = union_set


if __name__ == '__main__':
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
    # ffn_desktop = multiprocessing.Process(target=ffn_desktop_scraper.process_fanfiction_dot_net_desktop)
    # ffn_mobile = multiprocessing.Process(target=ffn_mobile_scraper.process_fanfiction_dot_net_mobile)

    liveprocs = [ao3]#, ffn_desktop, ffn_mobile]

    ao3.start()
    # ffn_desktop.start()
    # ffn_mobile.start()

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
    # ffn_desktop.join()
    # ffn_mobile.join()

    # No guarantee about which one finishes first
    print 'queue joined'

    # Now cross-reference works with the same work_id; choose desktop over mobile
    # cross_reference_ffn()

    # TODO: check for dupes across ffn & ao3

    # db_connector.processPostgresql(ffn_lists + ao3_lists, global_dict)
