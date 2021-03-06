import inspect
import itertools
import re
import sys
import traceback
from datetime import datetime

import requests
import pickle
from time import strptime
from time import mktime
from bs4 import BeautifulSoup
from enum import Enum

from postgresql.AO3OtherTagRow import AO3OtherTagRow
from postgresql.AO3SeriesRow import AO3SeriesRow
from postgresql.AO3WarningRow import AO3WarningRow
from postgresql.AuthorRow import AuthorRow
from postgresql.CharacterRow import CharacterRow
from postgresql.FandomRow import FandomRow
from postgresql.WorkRow import WorkRow


class ArchiveWarning(Enum):
    # First, the audience rating (upper left square)
    NR = 'Not Rated'
    G = 'General Audiences'
    T = 'Teen And Up Audiences'
    M = 'Mature'
    E = 'Explicit'

    # Next, archive warnings (bottom left square)
    CCNTUAW = 'Choose Not To Use Archive Warnings'
    NAWA = 'No Archive Warnings Apply'
    GDOV = 'Graphic Depictions Of Violence'
    MCD = 'Major Character Death'
    RNC = 'Rape/Non-Con'
    U = 'Underage'

    # Then relationship types (upper right square)
    GEN = 'Gen'
    MM = 'M/M'
    FF = 'F/F'
    FM = 'F/M'
    MULTI = 'Multi'
    OTHER = 'Other'
    NC = 'No category'

    # And finally, completion status (bottom right square)
    CW = 'Complete Work'
    SIP = 'Series in Progress'
    WIP = 'Work in Progress'

    @classmethod
    def get_name_from_value(cls, value):
        for item in cls:
            if value == item.value:
                return item
        return None


def get_quadrant(enum_set):
    audience_rating = {ArchiveWarning.NR, ArchiveWarning.G, ArchiveWarning.T, ArchiveWarning.M, ArchiveWarning.E}
    content_rating = {ArchiveWarning.CCNTUAW, ArchiveWarning.NAWA, ArchiveWarning.GDOV, ArchiveWarning.MCD,
                      ArchiveWarning.RNC, ArchiveWarning.U}
    relationship_type = {ArchiveWarning.GEN, ArchiveWarning.MM, ArchiveWarning.FF, ArchiveWarning.FM,
                         ArchiveWarning.MULTI, ArchiveWarning.OTHER, ArchiveWarning.NC}
    completion_status = {ArchiveWarning.CW, ArchiveWarning.SIP, ArchiveWarning.WIP}

    ar = audience_rating.intersection(enum_set)
    cr = content_rating.intersection(enum_set)
    rt = relationship_type.intersection(enum_set)
    cs = completion_status.intersection(enum_set)

    if len(ar) != 1 or len(cs) != 1:
        error_and_quit('need exactly one of each of these quadrants', enum_set)

    # There can be multiple here, for example, 'Gen, Multi' is a valid text
    if len(cr) == 0 or len(rt) == 0:
        error_and_quit('need at least one of each of these quadrants', enum_set)

    is_complete = False
    if cs.pop() is ArchiveWarning.CW:
        is_complete = True

    # Special case: if the audience warning is 'Not Rated', this is basically null
    ar_popped = ar.pop()
    if ar_popped is ArchiveWarning.NR:
        ar_popped = None

    return ar_popped, list(set(cr)), list(set(rt)), is_complete


def error_and_quit(error_msg, input_string):
    print error_msg
    print input_string
    exit(-1)


