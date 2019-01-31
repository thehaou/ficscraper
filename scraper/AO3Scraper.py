import itertools

import requests
from bs4 import BeautifulSoup


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

    def process_bookmarks(self):
        print self._log_prefix + 'Starting AO3'

        website = 'ArchiveOfOurOwn'
        personal_rating = None
        work_row_list = set()
        author_row_list = set()
        fandom_row_list = set()
        ffn_genre_row_list = set()
        ffn_char_row_list = set()

        print '\n'
        print '/ ~~~~~~~~~~~~~~~~~~~~~~~ \\'
        print '|      ArchiveOfOurOwn     |'
        print '\\ ~~~~~~~~~~~~~~~~~~~~~~~ /'

        # Happily AO3 starts returning blank results if you exceed the max page
        bookmarks = []
        api_url = (self._bookmarks_url_template % self._username)

        for page_num in itertools.count(start=1):
            print self._log_prefix + 'searching on page ' + str(page_num)

            req = self._sess.get(api_url % page_num)
            soup = BeautifulSoup(req.text, features='html.parser')

            ol_tag = soup.find('ol', attrs={'class': 'bookmark index group'})

            li_tags = ol_tag.findAll('li')
            if len(li_tags) > 0:
                for li_tag in li_tags:
                    work_id, title, author_id, author_name = processHeaderModule(li_tag)
                    # div 'class': 'header module' -->
                        # title, work id (a href)
                        # author (a rel)

                    fandoms = processFandomsHeading(li_tag)
                    # h5 'class': 'fandoms heading'
                        # a 'class': 'tag' <-- mutiple of these

                    content_rating, archiveWarnings = processRequiredTags(li_tag)
                    # ul 'class': 'required tags'

                    update_epoch_sec = processDatetime(li_tag) # publish isn't available from here...
                    # p 'datetime' DD Month YYYY

                    characters, relations, other_tags = processTags(li_tag)
                    # ul 'class': 'tags commas'

                    series = processSeries(li_tag)
                    # ul 'class': 'series'

                    word_count, released_chapters_count, total_chapters_count, is_complete = processStats(li_tag)
                    # dl 'class': 'stats'

                    personal_rating = processOwnUserModuleGroup(li_tag)
                    # div 'class': 'own user module group'
                        # ul 'class': 'meta tags commas'

                    print li_tag
            else:
                break

        print 'done searching on ao3'
