import itertools
import re
from datetime import datetime
import logging

import requests
from time import strptime
from time import mktime
from time import sleep
from bs4 import BeautifulSoup

from src.scrapers.ao3.ArchiveWarningsUtils import get_quadrant, ArchiveWarning
import src.scrapers.ao3.constants as constants


def error_and_quit(error_msg, input_string=""):
    logging.error(error_msg)
    logging.error(input_string)
    exit(-1)


class AO3Scraper:
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
        sess = requests.Session()
        req = sess.get(self._homepage_url)
        soup = BeautifulSoup(req.text, features='html.parser')

        authenticity_token = soup.find('input', {'name': 'authenticity_token'})['value']
        logging.debug('auth token is ' + str(authenticity_token))

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
        logging.debug('AO3 session set up')

    def __repr__(self):
        # This line is directly from # https://github.com/alexwlchan/ao3/blob/master/src/ao3/users.py
        return '%s(username=%r)' % (type(self).__name__, self._username)

    def grab_pages(self):
        # Happily AO3 starts returning blank results if you exceed the max page
        api_url = (self._bookmarks_url_template % self._username)

        # UNCOMMENT FOR TESTING: only fetch n number of patches (I have 100+, which isn't feasible for quick testing)
        page_count_limit = 2
        # END UNCOMMENT SECTION

        pages = []
        for page_num in itertools.count(start=1):
            # UNCOMMENT FOR TESTING
            page_count_limit -= 1
            if page_count_limit == 0:
                break
            # END UNCOMMENT SECTION

            logging.info('searching on page ' + str(page_num))

            while True:
                req = self._sess.get(api_url % page_num)
                if req.status_code == 429:
                    # https://otwarchive.atlassian.net/browse/AO3-5761
                    logging.error("AO3 rate limits; we will receive 429 \"Too Many Requests\" if we ask for pages "
                                  "too often. We need to wait for several minutes, sorry!")
                    logging.info("Sleeping for 5 min")
                    sleep(60 * 5)
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
                logging.info('no more bookmarks found, stopping')
                break
        return pages

    def process_bookmarks(self):
        logging.info('Starting AO3')

        website = 'Archive of Our Own'
        logging.info('\n')
        logging.info('/ ~~~~~~~~~~~~~~~~~~~~~~~ \\')
        logging.info('|      ArchiveOfOurOwn     |')
        logging.info('\\ ~~~~~~~~~~~~~~~~~~~~~~~ /')

        pages = self.grab_pages()
        page_num = 1
        total_work_row_list = []
        total_author_row_list = []
        total_fandom_row_list = []
        total_archive_warning_row_list = []
        total_other_tag_row_list = []
        total_series_row_list = []
        total_ao3_char_row_list = []
        for ol_tag in pages:
            # Bookkeeping
            logging.info('parsing page ' + str(page_num))
            page_num += 1

            # Set up lists
            work_row_list = []
            author_row_list = []
            fandom_row_list = []
            archive_warning_row_list = []
            other_tag_row_list = []
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

                # publish isn't available in the process_header_module unfortunately, only on the individual
                # work page
                publish_epoch_sec = None

                characters, other_tags = self.process_tags(li_tag) # TOO MANY on page 3, e.g. https://archiveofourown.org/works/13111908/chapters/29997507

                series_ids, series_names = self.process_series(li_tag)

                date_bookmarked, user_tags = self.process_user_bookmark(li_tag)

                # Create postgresql entries
                work_row_list.append(
                    {
                        "work_id": work_id,
                        "title": title,
                        "website": website,
                        "word_count": word_count,
                        "publish_epoch_sec": publish_epoch_sec,
                        "update_epoch_sec": update_epoch_sec,
                        "released_chapters_count": released_chapters_count,
                        "total_chapters_count": total_chapters_count,
                        "user_tags": user_tags,
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

                if other_tags is not None:
                    for other_tag in other_tags:
                        other_tag_row_list.append({
                            "work_id": work_id,
                            "other_tag": other_tag
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
            if len(other_tag_row_list) > 0:
                logging.debug("pg{} - putting {} other tags on the queue".format(page_num, len(other_tag_row_list)))
                total_other_tag_row_list.extend(other_tag_row_list)
            if len(series_row_list) > 0:
                logging.debug("pg{} - putting {} series on the queue".format(page_num, len(series_row_list)))
                total_series_row_list.extend(series_row_list)
            if len(char_row_list) > 0:
                logging.debug("pg{} - putting {} characters on the queue".format(page_num, len(char_row_list)))
                total_ao3_char_row_list.extend(char_row_list)
        logging.info('Exiting AO3')
        return {
            "works": total_work_row_list,
            "authors": total_author_row_list,
            "fandoms": total_fandom_row_list,
            "warnings": total_archive_warning_row_list,
            "misc": total_other_tag_row_list,
            "series": total_series_row_list,
            "characters": total_ao3_char_row_list
        }

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

        characters = tags.find('li', class_='characters')
        character_list = None
        if characters is not None:
            character_list = []
            for character_child in characters.findAll('a'):
                character_list.append(character_child.contents[0])

        other_tags = tags.findAll('li', class_='freeforms')
        other_tags_list = None
        # other_tag_last = tags.find('li', class_='freeforms last') # TODO should probably figure out if this is getting parsed or not
        """
        The issue with parsing all the extra tags is that they hyperlink to their verbatim tag url, and only THEN
        do they get redirected if they're tag-wrangled. For example,
        
        In "Two Timing Touch And Broken Bones" (https://archiveofourown.org/works/38860611), ashiftiperson lovingly 
        included the tag "no beta we die like men". bs4 sees the attached url like so...
        
            https://archiveofourown.org/tags/no%20beta%20we%20die%20like%20men/works
        
        ...which we can see is word-for-word the author's written tag, shoved into a URL.
        
        But what the tag URL ACTUALLY redirects to is:
        
            https://archiveofourown.org/tags/Not%20Beta%20Read/works
        
        This unfortunately means that there's no publicly-facing tag-id wrangled out that I can take advantage of.
        Not sure if I will hit a massive bottleneck with rate-limiting if I try to visit every single tag page or not,
        but when I allowed 1 second between clicks, I went 40 tag-follows without getting rate limited.
        
        TODO needs experimentation for following up tag URLs.
        TODO also experiment with the couple-second delay on fetching pages?? Perhaps it's a rate-limit if they 
        receive X # of requests in a VERY short time span such that it could ONLY be automated??
        """

        if other_tags is not None:
            other_tags_list = []
            for other_tag in other_tags:
                other_tags_list.append(other_tag.contents[0].contents[0])

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
            logging.info('This bookmark has probably been deleted, skipping it. Bookmark:')
            logging.debug(bookmark)
            return None, None, None

        word_count_child = stats.find('dd', class_='words')
        if word_count_child is None:
            # USUALLY word count has the class assigned to it, but then sometimes you get weird works like
            # https://archiveofourown.org/series/889014 which show up on bookmarks with no classes on their dd tags
            logging.info('This bookmark is probably a series, skipping it. Bookmark:')
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
