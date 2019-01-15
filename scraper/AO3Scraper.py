import itertools

import requests
from bs4 import BeautifulSoup


class AO3Scraper:
    def __init__(self, username, password, bookmarks_link, works_subscriptions_link, series_subscriptions_link, queue):
        self._username = username
        self._password = password
        self._bookmarks_link = bookmarks_link
        self._works_subscriptions_link = works_subscriptions_link
        self._series_subscriptions_link = series_subscriptions_link
        self._queue = queue
        self._log_prefix = 'ao3 '

        # set up active session for ao3 - this section is lifted out of
        # https://github.com/alexwlchan/ao3/blob/master/src/ao3/users.py
        sess = requests.Session()
        req = sess.get('https://archiveofourown.org')
        soup = BeautifulSoup(req.text, features='html.parser')

        authenticity_token = soup.find('input', {'name': 'authenticity_token'})['value']
        print 'auth token is ' + str(authenticity_token)
        req = sess.post('https://archiveofourown.org/user_sessions', params={
            'authenticity_token': authenticity_token,
            'user_session[login]': username,
            'user_session[password]': password,
        })

        print req.text

        if 'Please try again' in req.text:
            raise RuntimeError(
                'Error logging in to AO3; is your password correct?')

        self._sess = sess
        print 'session set up'

    # Also from # https://github.com/alexwlchan/ao3/blob/master/src/ao3/users.py
    def __repr__(self):
        return '%s(username=%r)' % (type(self).__name__, self.username)

    def process_bookmarks(self):
        # Happily AO3 starts returning blank results if you exceed the max page
        bookmarks = []
        api_url = (
                'https://archiveofourown.org/users/%s/bookmarks?page=%%d'
                % self._username)

        for page_num in itertools.count(start=1):
            print self._log_prefix + 'searching on page ' + str(page_num)

            req = self._sess.get(api_url % page_num)
            soup = BeautifulSoup(req.text, features='html.parser')

            # The entries are stored in a list of the form:
            #
            #     <ol class="bookmark index group">
            #       <li id="bookmark_12345" class="bookmark blurb group" role="article">
            #         ...
            #       </li>
            #       <li id="bookmark_67890" class="bookmark blurb group" role="article">
            #         ...
            #       </li>
            #       ...
            #     </o
            ol_tag = soup.find('ol', attrs={'class': 'bookmark'})
            print ol_tag
            for li_tag in ol_tag.findAll('li', attrs={'class': 'blurb'}):
                print 'li_tag'
                print li_tag
