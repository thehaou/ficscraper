from bs4 import BeautifulSoup
from scraper.FFNScraper import FFNScraper
import re
import requests

from postgresql.AuthorRow import AuthorRow
from postgresql.FFNCharacterRow import FFNCharacterRow
from postgresql.FFNGenreRow import FFNGenreRow
from postgresql.FandomRow import FandomRow
from postgresql.WorkRow import WorkRow


class FFNDesktopScraper(FFNScraper):

    def __init__(self, html_link, queue):
        FFNScraper.__init__(self, html_link, queue)
        self._log_prefix = 'ffn_desktop '

    def process_fanfiction_dot_net_desktop(self):
        print  self._log_prefix + 'Starting FanfictionDotNetDesktop'

        website = 'FanFiction.Net'
        personal_rating = None
        ff_url = self._html_link
        response = requests.get(ff_url)
        html = response.content

        soup = BeautifulSoup(html, 'html.parser')

        work_row_list = set()
        author_row_list = set()
        fandom_row_list = set()
        ffn_genre_row_list = set()
        ffn_char_row_list = set()

        print '\n'
        print '/ ~~~~~~~~~~~~~~~~~~~~~~~ \\'
        print '|    Desktop (500 MAX)    |'
        print '\\ ~~~~~~~~~~~~~~~~~~~~~~~ /'

        for fav_story_tag in soup.find_all('div', class_='z-list favstories'):
            fandoms = self.processFandoms(fav_story_tag.attrs['data-category'])
            released_chapters_count = fav_story_tag.attrs['data-chapters']
            publish_epoch_sec = fav_story_tag.attrs['data-datesubmit']
            update_epoch_sec = fav_story_tag.attrs['data-dateupdate']
            work_id = fav_story_tag.attrs['data-storyid']
            title = fav_story_tag.attrs['data-title']
            word_count = fav_story_tag.attrs['data-wordcount']

            author_children = fav_story_tag.find_all('a')
            (author_id, author_name) = self.process_author_children_stats(author_children)

            other_detail_child = fav_story_tag.find_all('div', class_='z-padtop2 xgray')
            (content_rating, genres, characters, is_complete,
             total_chapters_count) = self.process_other_detail_child_stats(
                other_detail_child, released_chapters_count)

            work_row_list.add(
                WorkRow(work_id, title, website, word_count, publish_epoch_sec, update_epoch_sec,
                        released_chapters_count,
                        total_chapters_count, personal_rating, is_complete, content_rating))

            author_row_list.add(AuthorRow(work_id, author_id, author_name))

            if fandoms is not None:
                for fandom_name in fandoms:
                    fandom_row_list.add(FandomRow(work_id, fandom_name))

            if genres is not None:
                for genre_row in genres:
                    ffn_genre_row_list.add(FFNGenreRow(work_id, genre_row))

            if characters is not None:
                for character_name in characters:
                    ffn_char_row_list.add(FFNCharacterRow(work_id, character_name))

        self._queue.put(('desktop work_row_list', work_row_list))
        self._queue.put(('desktop author_row_list', author_row_list))
        self._queue.put(('desktop fandom_row_list', fandom_row_list))
        self._queue.put(('desktop ffn_genre_row_list', ffn_genre_row_list))
        self._queue.put(('desktop ffn_char_row_list', ffn_char_row_list))
        print  self._log_prefix + 'Exiting FanfictionDotNetDesktop'

    def process_author_children_stats(self, children):
        for child in children:
            href_value = child.get('href').encode('utf-8')
            if '/u/' in href_value:
                sections = href_value.split('/')
                if len(sections) < 4:
                    self.errorAndQuit('too few partitions in the user tag!', href_value)
                return sections[2], sections[3]

        self.errorAndQuit('author tag not detected', str(children))
        return None

    def process_other_detail_child_stats(self, children, released_chapters_count):
        if len(children) > 1:
            self.errorAndQuit('something is weird, more than one z-padtop2 xgray child', str(children))

        child = children[0]
        content_rating = self.process_rating(child.contents[0])
        genres = self.process_genres(child.contents[0])

        # Depending on whether the fic is finished or not, additional datetime fields may be missing
        characters = None
        is_complete = False
        total_chapters_count = None
        if len(child.contents) > 4:
            characters = self.process_characters(child.contents[4])
            is_complete = self.process_complete(child.contents[4])
        elif len(child.contents) > 2:
            characters = self.process_characters(child.contents[2])
            is_complete = self.process_complete(child.contents[2])

        if is_complete is not None and is_complete:
            total_chapters_count = released_chapters_count

        return content_rating, genres, characters, is_complete, total_chapters_count

    def process_rating(self, input_string):
        utf8_string = input_string.encode('utf-8')

        rating_split = utf8_string.split('Rated: ')
        if len(rating_split) < 2:
            self.errorAndQuit('Rating missing!! This is dire!!!!', utf8_string)

        rating = rating_split[1][0]
        is_enum = WorkRow.check_content_rating_enum(rating)
        if not is_enum:
            self.errorAndQuit(rating + ' is not a recognized rating!! This is dire!!!!', utf8_string)

        return rating

    def process_genres(self, input_string):
        utf8_string = input_string.encode('utf-8')

        language_split = utf8_string.split('English - ')
        if len(language_split) < 2:
            self.errorAndQuit('Language missing!! This is dire!!!!', utf8_string)

        chapters_split = language_split[1].split(' - Chapters:')
        if len(chapters_split) == 1:
            print self._log_prefix + 'no genres to process: ' + input_string
            return None
        else:
            no_genre_chapters_split = language_split[1].split('Chapters:')
            if len(no_genre_chapters_split) < 2:
                self.errorAndQuit('Chapter count missing!! This is dire!!!!', utf8_string)

        genres = chapters_split[0]
        genre_list = set(genres.split('/'))
        return genre_list

    def process_characters(self, input_string):
        utf8_string = input_string.encode('utf-8')
        hyphen_split = utf8_string.split(' - ')

        if len(hyphen_split) < 2:
            print self._log_prefix + 'no characters to process: ' + input_string
            return None

        if 'Complete' in hyphen_split[1]:
            print self._log_prefix + 'no characters to process: ' + input_string
            return None

        no_brackets = re.sub(r'\[([^\]]*)\]', r',\1,', hyphen_split[1])
        comma_split = re.split(',+ ?', no_brackets)
        # Don't allow for duplicates... I've seen a fic put 'Harry P.' twice, see https://www.fanfiction.net/s/2630300
        characters = set(filter(None, comma_split))

        return characters

    def process_complete(self, input_string):
        return 'Complete' in input_string
