import re

import requests
from bs4 import BeautifulSoup

from scraper.FFNScraper import FFNScraper
from postgresql.AuthorRow import AuthorRow
from postgresql.CharacterRow import CharacterRow
from postgresql.FFNGenreRow import FFNGenreRow
from postgresql.FandomRow import FandomRow
from postgresql.WorkRow import WorkRow


class FFNMobileScraper(FFNScraper):
    def __init__(self, html_link, queue):
        FFNScraper.__init__(self, html_link, queue)
        self._log_prefix = 'ffn_mobile '

    def process_fanfiction_dot_net_mobile(self):
        print self._log_prefix + 'Starting FanfictionDotNetMobile'

        website = 'FanFiction.Net'
        personal_rating = None
        work_row_list = set()
        author_row_list = set()
        fandom_row_list = set()
        ffn_genre_row_list = set()
        ffn_char_row_list = set()

        print '\n'
        print '/ ~~~~~~~~~~~~~~~~~~~~~~~ \\'
        print '|   Mobile (WC rounded)   |'
        print '\\ ~~~~~~~~~~~~~~~~~~~~~~~ /'

        max_page_num = self.find_max_page_num()
        trimmed_link = self._html_link[0:len(self._html_link) - 1]

        # Start iterating...
        for page_num in range(1, max_page_num + 1):
            print self._log_prefix + 'searching on page ' + str(page_num)

            # Fetch page
            ff_url = trimmed_link + unicode(page_num)
            response = requests.get(ff_url)
            html = response.content
            soup = BeautifulSoup(html, 'html.parser')

            # Filter down to fic entries
            brb_stories = soup.find_all('div', class_='bs brb')
            brb_alto_stories = soup.find_all('div', class_='bs alto brb')

            # Set possible None immediately
            characters = None
            is_complete = False
            total_chapters_count = None

            # Scrape fields
            for fav_story_tag in brb_stories + brb_alto_stories:
                work_id, title = self.processMobileTitle(fav_story_tag)
                author_id, author_name = self.process_mobile_author(fav_story_tag)

                stats_child = fav_story_tag.find('div', class_='gray')
                epoch_tags = stats_child.find_all('span')

                partitions = stats_child.contents
                if len(partitions) == 1:
                    self.errorAndQuit('only one string, no datetime, that is very strange', str(partitions))

                # These two basic stats should always be here
                fandoms, content_rating, genres, released_chapters_count, word_count = \
                    self.process_mobile_fandom_rating_genre_chapter_wc(partitions[0])

                publish_epoch_sec, update_epoch_sec = self.process_publish_update_time(epoch_tags)

                # This part is definitely optional
                if (len(partitions) == 3 and update_epoch_sec == publish_epoch_sec) or (len(partitions) == 5):
                    characters, is_complete = self.process_characters_complete(partitions[len(partitions) - 1])

                if is_complete is not None and is_complete:
                    total_chapters_count = released_chapters_count

                work_row_list.add(WorkRow(work_id, title, website, word_count, publish_epoch_sec,
                                          update_epoch_sec, released_chapters_count, total_chapters_count,
                                          personal_rating, is_complete, content_rating))

                author_row_list.add(AuthorRow(work_id, author_id, author_name))

                if fandoms is not None:
                    for fandom_name in fandoms:
                        fandom_row_list.add(FandomRow(work_id, fandom_name))

                if genres is not None:
                    for genre_row in genres:
                        ffn_genre_row_list.add(FFNGenreRow(work_id, genre_row))

                if characters is not None:
                    for character_name in characters:
                        ffn_char_row_list.add(CharacterRow(work_id, character_name))

        # Place results
        self._queue.put(('mobile work_row_list', work_row_list))
        self._queue.put(('mobile author_row_list', author_row_list))
        self._queue.put(('mobile fandom_row_list', fandom_row_list))
        self._queue.put(('mobile ffn_genre_row_list', ffn_genre_row_list))
        self._queue.put(('mobile ffn_char_row_list', ffn_char_row_list))
        print self._log_prefix +  'Exiting FanfictionDotNetMobile'

    def find_max_page_num(self):
        ff_url = self._html_link
        response = requests.get(ff_url)
        html = response.content

        soup = BeautifulSoup(html, 'html.parser')

        # Find max page num
        max_page_num = 0
        for child in soup.find_all(id='content'):
            for sub_child in child('div', attrs={'align': 'center', 'style': 'margin-top:5px'}):
                for sub_sub_child in sub_child('a', href=re.compile('a=fs&s=0&cid=0&p=')):
                    href_full = sub_sub_child.get('href')
                    page_splits = href_full.split('p=')
                    if len(page_splits) < 2:
                        self.errorAndQuit('can\'t find page number', href_full)
                    if int(page_splits[1]) > max_page_num:
                        max_page_num = int(page_splits[1])

        return max_page_num

    def process_mobile_fandom_rating_genre_chapter_wc(self, child):
        # mobile has an annoying habit of representing by k, e.g. '374k+' instead of '374011'
        # Note that the rating is 'K+' but the word count is 'k+'. Case matters!
        full_num_string = re.sub('k\+', '000', child)

        # content rating is mandatory
        rating_split = re.split(', [KTM]\+*,', full_num_string)
        if len(rating_split) != 2:
            self.errorAndQuit('could not split on rating', full_num_string)
        content_rating_find = re.search(', [KTM]\+*,', full_num_string.encode('utf-8')).group()
        content_rating = content_rating_find[2]
        if len(content_rating_find) == 5:
            content_rating = content_rating_find[2:4]

        # fandom(s) is mandatory
        fandoms = self.processFandoms(rating_split[0])

        # word count is mandatory
        word_count_split = full_num_string.encode('utf-8').split('words: ')
        if len(word_count_split) != 2:
            self.errorAndQuit('could not split on word count', full_num_string)
        fav_split = word_count_split[1].split(', favs:')
        if len(fav_split) != 2:
            self.errorAndQuit('could not split on favs:', full_num_string)
        word_count = fav_split[0]

        # genre(s) are optional
        genres = self.process_mobile_genres(full_num_string)

        # chapter count is optional (could be a one-shot)
        chapter_count_split = full_num_string.encode('utf-8').split('chapters: ')
        released_chapters_count = 1
        if len(chapter_count_split) != 1:
            # not a one-shot, then.
            word_chapter_split = chapter_count_split[1].split(', words:')
            if len(word_chapter_split) != 2:
                self.errorAndQuit('could not split on word count', full_num_string)
            released_chapters_count = word_chapter_split[0]

        return fandoms, content_rating, genres, released_chapters_count, word_count

    def process_publish_update_time(self, time_children):
        if len(time_children) < 1 or len(time_children) > 2:
            self.errorAndQuit('too many time children tags', str(time_children))

        # There will always be at least one time field available
        mandatory_time = time_children[0].get('data-xutime')
        publish_epoch_sec = mandatory_time
        update_epoch_sec = mandatory_time

        if len(time_children) == 2:
            optional_time = time_children[1].get('data-xutime')
            if mandatory_time is None or optional_time is None:
                self.errorAndQuit('times not found', str(time_children))

            if long(mandatory_time) > long(optional_time):
                publish_epoch_sec = optional_time
                update_epoch_sec = mandatory_time
            else:
                publish_epoch_sec = mandatory_time
                update_epoch_sec = optional_time

        return publish_epoch_sec, update_epoch_sec

    def process_characters_complete(self, child):
        characters = self.process_mobile_characters(child)
        is_complete = None
        return characters, is_complete

    def processMobileTitle(self, child):
        # find only the first. find returns a single value, find_all returns a list
        story_a = child.find('a', href=re.compile('\/s\/[0-9]+\/[0-9]\/'))

        if story_a is not None:
            href_value = story_a.get('href').encode('utf-8')
            sections = href_value.split('/')
            if len(sections) < 5:
                self.errorAndQuit('too few partitions in the title tag!', href_value)
            return sections[2], story_a.contents[0].encode('utf-8')

        self.errorAndQuit('title tag not detected', str(child))
        return None

    def process_mobile_author(self, child):
        author_a = child.find('a', href=re.compile('\/u\/[0-9]+\/'))

        if author_a is not None:
            href_value = author_a.get('href').encode('utf-8')
            sections = href_value.split('/')
            if len(sections) < 4:
                self.errorAndQuit('too few partitions in the author tag!', href_value)
            return sections[2], author_a.contents[0].encode('utf-8')

        self.errorAndQuit('author tag not detected', str(child))
        return None

    def process_mobile_genres(self, input_string):
        utf8_string = input_string.encode('utf-8')

        # language will always be included, so we start the pre-split at language
        language_split = utf8_string.split('English, ')
        if len(language_split) < 2:
            self.errorAndQuit('Language missing!! This is dire!!!!', utf8_string)

        # could be a oneshot (chapters field missing)
        if 'chapters: ' not in utf8_string:
            chapters_split = language_split[1].split(', words: ')
            if len(chapters_split) == 1:
                print self._log_prefix + 'no genres to process: ' + input_string
                return None
            else:
                no_genre_words_split = language_split[1].split('words: ')
                if len(no_genre_words_split) < 2:
                    self.errorAndQuit('Word count missing!! This is dire!!!!', utf8_string)
        else:
            chapters_split = language_split[1].split(', chapters:')
            if len(chapters_split) == 1:
                print self._log_prefix + 'no genres to process: ' + input_string
                return None
            else:
                no_genre_chapters_split = language_split[1].split('chapters: ')
                if len(no_genre_chapters_split) < 2:
                    self.errorAndQuit('Chapter count missing!! This is dire!!!!', utf8_string)


        # Just in case, I have seen genres get duped e.g. 'Romance & Romance' e_e so we'll make this a set
        genres = chapters_split[0]
        genre_list = set(genres.split(' & '))

        return genre_list

    def process_mobile_characters(self, input_string):
        utf8_string = input_string.encode('utf-8')
        no_brackets = re.sub(r'\[([^\]]*)\]', r',\1,', utf8_string)

        comma_split = re.split(',+ ?', no_brackets)

        if len(comma_split) < 2:
            print self._log_prefix + 'no characters to process: ' + input_string
            return None

        characters = set(filter(None, comma_split))
        return characters
