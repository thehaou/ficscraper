import logging

from bs4 import BeautifulSoup

from scrapers.ao3 import constants
from scrapers.ao3.utils_progress_bar import print_progress_bar
from scrapers.ao3.utils_requests import get_req, setup_ao3_session
from sqlite.utils_sqlite import setup_sqlite_connection


class AO3TagWrangler:
    def __init__(self, username, password):
        # First we need to set up a connection to sqlite db. This will tell us what wrangles tags we have & what we
        # still need to try to wrangle
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
        logging.info('AO3 rate-limits roughly ~80 work-tag page-fetch-->redirects per ~10 minutes.\n'
                     '\tIf the works you read have a lot of additional tags, this may take a while. For example:\n'
                     '\n'
                     '\tassume ~30 additional tags per work (e.g. "Fluff", "Alternate Universe - Canon Divergence", ...)\n'
                     '\tassume you\'ve read ~1000 works\n'
                     '\t= (~1000works) * (~30tags/work) * (10min/80tags)\n'
                     '\t= 3750min+\n'
                     '\t= at least 62.5hrs   (yes you read that right)\n'
                     '\n'
                     '\tThis process can EASILY run for several days straight, and it can also easily fall apart\n'
                     '\tif you use AO3 in the mean time. You WILL need to change your computer sleep settings so it doesn\'t\n'
                     '\tfall asleep while ficscraper is working.\n\n'
                     '\tIn case it does, however, ficscraper will commit the tags it was able to wrangle, so you won\'t\n'
                     '\thave to go back and re-wrangle them. So it\'s not the end of the world if your computer falls\n'
                     '\tasleep; you just have to keep rerunning this wrangler until it goes down to 0.\n')

        wrangled_relations_list = []
        unwrangleable_list = []
        num_unkn_status_tags = len(unkn_status_tags_set)
        num_wrangled = 0
        try:
            for unkn_status_tag in unkn_status_tags_set:
                # Bookkeeping
                work_tag_id = unkn_status_tag[0]
                num_wrangled += 1
                print_progress_bar(prefix='Wrangling tag {}/{}:'.format(num_wrangled, num_unkn_status_tags),
                                   current=num_wrangled,
                                   length=num_unkn_status_tags)

                # Send the request
                href = '/tags/' + work_tag_id.replace(' ', '%20') + '/works'
                req = get_req(self._sess, self._homepage_url + href, retry_num_min=3)

                # Parse the request
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
        except Exception as e:
            logging.error('ficscraper ran into an error while doing work tag wrangling. '
                          '(Your computer probably fell asleep.) '
                          '\nFicscraper will commit back to sqlite the tags it was able to successfully wrangle.')
            logging.error(e)

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