class AO3Scraper:
    def __init__(self, username, password, queue):
        self._log_prefix = 'ao3 '
        self._username = username
        self._password = password
        self._queue = queue
        self._bookmarks_url_template = 'https://archiveofourown.org/users/%s/bookmarks?page=%%d'
        self._works_subscriptions_url_template = 'https://archiveofourown.org/users/%s/subscriptions?type=works'
        self._series_subscriptions_url_template = 'https://archiveofourown.org/users/%s/subscriptions?type=series'
        self._homepage_url = 'https://archiveofourown.org'
        self._login_url = 'https://archiveofourown.org/users/login'


        # set up active session for ao3 - this section is based off of
        # https://github.com/alexwlchan/ao3/blob/master/src/ao3/users.py
        sess = requests.Session()
        req = sess.get(self._homepage_url)
        soup = BeautifulSoup(req.text, features='html.parser')

        authenticity_token = soup.find('input', {'name': 'authenticity_token'})['value']
        print 'auth token is ' + str(authenticity_token)

        req = sess.post(self._login_url, params={
            'authenticity_token': authenticity_token, # csrf token
            'user[login]': self._username,
            'user[password]': self._password,
            'commit': 'Log in'
        })

        if 'Please try again' in req.text:
            raise RuntimeError(
                'Error logging in to AO3; is your password correct?')

        self._sess = sess
        print 'session set up'

    # Also from # https://github.com/alexwlchan/ao3/blob/master/src/ao3/users.py
    def __repr__(self):
        return '%s(username=%r)' % (type(self).__name__, self.username)

    def grab_pages(self):
        # Happily AO3 starts returning blank results if you exceed the max page
        api_url = (self._bookmarks_url_template % self._username)

        pages = []
        for page_num in itertools.count(start=1):
            print self._log_prefix + 'searching on page ' + str(page_num)

            req = self._sess.get(api_url % page_num)
            soup = BeautifulSoup(req.text, features='html.parser')

            ol_tag = soup.find('ol', class_='bookmark index group')

            li_tags = ol_tag.findAll('li', class_='bookmark blurb group')
            if len(li_tags) > 0:
                pages.append(ol_tag)
            else:
                print 'no more bookmarks found, stopping'
                break
        return pages

    def process_bookmarks(self):
        print self._log_prefix + 'Starting AO3'

        QUEUE_MAX = 50

        website = 'Archive of Our Own'
        print '\n'
        print '/ ~~~~~~~~~~~~~~~~~~~~~~~ \\'
        print '|      ArchiveOfOurOwn     |'
        print '\\ ~~~~~~~~~~~~~~~~~~~~~~~ /'

        pages = self.grab_pages()
        page_num = 1
        for ol_tag in pages:
            # Bookkeeping
            print self._log_prefix + 'parsing page ' + str(page_num)
            page_num += 1

            # Set up lists
            work_row_list = []
            author_row_list = []
            fandom_row_list = []
            archive_warning_row_list = []
            other_tag_row_list = []
            series_row_list = []
            ao3_char_row_list = []

            # Scrape
            li_tags = ol_tag.findAll('li', class_='bookmark blurb group')
            for li_tag in li_tags:
                word_count, released_chapters_count, total_chapters_count = self.process_stats(li_tag)

                if word_count is None:
                    print self._log_prefix + 'This is a series bookmark, skipping'
                    continue

                work_id, title, author_id, author_name, fandoms, content_rating, archive_warnings, is_complete, \
                    update_epoch_sec = self.process_header_module(li_tag)
                if content_rating is not None:
                    content_rating = content_rating.name

                # publish isn't available in the process_header_module unfortunately, only on the individual
                # work page
                publish_epoch_sec = None

                characters, other_tags = self.process_tags(li_tag) # TOO MANY on page 3, e.g. https://archiveofourown.org/works/13111908/chapters/29997507
                # characters = None
                # other_tags = None

                series_ids, series_names = self.process_series(li_tag)
                # series_ids = None
                # series_names = None

                personal_rating = self.process_meta_tags_commas(li_tag)
                # personal_rating = None

                # Create postgresql entries
                work_row_list.append(
                    WorkRow(work_id, title, website, word_count, publish_epoch_sec, update_epoch_sec,
                            released_chapters_count,
                            total_chapters_count, personal_rating, is_complete, content_rating))

                author_row_list.append(AuthorRow(work_id, author_id, author_name))

                if fandoms is not None:
                    for fandom_name in fandoms:
                        fandom_row_list.append(FandomRow(work_id, fandom_name))

                if archive_warnings is not None:
                    for archive_warning in archive_warnings:
                        archive_warning_row_list.append(AO3WarningRow(work_id, archive_warning.value))

                if other_tags is not None:
                    for other_tag in other_tags:
                        other_tag_row_list.append(AO3OtherTagRow(work_id, other_tag))

                if series_ids is not None:
                    for series_id, series_name in zip(series_ids, series_names):
                        series_row_list.append(AO3SeriesRow(work_id, series_id, series_name))

                if characters is not None:
                    for character_name in characters:
                        ao3_char_row_list.append(CharacterRow(work_id, character_name))

            # Dump them on the queue, per page
            if len(work_row_list) > 0:
                print str(page_num) + ' putting ' + str(len(work_row_list)) + ' works on the queue'
                self._queue.put(('work_row_list', work_row_list))
            if len(author_row_list) > 0:
                print str(page_num) + ' putting ' + str(len(work_row_list)) + ' authors on the queue'
                self._queue.put(('author_row_list', author_row_list))
            if len(fandom_row_list) > 0:
                print str(page_num) + ' putting ' + str(len(work_row_list)) + ' fandoms on the queue'
                self._queue.put(('fandom_row_list', fandom_row_list))
            if len(archive_warning_row_list) > 0:
                print str(page_num) + ' putting ' + str(len(work_row_list)) + ' archive warnings on the queue'
                self._queue.put(('archive_warning_row_list', archive_warning_row_list))
            if len(other_tag_row_list) > 0:
                print str(page_num) + ' putting ' + str(len(work_row_list)) + ' other tags on the queue'
                self._queue.put(('other_tag_row_list', other_tag_row_list))
            if len(series_row_list) > 0:
                print str(page_num) + ' putting ' + str(len(work_row_list)) + ' series on the queue'
                self._queue.put(('series_row_list', series_row_list))
            if len(ao3_char_row_list) > 0:
                print str(page_num) + ' putting ' + str(len(work_row_list)) + ' characters on the queue'
                self._queue.put(('ao3_char_row_list', ao3_char_row_list))
        print self._log_prefix + 'Exiting AO3'

    def process_header_module(self, bookmark):
        # print 'processing header module'
        header_module = bookmark.find('div', class_='header module')
        if header_module is None:
            error_and_quit(self._log_prefix + 'can\'t find header module class', bookmark)

        work_id, title, author_id, author_name = self.process_heading(header_module)
        fandoms = self.process_fandoms_heading(header_module)
        content_rating, archive_warnings, relationship_types, is_complete = self.process_required_tags(header_module)
        update_epoch_sec = self.process_datetime(header_module)

        return work_id, title, author_id, author_name, fandoms, content_rating, archive_warnings, is_complete, \
               update_epoch_sec

    def process_heading(self, header_module):
        # print 'processing process_heading module'
        heading = header_module.find('h4', class_='heading')
        if heading is None:
            error_and_quit(self._log_prefix + 'can\'t find heading class', header_module)

        for a_child in heading.findAll('a'):
            if a_child.get('rel') is not None:
                # Grab author info
                author_id = a_child.get('href').split('/')[2]
                author_name = a_child.contents[0]
                if author_id is None or author_name is None:
                    error_and_quit(self._log_prefix + 'can\'t parse author info', a_child)

            else:
                # Grab work info - however, works can be written for other people, we need to ignore hrefs with /users
                prefix = a_child.get('href')[1:6]
                if prefix == 'works':
                    work_id = a_child.get('href')[7:]
                    title = a_child.contents[0]
                    if work_id is None or title is None:
                        error_and_quit(self._log_prefix + 'can\'t parse title info', a_child)


        return work_id, title, author_id, author_name

    def process_fandoms_heading(self, header_module):
        # print 'processing process_fandoms_heading module'
        fandoms_heading = header_module.find('h5', class_='fandoms heading')
        if fandoms_heading is None:
            error_and_quit(self._log_prefix + 'can\'t find fandoms heading class', header_module)

        fandoms = []
        for a_child in fandoms_heading.findAll('a'):
            fandom_name = a_child.contents[0]
            if fandom_name is None:
                error_and_quit(self._log_prefix + 'can\'t parse fandom tag', header_module)
            fandoms.append(fandom_name)

        return fandoms

    def process_required_tags(self, header_module):
        # print 'processing process_required_tags module'
        found_tags = set()
        required_tags = header_module.find('ul', class_='required-tags')
        if required_tags is None:
            error_and_quit(self._log_prefix + 'can\'t find required tags class', header_module)
            
        for tag in required_tags.findAll('span', class_='text'):
            tag_content_list = tag.contents[0].split(', ')
            for tag_content in tag_content_list:
                archive_warning_enum = ArchiveWarning.get_name_from_value(tag_content)
                found_tags.add(archive_warning_enum)

        return get_quadrant(found_tags)

    def process_datetime(self, header_module):
        """
        Format is DD Month YYYY
        ArchiveOfOurOwn posts are suffixed with -0400 so I'm going to assume AO3 is UTC-4, which is EST.
        Regardless we're not given an hour or minute to go by, so we'll just call the day posted the UTC day too.
        :param header_module:
        :return:
        """
        # print 'processing process_datetime module'
        datetime_child = header_module.find('p', class_='datetime')
        if datetime_child is None:
            error_and_quit(self._log_prefix + 'can\'t find datetime class', header_module)

        dd_Month_YYYY = datetime_child.contents[0]
        struct_time = strptime(dd_Month_YYYY, "%d %b %Y")
        return mktime(struct_time) - mktime(datetime(1970, 1, 1).timetuple())

    def process_tags(self, header_module):
        # print 'processing process_tags module'
        tags = header_module.find('ul', class_='tags commas')
        if tags is None:
            error_and_quit('couldn\'t find tags... actually this is plausible if there are NO tags, but...', header_module)

        characters = tags.find('li', class_='characters')
        character_list = None
        if characters is not None:
            character_list = []
            for character_child in characters.findAll('a'):
                character_list.append(character_child.contents[0])

        other_tags = tags.find('li', class_='freeforms')
        other_tags_list = None
        # other_tag_last = tags.find('li', class_='freeforms last') # TODO should probably figure out if this is getting parsed or not
        if other_tags is not None:
            other_tags_list = []
            for other_tag in other_tags:
                other_tags_list.append(other_tag.contents[0])

        return character_list, other_tags_list

    def process_series(self, bookmark):
        # print 'processing process_series module'
        datetime_child = bookmark.find('ul', class_='series')
        if datetime_child is None:
            print 'Not a series, skipping process_series'
            return None, None

        series_ids = []
        series_names = []
        for a_child in datetime_child.findAll('a'):
            series_ids.append(a_child.get('href')[8:])
            series_names.append(a_child.contents[0])

        return series_ids, series_names

    def process_stats(self, bookmark):
        # print 'processing process_stats module'
        stats = bookmark.find('dl', class_='stats')
        if stats is None:
            print self._log_prefix + 'This bookmark has probably been deleted, skipping it. Bookmark:'
            print bookmark
            return None, None, None

        word_count_child = stats.find('dd', class_='words')
        if word_count_child is None:
            # USUALLY word count has the class assigned to it, but then sometimes you get weird works like
            # https://archiveofourown.org/series/889014 which show up on bookmarks with no classes on their dd tags
            print self._log_prefix + 'This bookmark is probably a series, skipping it. Bookmark:'
            print bookmark
            return None, None, None
        word_count = re.sub(',', '', word_count_child.contents[0])

        chapters_count_child = stats.find('dd', class_='chapters')
        if chapters_count_child is None:
            error_and_quit('couldn\'t find chapter count')
        chapters_split = chapters_count_child.contents[0].split('/')
        released_chapters_count = chapters_split[0]
        total_chapters_count = None
        if chapters_split[1] != '?':
            total_chapters_count = chapters_split[1]

        return word_count, released_chapters_count, total_chapters_count

    def process_meta_tags_commas(self, bookmark):
        # print 'processing process_meta_tags_commas module'
        meta_tags_commas = bookmark.find('ul', class_='meta tags commas')
        if meta_tags_commas is None:
            print 'can\'t find any user bookmarks, skipping process_meta_tags_commas'
            return None

        # TODO - support multiple tags properly
        for a_child in meta_tags_commas.findAll('a'):
            return a_child.contents[0]
