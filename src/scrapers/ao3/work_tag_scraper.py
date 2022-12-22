"""
The 200 most popular tags on the Archive are available on https://archiveofourown.org/tags as a word cloud.

Tag search (https://archiveofourown.org/tags/search?tag_search%5Bname%5D=&tag_search%5Bfandoms%5D=&tag_search%5Bty
pe%5D=Freeform&tag_search%5Bcanonical%5D=&tag_search%5Bsort_column%5D=name&tag_search%5Bsort_direction%5D=asc&commit=Search+Tags)
doesn't include <common tag> filtering unfortunately, so we'll have to make do with the top 200 word cloud.

The idea is: for each top 200 tag, there exists many tags with the same meaning.
EX: "I'm Sorry" has these tags with the same meaning (last checked 12/22/22):
    #So very sorry
    (I'm so sorry),
    ...Sorry
    A little sorry
    again i am so sorry
    Apologies.author is very sorry
    because i'm sorry
    desculpa
    desole
    disculpen
    First of all im sorry
    For which I apologize
    förlåt
    GOD im sorry
    I am so fucking sorry
    i am so so so sorry
    I apologize in advance!
    I apologize profusely
    простите
    对不起
...(and so on, there are dozens upon dozens.)

These all wrangle back to the common tag "I'm Sorry".
We will build a cache (sqlite table, really) that maps the freeform tag to the wrangled tag. EX:
    "Apologies.author is very sorry" --> "I'm Sorry"
    "i am so so so sorry" --> "I'm Sorry"
    "простите" --> "I'm Sorry"
which should help cut down on some of the wrangling time a user has to do on their work tags.
"""
import logging

from bs4 import BeautifulSoup

from scrapers.ao3 import constants
from scrapers.ao3.utils_progress_bar import print_progress_bar
from scrapers.ao3.utils_requests import get_req, setup_ao3_session
from sqlite.utils_sqlite import setup_sqlite_connection


class AO3PopularTagScraper:
    def __init__(self, username, password):
        # First we need to set up a connection to sqlite db, as this is where we're going to be dumping.
        logging.info('Setting up an active connection to the sqlite db...')
        con, cur = setup_sqlite_connection()
        self._sqlite_con = con
        self._sqlite_cur = cur

        # Then set up active session for AO3.
        self._username = username
        self._homepage_url = constants.homepage_url
        self._sess = setup_ao3_session(username, password)

    def __repr__(self):
        # This line is directly from # https://github.com/alexwlchan/ao3/blob/master/src/ao3/users.py
        return '%s(username=%r)' % (type(self).__name__, self._username)

    def close_connection(self):
        logging.info('Closing connection to sqlite db')
        self._sqlite_con.close()

    def scrape_top_200_tags_page(self):
        # Send request
        req = get_req(session=self._sess,
                      url=constants.top_200_tags_url)

        # Parse response
        soup = BeautifulSoup(req.text, features='html.parser')
        ul_tag = soup.find('ul', class_='tags cloud index group')
        a_tags = ul_tag.findAll('a')  # Class could be cloud2, cloud1, whatever
        content = [a_tag.contents[0] for a_tag in a_tags]
        return content

    def wrangle_top_200_work_tags(self):
        # Get the names of the top 200
        top_200_tags_list = self.scrape_top_200_tags_page()

        # Now we will hit main tag page of each of the 200 tags
        num_tags = len(top_200_tags_list)
        wrangled_rows = []
        for i, tag in enumerate(top_200_tags_list):
            # Bookkeeping
            print_progress_bar(prefix='Wrangling most popular tag #{}/{}:'.format(i + 1, num_tags),
                               current=i + 1,
                               length=num_tags)

            # Build the next url request
            href = '/tags/' + tag.replace(' ', '%20').replace('/', '*s*').replace('.', '*d*')

            # Send request
            req = get_req(session=self._sess,
                          url=self._homepage_url + href,
                          retry_num_min=3)

            # Parse response
            soup = BeautifulSoup(req.text, features='html.parser')
            synonym_div = soup.find('div', class_='synonym listbox group')
            try:
                ul_tag = synonym_div.find('ul', class_='tags commas index group')
            except Exception as e:
                logging.error('\nCouldn\'t find the synonym block. This is probably because the tag contains '
                              'escaped characters we haven\'t accounted for.')
                logging.error('Tag name: {}; href attempted: {}'.format(tag, href))
                logging.error(e)
                logging.error('Skipping this tag...')
                continue
            a_tags = ul_tag.findAll('a')
            wrangled_entries = [(a_tag.contents[0], tag) for a_tag in a_tags]

            # Also add in the actual common name of this tag! It maps to itself
            wrangled_entries.append((tag, tag))

            # Add onto the master list
            wrangled_rows.extend(wrangled_entries)

        # Done wrangling - insert/replace the wrangled data
        logging.info('Inserting all aliases of the popular tags into wrangled_work_tags...')
        insert_records = """
        REPLACE INTO wrangled_work_tags(
        work_tag_id, 
        wrangled_tag_id) VALUES(
        ?, 
        ?)
        """
        self._sqlite_cur.executemany(insert_records, wrangled_rows)

        # And we need to make sure we COMMIT the changes!!
        logging.info('Committing changes back to sqlite db')
        self._sqlite_con.commit()
