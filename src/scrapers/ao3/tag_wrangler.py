import logging
from time import sleep

import requests
from bs4 import BeautifulSoup

from scrapers.ao3 import constants
from scrapers.ao3.utils_progress_bar import log_progress_bar
from sqlite.utils_sqlite import setup_sqlite_connection


class AO3TagWrangler:
    def __init__(self, username, password):
        self._username = username
        self._password = password
        self._homepage_url = constants.homepage_url
        self._login_url = constants.login_url

        # First we need to set up a connection to sqlite db. This will tell us what wrangles tags we have & what we
        # still need to try to wrangle
        logging.info('Setting up an active connection to the sqlite db...')
        con, cur = setup_sqlite_connection()
        self._sqlite_con = con
        self._sqlite_cur = cur

        # Then set up active session for AO3. This section is based off of
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
        logging.debug('AO3 session set up')

    def __repr__(self):
        # This line is directly from # https://github.com/alexwlchan/ao3/blob/master/src/ao3/users.py
        return '%s(username=%r)' % (type(self).__name__, self._username)

    def close_connection(self):
        logging.info('Closing connection to sqlite db')
        self._sqlite_con.close()

    def get_work_tags_to_wrangle(self):
        select_query = """
        SELECT work_tags.work_tag_id
        FROM works
        INNER JOIN work_tags ON works.work_id = work_tags.work_id
        WHERE work_tags.work_tag_id NOT IN
            (SELECT wrangled_work_tags.work_tag_id
             FROM wrangled_work_tags
            ) 
            AND work_tags.work_tag_id NOT IN
            (SELECT unwrangleable_tag_id
             FROM unwrangleable_work_tags
            )         
        GROUP BY work_tags.work_tag_id
        """
        rows = self._sqlite_cur.execute(select_query).fetchall()
        # for r in rows:
        #     print(r)
        return set(rows)

    def wrangle_all_unknown_work_tags(self):
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
        # First, visit our sqlite (aka our cache) and find the tags that have not been processed (i.e. NOT known
        # to be wrangleable or not)
        logging.info('Getting the list of all work-tags that have not been wrangled yet...')
        unkn_status_tags_set = self.get_work_tags_to_wrangle()

        # UNCOMMENT FOR TESTING - just pop off one unknown tag to test
        # unkn_status_tags_set = [unkn_status_tags_set.pop()]

        if len(unkn_status_tags_set) == 0:
            logging.info('No unknown work tags found. Either you have'
                         '\n\t1) Forgotten to import scraped work tags into this sqlite '
                         '(see ./ficscraper_cli.sh --load), or'
                         '\n\t2) No unwrangled work tags (this is a good thing).'
                         '\nExiting work-tag-wrangling')
            return

        # Time to construct wrangled-not-wrangled
        logging.info('\n')
        logging.info('/ ~~~~~~~~~~~~~~~~~~~~~~~ \\')
        logging.info('|      ArchiveOfOurOwn     |')
        logging.info('\\ ~~~~~~~~~~~~~~~~~~~~~~~ /')
        logging.info(' |     DO NOT USE AO3     |')
        logging.info(' |   WHILE THIS PROGRAM   |')
        logging.info(' |       IS RUNNING       |')
        logging.info(' \\------------------------/')
        logging.info('Beginning wrangling of {} work tags!'
                     '\nThese will either be found to be wrangleable or to be in the Additional Tags Category.'
                     .format(len(unkn_status_tags_set)))

        wrangled_relations_list = []
        unwrangleable_list = []
        num_unkn_status_tags = len(unkn_status_tags_set)
        num_wrangled = 0
        for unkn_status_tag in unkn_status_tags_set:
            # Bookkeeping
            work_tag_id = unkn_status_tag[0]
            num_wrangled += 1
            log_progress_bar(prefix='Wrangling tag {}/{}:'.format(num_wrangled, num_unkn_status_tags),
                             current=num_wrangled,
                             length=num_unkn_status_tags)

            href = '/tags/' + work_tag_id.replace(' ', '%20') + '/works'

            count_503 = 0
            while True:
                req = self._sess.get(self._homepage_url + href)
                sleep(1.5)  # Try to avoid triggering rate limiting

                if req.status_code == 429:
                    # https://otwarchive.atlassian.net/browse/AO3-5761
                    logging.error("\nAO3 rate limits; we will receive 429 \"Too Many Requests\" if we ask for pages "
                                  "too often. We need to wait for several minutes, sorry!")
                    logging.info("Sleeping for 3 min; in the middle of trying to process tag {}"
                                 .format(work_tag_id))
                    sleep(60 * 3)  # Tag-retry MIGHT be shorter than bookmark-page-retry
                    continue
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
            h2_tag = soup.find('h2')
            a_tag = h2_tag.find('a')

            if a_tag:
                # Wrangled tag; let's grab it. A "h2" tag w/o an "a" tag belongs to the Additional Category of tags,
                # aka tags that aren't searchable (usually due to not having enough results).
                wrangled_tag_id = a_tag.contents[0]
                wrangled_relations_list.append((work_tag_id, wrangled_tag_id))
            else:
                unwrangleable_list.append((work_tag_id,))

        # Now that we have the full giant list of wrangled & can't-be-wrangled (unwrangleable), commit back to sqlite
        logging.info('\n')
        logging.info('/ ~~~~~~~~~~~~~~~~~~~~~~~ \\')
        logging.info('|      ArchiveOfOurOwn     |')
        logging.info('\\ ~~~~~~~~~~~~~~~~~~~~~~~ /')
        logging.info(' |  You may now use AO3.  |')
        logging.info(' |     ficscraper will    |')
        logging.info(' |    continue to work    |')
        logging.info(' |   in the background.   |')
        logging.info(' \\------------------------/')

        # Wrangleable...
        logging.info('Inserting all tags found to be wrangleable into wrangled_work_tags...')
        insert_records = """
        INSERT INTO wrangled_work_tags(
        work_tag_id, 
        wrangled_tag_id) VALUES(
        ?, 
        ?)
        """
        self._sqlite_cur.executemany(insert_records, wrangled_relations_list)

        # Unwrangleable...
        logging.info('Inserting all tags that were Additional Tags Category into unwrangleable_work_tags...')
        insert_records = """
        INSERT INTO unwrangleable_work_tags(
        unwrangleable_tag_id) VALUES(         
        ?)
        """
        self._sqlite_cur.executemany(insert_records, unwrangleable_list)

        # And we need to make sure we COMMIT the changes!!
        logging.info('Committing changes back to sqlite db')
        self._sqlite_con.commit()
