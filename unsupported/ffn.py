"""
FFN not supported right now because it's honestly a mess tagging-system wise, and I don't want to deal with
trying to figure out which AO3 fic is actually an imported FFN fic. Let's make this ficscraper work beautifully
for AO3 first before even thinking about supporting FFN.
-sorcrane 12/1/2022
"""
from configparser import ConfigParser
import multiprocessing
import queue
import time

from scraper.FFNDesktopScraper import FFNDesktopScraper
from scraper.FFNMobileScraper import FFNMobileScraper

# Globals - put these in a class later!
ffn_lists = {'work_row_list', 'author_row_list', 'fandom_row_list', 'ffn_genre_row_list', 'ffn_char_row_list'}
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


def cross_reference_ffn():
    # update() is mutating
    for list_name in ffn_lists:
        union_set = global_dict.get('desktop ' + list_name).union(global_dict.get('mobile ' + list_name)
                                                                  .difference(global_dict.get('desktop ' + list_name)))
        print('new union set of ' + list_name + ' has ' + str(len(union_set)) + ' entries')
        del global_dict['desktop ' + list_name]
        del global_dict['mobile ' + list_name]

        if list_name not in global_dict:
            global_dict[list_name] = union_set
        else:
            print('extending ' + list_name)
            global_dict[list_name].extend(list(union_set))
            print('new length: ' + str(len(global_dict[list_name])))


if __name__ == '__main__':
    config = ConfigParser.RawConfigParser()
    config.read('SETUP.INI')

    # set up multiprocessing queue
    q = multiprocessing.Queue()

    # fanfiction.net
    user_html_link = config.get('ffn', 'user_html_link')
    user_html_mobile_link = config.get('ffn', 'user_html_mobile_link')
    ffn_desktop_scraper = FFNDesktopScraper(user_html_link, q)
    ffn_mobile_scraper = FFNMobileScraper(user_html_mobile_link, q)

    # create processes
    ffn_desktop = multiprocessing.Process(target=ffn_desktop_scraper.process_fanfiction_dot_net_desktop)
    ffn_mobile = multiprocessing.Process(target=ffn_mobile_scraper.process_fanfiction_dot_net_mobile)

    liveprocs = [ffn_desktop, ffn_mobile]

    ffn_desktop.start()
    ffn_mobile.start()

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

    ffn_desktop.join()
    ffn_mobile.join()

    # No guarantee about which one finishes first
    print('queue joined')

    # Now cross-reference works with the same work_id; choose desktop over mobile
    cross_reference_ffn()

    # TODO: check for dupes across ffn & ao3