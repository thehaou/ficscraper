import itertools
import json
import re
from datetime import datetime
import logging

import requests
from time import strptime
from time import mktime
from time import sleep
from bs4 import BeautifulSoup

from scrapers.ao3.utils_archive_warnings import get_quadrant, ArchiveWarning
import scrapers.ao3.constants as constants
from scrapers.ao3.utils_progress_bar import log_progress_bar


def error_and_quit(error_msg, input_string=""):
    logging.error(error_msg)
    logging.error(input_string)
    exit(-1)


class AO3BookmarkScraper:
    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._bookmarks_url_template = constants.bookmarks_url_template
        self._works_subscriptions_url_template = constants.works_subscriptions_url_template
        self._series_subscriptions_url_template = constants.series_subscriptions_url_template
        self._homepage_url = constants.homepage_url
        self._login_url = constants.login_url

        # Set up active session for AO3. This section is based off of
        # https://github.com/alexwlchan/ao3/blob/master/src/ao3/users.py
        logging.info('Setting up an active session with AO3...')
        sess = requests.Session()
        req = sess.get(self._homepage_url)
        soup = BeautifulSoup(req.text, features='html.parser')
        sleep(1.5)  # Try to avoid triggering rate limiting

        authenticity_token = soup.find('input', {'name': 'authenticity_token'})['value']

        req = sess.post(self._login_url, params={
            'authenticity_token': authenticity_token,  # csrf token
            'user[login]': self._username,
            'user[password]': self._password,
            'commit': 'Log in'
        })

        if 'Please try again' in req.text:
            raise RuntimeError(
                'Error logging in to AO3; is your password correct?')

        self._sess = sess
        logging.info('AO3 session set up')

    def __repr__(self):
        # This line is directly from # https://github.com/alexwlchan/ao3/blob/master/src/ao3/users.py
        return '%s(username=%r)' % (type(self).__name__, self._username)

    def grab_pages(self):
        logging.info('Figuring out how many pages to scrape.\n'
                     '\tAO3 rate-limits roughly ~25 bookmark page-fetches per ~10 minutes.\n'
                     '\tIf you have a lot of bookmarks, this may take a while. For example:\n'
                     '\n'
                     '\t200 pages of bookmarks\n'
                     '\t= (200pgs) * (10min/25pgs)\n'
                     '\t= at least 80min\n'
                     '\n'
                     '\tYou may need to change your computer sleep settings so it doesn\'t\n'
                     '\tfall asleep while ficscraper is working.\n')
        # Happily AO3 starts returning blank results if you exceed the max page
        api_url = (self._bookmarks_url_template % self._username)

        # UNCOMMENT FOR TESTING: only fetch n number of patches (I have 100+, which isn't feasible for quick testing)
        # page_count_limit = 2
        # END UNCOMMENT SECTION

        pages = []
        try:
            for page_num in itertools.count(start=1):
                # UNCOMMENT FOR TESTING
                # page_count_limit -= 1
                # if page_count_limit == -1:
                #     break
                # END UNCOMMENT SECTION

                logging.info('Searching page {} for content'.format(page_num))

                count_503 = 0
                while True:
                    req = self._sess.get(api_url % page_num)
                    sleep(1.5)  # Try to avoid triggering rate limiting

                    if req.status_code == 429:
                        # https://otwarchive.atlassian.net/browse/AO3-5761
                        logging.error("AO3 rate limits; we will receive 429 \"Too Many Requests\" if we ask for pages "
                                      "too often.\nWe need to wait for several minutes, sorry!")
                        logging.info("Sleeping for 3 min")
                        sleep(60 * 3)
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
                            exit(-1)
                    else:
                        break

                soup = BeautifulSoup(req.text, features='html.parser')

                ol_tag = soup.find('ol', class_='bookmark index group')
                if not ol_tag:
                    logging.error("Could not find bookmark index group on soup; something is seriously wrong. soup:")
                    logging.error(soup)
                    logging.error("Skipping this page...")
                    continue

                li_tags = ol_tag.findAll('li', attrs={'class': re.compile('^bookmark blurb group.*')})
                if len(li_tags) > 0:
                    pages.append(ol_tag)
                else:
                    logging.info('No more bookmarks found, stopping page-grabbing')
                    break
        except Exception as e:
            logging.error('ficscraper ran into an error while doing preliminary page fetching. '
                          '(Your computer probably fell asleep.) '
                          '\nFicscraper will try to run against the pages it was able to successfully collect.')
            logging.error(e)
        return pages

    def process_bookmarks(self):
        """
        Processes all entries on https://archiveofourown.org/users/<user_id>/bookmarks.
        TODO: does NOT handle series bookmarks (yet). Those are skipped.

        :return: (1) dictionary of further specific kinds of dictionaries (i.e. user tags, work info, authors)
                 (2) single list (JSON) of the complete bookmark history
        """
        logging.info('Starting AO3 bookmark-scraping process')

        website = 'Archive of Our Own'
        logging.info('\n')
        logging.info('/ ~~~~~~~~~~~~~~~~~~~~~~~ \\')
        logging.info('|      ArchiveOfOurOwn     |')
        logging.info('\\ ~~~~~~~~~~~~~~~~~~~~~~~ /')
        logging.info(' |     DO NOT USE AO3     |')
        logging.info(' |   WHILE THIS PROGRAM   |')
        logging.info(' |       IS RUNNING       |')
        logging.info(' \\------------------------/')

        # Grab the bs4 of as many pages as we can
        pages = self.grab_pages()
        num_pages = len(pages)

        logging.info('\n')
        logging.info('/ ~~~~~~~~~~~~~~~~~~~~~~~ \\')
        logging.info('|      ArchiveOfOurOwn     |')
        logging.info('\\ ~~~~~~~~~~~~~~~~~~~~~~~ /')
        logging.info(' |  You may now use AO3.  |')
        logging.info(' |     ficscraper will    |')
        logging.info(' |    continue to work    |')
        logging.info(' |   in the background.   |')
        logging.info(' \\------------------------/')

        # Initialize scraping variables
        logging.info('Beginning to scrape each collected page. This scraping process does not include wrangling tags, '
                     'so it will finish relatively quickly. See ficscraper\'s "wrangle" process '
                     '(./ficscraper_cli.sh --wrangle) for more info on how to automatically wrangle these collected tags.')
        page_num = 1
        total_work_row_list = []
        total_author_row_list = []
        total_fandom_row_list = []
        total_archive_warning_row_list = []
        total_addn_tag_row_list = []
        total_user_tag_row_list = []
        total_series_row_list = []
        total_ao3_char_row_list = []
        bookmarks_json_list = []
        for ol_tag in pages:
            # Bookkeeping
            log_progress_bar(prefix='Scraping page {}/{}:'.format(page_num, num_pages),
                             current=page_num,
                             length=num_pages)
            page_num += 1

            # Set up lists
            work_row_list = []
            author_row_list = []
            fandom_row_list = []
            archive_warning_row_list = []
            addn_tag_row_list = []
            user_tag_row_list = []
            series_row_list = []
            char_row_list = []

            # Scrape
            li_tags = ol_tag.findAll('li', attrs={'class': re.compile('^bookmark blurb group.*')})
            for li_tag in li_tags:
                word_count, released_chapters_count, total_chapters_count = self.process_stats(li_tag)

                if word_count is None:
                    logging.debug('This is a series bookmark, skipping')
                    continue

                work_id, title, author_id, author_name, fandoms, content_rating, archive_warnings, is_complete, \
                    update_epoch_sec = self.process_header_module(li_tag)
                if content_rating is not None:
                    content_rating = content_rating.name

                # publish_epoch_sec sadly isn't available in the process_header_module, only on the individual work page
                publish_epoch_sec = None

                # Work tags require a separate network call to wrangle them
                # (ex "no beta we die like men" --> "Not Beta Read"). To keep scraping down to a reasonable amount of
                # processing time, tag wrangling is a completely separate process. (See ./ficscraper_cli.sh --wrangle)
                characters, addn_tags = self.process_tags(li_tag)

                series_ids, series_names = self.process_series(li_tag)

                date_bookmarked, user_tags = self.process_user_bookmark(li_tag)

                # Create (singular) JSON entry
                series_json = [{"series_id": series_id, "series_name": series_name}
                               for series_id, series_name in zip(series_ids, series_names)] if series_ids else []
                bookmarks_json_list.append(
                    {
                        "work_id": work_id,
                        "title": title,
                        "author_id": author_id,
                        "author_name": author_name,
                        "word_count": word_count,
                        "publish_epoch_sec": publish_epoch_sec,
                        "update_epoch_sec": update_epoch_sec,
                        "released_chapters_count": released_chapters_count,
                        "total_chapters_count": total_chapters_count,
                        "is_complete": is_complete,
                        "content_rating": content_rating,
                        "archive_warnings": [archive_warning.value for archive_warning in archive_warnings],
                        "fandoms": [fandom for fandom in fandoms],
                        "series": series_json,
                        "characters": [character for character in characters],
                        "additional_tags": [tag for tag in addn_tags],
                        "user_tags": [tag for tag in user_tags],
                        "date_bookmarked": date_bookmarked,
                    }
                )

                # Create CSV entries
                work_row_list.append(
                    {
                        "work_id": work_id,
                        "title": title,
                        # "website": website,
                        "word_count": word_count,
                        "publish_epoch_sec": publish_epoch_sec,
                        "update_epoch_sec": update_epoch_sec,
                        "released_chapters_count": released_chapters_count,
                        "total_chapters_count": total_chapters_count,
                        "is_complete": is_complete,
                        "content_rating": content_rating,
                        "date_bookmarked": date_bookmarked
                    })

                author_row_list.append({
                    "work_id": work_id,
                    "author_id": author_id,
                    "author_name": author_name
                })

                if fandoms is not None:
                    for fandom_name in fandoms:
                        fandom_row_list.append({
                            "work_id": work_id,
                            "fandom_name": fandom_name
                        })

                if archive_warnings is not None:
                    for archive_warning in archive_warnings:
                        archive_warning_row_list.append({
                            "work_id": work_id,
                            "warning": archive_warning.value
                        })

                if addn_tags is not None:
                    for addn_tag in addn_tags:
                        addn_tag_row_list.append({
                            "work_id": work_id,
                            "work_tag_id": addn_tag
                        })

                if user_tags is not None:
                    for user_tag in user_tags:
                        user_tag_row_list.append({
                            "work_id": work_id,
                            "user_tag": user_tag
                        })

                if series_ids is not None:
                    for series_id, series_name in zip(series_ids, series_names):
                        series_row_list.append({
                            "work_id": work_id,
                            "series_id": series_id,
                            "series_name": series_name
                        })

                if characters is not None:
                    for character_name in characters:
                        char_row_list.append({
                            "work_id": work_id,
                            "character_name": character_name
                        })

            # Dump them on the queue, per page
            if len(work_row_list) > 0:
                logging.debug("pg{} - putting {} works on the queue".format(page_num, len(work_row_list)))
                total_work_row_list.extend(work_row_list)
            if len(author_row_list) > 0:
                logging.debug("pg{} - putting {} authors on the queue".format(page_num, len(author_row_list)))
                total_author_row_list.extend(author_row_list)
            if len(fandom_row_list) > 0:
                logging.debug("pg{} - putting {} fandoms on the queue".format(page_num, len(fandom_row_list)))
                total_fandom_row_list.extend(fandom_row_list)
            if len(archive_warning_row_list) > 0:
                logging.debug("pg{} - putting {} archive warnings on the queue".format(page_num,
                                                                                       len(archive_warning_row_list)))
                total_archive_warning_row_list.extend(archive_warning_row_list)
            if len(addn_tag_row_list) > 0:
                logging.debug("pg{} - putting {} additional tags on the queue".format(page_num, len(addn_tag_row_list)))
                total_addn_tag_row_list.extend(addn_tag_row_list)
            if len(user_tag_row_list) > 0:
                logging.debug("pg{} - putting {} user-defined bookmark tags on the queue"
                              .format(page_num, len(user_tag_row_list)))
                total_user_tag_row_list.extend(user_tag_row_list)
            if len(series_row_list) > 0:
                logging.debug("pg{} - putting {} series on the queue".format(page_num, len(series_row_list)))
                total_series_row_list.extend(series_row_list)
            if len(char_row_list) > 0:
                logging.debug("pg{} - putting {} characters on the queue".format(page_num, len(char_row_list)))
                total_ao3_char_row_list.extend(char_row_list)

        logging.info('Scraping process completed. Exiting AO3 bookmark scraper')
        fics_dict = {
            "works": total_work_row_list,
            "authors": total_author_row_list,
            "fandoms": total_fandom_row_list,
            "warnings": total_archive_warning_row_list,
            "work_tags": total_addn_tag_row_list,
            "user_tags": total_user_tag_row_list,
            "series": total_series_row_list,
            "characters": total_ao3_char_row_list
        }

        try:
            bookmarks_json = json.dumps(bookmarks_json_list)
        except Exception as e:
            logging.error('Can\'t translate bookmarks to JSON for some reason; returning raw')
            logging.error(e)
            bookmarks_json = bookmarks_json_list

        return fics_dict, bookmarks_json

    def process_header_module(self, bookmark):
        # logging.debug('processing header module')
        header_module = bookmark.find('div', class_='header module')
        if header_module is None:
            error_and_quit('can\'t find header module class', bookmark)

        work_id, title, author_id, author_name = self.process_heading(header_module)
        fandoms = self.process_fandoms_heading(header_module)
        content_rating, archive_warnings, relationship_types, is_complete = self.process_required_tags(header_module)
        update_epoch_sec = self.process_datetime(header_module)

        return work_id, title, author_id, author_name, fandoms, content_rating, archive_warnings, is_complete, \
               update_epoch_sec

    def process_heading(self, header_module):
        # logging.debug('processing process_heading module')
        heading = header_module.find('h4', class_='heading')
        if heading is None:
            error_and_quit('can\'t find heading class', header_module)

        # Some authors are listed as Anonymous, and thus, have no author profile to link to.
        # See https://archiveofourown.org/collections/anonymous for more details.
        author_name = 'Anonymous'
        author_id = 'Anonymous'

        for a_child in heading.findAll('a'):
            if a_child.get('rel') is not None:
                # Grab author info
                author_id = a_child.get('href').split('/')[2]
                author_name = a_child.contents[0]
                if author_id is None or author_name is None:
                    error_and_quit('can\'t parse author info', a_child)

            else:
                # Grab work info - however, works can be written for other people, we need to ignore hrefs with /users
                prefix = a_child.get('href')[1:6]
                if prefix == 'works':
                    work_id = a_child.get('href')[7:]
                    title = a_child.contents[0]
                    if work_id is None or title is None:
                        error_and_quit('can\'t parse title info', a_child)

        return work_id, title, author_id, author_name

    def process_fandoms_heading(self, header_module):
        # logging.debug('processing process_fandoms_heading module')
        fandoms_heading = header_module.find('h5', class_='fandoms heading')
        if fandoms_heading is None:
            error_and_quit('can\'t find fandoms heading class', header_module)

        fandoms = []
        for a_child in fandoms_heading.findAll('a'):
            fandom_name = a_child.contents[0]
            if fandom_name is None:
                error_and_quit('can\'t parse fandom tag', header_module)
            fandoms.append(fandom_name)

        return fandoms

    def process_required_tags(self, header_module):
        # logging.debug('processing process_required_tags module')
        found_tags = set()
        required_tags = header_module.find('ul', class_='required-tags')
        if required_tags is None:
            error_and_quit('can\'t find required tags class', header_module)
            
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
        # logging.debug('processing process_datetime module')
        datetime_child = header_module.find('p', class_='datetime')
        if datetime_child is None:
            error_and_quit('can\'t find datetime class', header_module)

        dd_Month_YYYY = datetime_child.contents[0]
        struct_time = strptime(dd_Month_YYYY, "%d %b %Y")
        return int(mktime(struct_time) - mktime(datetime(1970, 1, 1).timetuple()))

    def process_tags(self, header_module):
        # logging.debug('processing process_tags module')
        tags = header_module.find('ul', class_='tags commas')
        if tags is None:
            error_and_quit('couldn\'t find tags... actually this is plausible if there are NO tags, but...', header_module)

        characters_lis = tags.findAll('li', class_='characters')
        character_list = []
        if characters_lis is not None:
            for character_li in characters_lis:
                character_a = character_li.find('a')
                character_list.append(character_a.contents[0])

        other_tags = tags.findAll('li', class_='freeforms')
        other_tags_list = []
        if other_tags:
            for li_tag in other_tags:
                a_tag = li_tag.find('a')
                fun_id = a_tag.contents[0]
                other_tags_list.append(fun_id)
        return character_list, other_tags_list

    def process_series(self, bookmark):
        # logging.debug('processing process_series module')
        datetime_child = bookmark.find('ul', class_='series')
        if datetime_child is None:
            return None, None

        logging.debug('This is a series, actually going through process_series')
        """
        TODO - we don't process series correctly at all; just the name and id of the series and nothing about the 
        works in them.
        """
        series_ids = []
        series_names = []
        for a_child in datetime_child.findAll('a'):
            series_ids.append(a_child.get('href')[8:])
            series_names.append(a_child.contents[0])

        return series_ids, series_names

    def process_stats(self, bookmark):
        # logging.debug('processing process_stats module')
        stats = bookmark.find('dl', class_='stats')
        if stats is None:
            logging.debug('This bookmark has probably been deleted, skipping it. Bookmark:')
            logging.debug(bookmark)
            return None, None, None

        word_count_child = stats.find('dd', class_='words')
        if word_count_child is None:
            # USUALLY word count has the class assigned to it, but then sometimes you get weird works like
            # https://archiveofourown.org/series/889014 which show up on bookmarks with no classes on their dd tags
            logging.debug('This bookmark is probably a series, skipping it. Bookmark:')
            logging.debug(bookmark)
            return None, None, None
        word_count = re.sub(',', '', word_count_child.contents[0])

        chapters_count_child = stats.find('dd', class_='chapters')
        if chapters_count_child is None:
            error_and_quit('couldn\'t find chapter count')

        # If a chapter is 1/1, the contents will all be in one element.
        # But if a chapter has multiple, regardless of if it is finished, the released chapters # will be in an
        # a-tag, and the total chapters will be in the second contents element. :'(

        contents_first_elem = chapters_count_child.contents[0]
        if contents_first_elem.next_sibling:
            # We have a multi chapter on our hands!
            released_chapters_count = contents_first_elem.contents[0]
            total_chapters_elem = chapters_count_child.contents[1].split('/')[1]
        else:
            chapters_split = chapters_count_child.contents[0].split('/')
            released_chapters_count = chapters_split[0]
            total_chapters_elem = chapters_split[1]

        total_chapters_count = None
        if total_chapters_elem != '?':
            total_chapters_count = total_chapters_elem

        return word_count, released_chapters_count, total_chapters_count

    def process_user_bookmark(self, bookmark):
        # logging.debug('processing process_user_bookmark module')
        user_bookmark = bookmark.find('div', class_='own user module group')
        date_bookmarked = self.process_datetime(user_bookmark)

        meta_tags_commas = user_bookmark.find('ul', class_='meta tags commas')
        user_tags = []
        if meta_tags_commas:
            for a_child in meta_tags_commas.findAll('a'):
                user_tags.append(a_child.contents[0])

        return date_bookmarked, user_tags
