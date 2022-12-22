import argparse
import datetime
import logging

from html2image import Html2Image
from mako.template import Template
from mako.exceptions import RichTraceback

from sqlite.constants import ROOT_DIR, SRC_DIR
from sqlite.sqlite_stats import calc_wc_and_works_per_fandom, calc_wc_per_author, calc_works_per_author, \
    select_first_fic_per_fandom_wc, select_biggest_works
from sqlite.utils_sqlite import setup_sqlite_connection

"""
This file generates some stats one might find interesting for a year-in-review. Cards are outputted to the /cards
directory in JPG format.

Cards generated right now are:
* Top 5 fandoms (by total wc of fics you read from them) (Uses the Top 5 card template 'top_5.html')
* Top 5 authors (by total wc of fics you read from them) (Uses the Top 5 card template 'top_5.html')
* Top 5 authors (by total # of fics you read from them) (Uses the Top 5 card template 'top_5.html')
* First fic + date bookmarked for your Top 5 fandoms (by total wc of fics you read from fandom) 
                                                      (Uses the Top 5 card template 'top_5.html')
                                                      
                                                      
You can modify the "year" field right below this message to change which year it calculates year-in-review for. 
"""

subheading_template = "— AO3 {} YEAR-IN-REVIEW —"  # TODO move to constants...?

# Testing-related things. TODO move out to a testing folder?
def get_test_5_ranked_items():
    return [{'name': 'Top Rank', 'details': 'The best'},
            {'name': 'Second Rank', 'details': 'Overshadowed'},
            {'name': 'Third Rank', 'details': 'Middle of the pack'},
            {'name': 'Fourth Rank', 'details': 'At least they\'re not last'},
            {'name': 'Fifth Rank', 'details': 'Happy to be on the list'}]


def get_test_card_title():
    return "My Statistic Title"


# General-purpose functions
def render_mako_template(template_file_name: str, template_args: dict):
    try:
        mako_template = Template(filename=template_file_name)
        rendered_template = mako_template.render(**template_args)
        return rendered_template
    except:
        traceback = RichTraceback()
        for (template_file_name, lineno, function, line) in traceback.traceback:
            logging.error('ERROR generating Mako template. Please contact the repo owner.')
            logging.error("File %s, line %s, in %s" % (template_file_name, lineno, function))
            logging.error(line)
        exit(-1)


def export_html_as_image(html: str, image_name='test.jpg'):
    hti = Html2Image(output_path=ROOT_DIR + "/output/cards",
                     size=(360, 640))  # size: (width, height)

    logging.info("Screenshotting HTML...")
    hti.screenshot(
        html_str=html,
        css_file=SRC_DIR + '/output_card_templates/css/card.css',
        save_as=image_name
    )

# Card-making callers
def make_top_5_fandom_card(image_name):
    # Get stats
    con, cur = setup_sqlite_connection()
    top_rows = calc_wc_and_works_per_fandom(cur, year=year)  # a tuple

    # Compute just the top five from all the rows we got back
    top_five_rows = get_top_five_from_prefix(top_rows)

    # Make the details for the template
    title = "Your Biggest Fandoms"
    title_flavor = "Once you went in, there was no coming back"
    ranked_items = []
    for row in top_five_rows:
        fandom_name = row[0]
        total_wc = row[1]
        total_num_fics = row[2]
        details_template = "{:,} fics over {:,} words"  # We won't format here because I want the vars to be bolded.
                                                        # See top_5.html opt_vars for more info
        details_template_vars = [total_num_fics, total_wc]
        ranked_items.append({'name': fandom_name,
                             'details_template': details_template,
                             'details_template_vars': details_template_vars})

    # Make the mako template
    rendered_template = render_mako_template(template_file_name=SRC_DIR + '/output_card_templates/html/top_5.html',
                                             template_args={"title": title,
                                                            "title_flavor": title_flavor,
                                                            "subheading": subheading_template.format(year),
                                                            "ranked_items": ranked_items})

    # Write out the HTML to a test file. This is really just for testing CSS quickly in-browser
    # TODO test code, flesh out test folder with it...?
    with open(SRC_DIR + '/output_card_templates/css/test.html', 'w') as f:
        f.write(rendered_template)

    # Capture HTML to a jpg into our cards folder
    export_html_as_image(html=rendered_template, image_name=image_name)
    logging.info("HTML successfully exported as image!")


def make_top_5_authors_wc_card(image_name):
    logging.info('Making top-5-authors-read-by-total-word-count card...')
    # Get stats
    con, cur = setup_sqlite_connection()
    top_rows = calc_wc_per_author(cur, year=year)  # a tuple

    # Do some special cleaning on author names
    top_rows = get_top_five_active(top_rows)

    # Make the details for the template
    title = "Most-Read Authors"
    title_flavor = "You committed to the long haul"
    ranked_items = []
    for row in top_rows:
        author_id = row[0]
        total_wc = row[1]
        details_template = "{:,} words read"  # We won't format here because I want the vars to be bolded.
                                              # See top_5.html opt_vars for more info
        details_template_vars = [total_wc]
        ranked_items.append({'name': author_id,
                             'details_template': details_template,
                             'details_template_vars': details_template_vars})

    # Make the mako template
    rendered_template = render_mako_template(template_file_name=SRC_DIR + '/output_card_templates/html/top_5.html',
                                             template_args={"title": title,
                                                            "title_flavor": title_flavor,
                                                            "subheading": subheading_template.format(year),
                                                            "ranked_items": ranked_items})

    # Write out the HTML to a test file. This is really just for testing CSS quickly in-browser
    # TODO test code, flesh out test folder with it...?
    with open(SRC_DIR + '/output_card_templates/css/test.html', 'w') as f:
        f.write(rendered_template)

    # Capture HTML to a jpg into our cards folder
    export_html_as_image(html=rendered_template, image_name=image_name)
    logging.info("Done")


def make_top_5_authors_count_card(image_name):
    logging.info('Making top-5-authors-read-by-num-works card...')
    # Get stats
    con, cur = setup_sqlite_connection()
    top_rows = calc_works_per_author(cur, year=year)  # a tuple

    # Do some special cleaning on author names
    top_rows = get_top_five_active(top_rows)

    # Make the details for the template
    title = "Most-Read Authors"
    title_flavor = "You followed their pen and paper closely, like a detective"
    ranked_items = []
    for row in top_rows:
        author_id = row[0]
        total_wc = row[1]
        details_template = "{:,} works read"  # We won't format here because I want the vars to be bolded.
        # See top_5.html opt_vars for more info
        details_template_vars = [total_wc]
        ranked_items.append({'name': author_id,
                             'details_template': details_template,
                             'details_template_vars': details_template_vars})

    # Make the mako template
    rendered_template = render_mako_template(template_file_name=SRC_DIR + '/output_card_templates/html/top_5.html',
                                             template_args={"title": title,
                                                            "title_flavor": title_flavor,
                                                            "subheading": subheading_template.format(year),
                                                            "ranked_items": ranked_items})

    # Write out the HTML to a test file. This is really just for testing CSS quickly in-browser
    # TODO test code, flesh out test folder with it...?
    with open(SRC_DIR + '/output_card_templates/css/test.html', 'w') as f:
        f.write(rendered_template)

    # Capture HTML to a jpg into our cards folder
    export_html_as_image(html=rendered_template, image_name=image_name)
    logging.info("Done")


def make_first_fic_of_top_5_fandoms(image_name):
    logging.info('Making first-fic-of-top-5-fandoms card...')
    # Get stats
    con, cur = setup_sqlite_connection()
    top_rows = select_first_fic_per_fandom_wc(cur, year=year)  # a tuple

    # Compute just the top five from all the rows we got back
    top_five_rows = get_top_five_from_prefix(top_rows)

    # Make the details for the template
    title = "Big Fandoms: What and When"
    title_flavor = "The devouring of a fandom begins with a single step"
    ranked_items = []

    # TODO remove, this is hacky and only necessary because I messed up bookmark orderings and I am
    # keenly aware of what my actual Batman-entry fic was. :, (
    # top_five_rows[0] = (top_five_rows[0][0], 1656658800, top_five_rows[0][2], top_five_rows[0][3], "repetitio est mater studiorum", 31849066, "distortopia")

    for row in top_five_rows:
        fandom_name = row[0]
        date_bookmarked_epoch_ms = row[1]
        date_bookmarked = datetime.datetime.fromtimestamp(date_bookmarked_epoch_ms)
        date_bookmarked_template_var = date_bookmarked.strftime("%b %d")
        work_title = row[4]
        # work_id = row[5]  # Only needed if cards were interactive, so we can rebuild the url
        author_id = row[6]

        details_template = "{} - \"" + work_title + "\" by {}"

        # See top_5.html opt_vars for more info
        details_template_vars = [date_bookmarked_template_var, author_id]
        ranked_items.append({'name': fandom_name,
                             'details_template': details_template,
                             'details_template_vars': details_template_vars})

    # Make the mako template
    rendered_template = render_mako_template(template_file_name=SRC_DIR + '/output_card_templates/html/top_5.html',
                                             template_args={"title": title,
                                                            "title_flavor": title_flavor,
                                                            "subheading": subheading_template.format(year),
                                                            "ranked_items": ranked_items})

    # Write out the HTML to a test file. This is really just for testing CSS quickly in-browser
    # TODO test code, flesh out test folder with it...?
    with open(SRC_DIR + '/output_card_templates/css/test.html', 'w') as f:
        f.write(rendered_template)

    # Capture HTML to a jpg into our cards folder
    export_html_as_image(html=rendered_template, image_name=image_name)
    logging.info("Done")


def make_top_5_longest_works_card(image_name):
    logging.info('Making top-5-longest-works-read card...')
    # Get stats
    con, cur = setup_sqlite_connection()
    top_rows = select_biggest_works(cur, year=year)  # a tuple

    # Just truncate
    top_five_rows = top_rows[:5]

    # Make the details for the template
    title = "Longest Works Read"
    title_flavor = "You really sunk your teeth in"
    ranked_items = []

    for row in top_five_rows:
        work_title = row[0]
        wc = row[1]
        author_id = row[2]

        details_template = "\"" + work_title + "\" by {}"

        # See top_5.html opt_vars for more info
        details_template_vars = [author_id]
        ranked_items.append({'name': "{:,} words".format(wc),
                             'details_template': details_template,
                             'details_template_vars': details_template_vars})

    # Make the mako template
    rendered_template = render_mako_template(template_file_name=SRC_DIR + '/output_card_templates/html/top_5.html',
                                             template_args={"title": title,
                                                            "title_flavor": title_flavor,
                                                            "subheading": subheading_template.format(year),
                                                            "ranked_items": ranked_items})

    # Write out the HTML to a test file. This is really just for testing CSS quickly in-browser
    # TODO test code, flesh out test folder with it...?
    with open(SRC_DIR + '/output_card_templates/css/test.html', 'w') as f:
        f.write(rendered_template)

    # Capture HTML to a jpg into our cards folder
    export_html_as_image(html=rendered_template, image_name=image_name)
    logging.info("Done")


# Card-making helpers - usually for odd edge cases
def get_top_five_from_prefix(rows):
    """
    Getting the top 5 fandoms is a bit tough - what does "top 5" mean?
    Because my top 5 as-is from AO3 for 2022 are
        Star Wars - All Media Types,
        Star Wars Prequel Trilogy,
        Star Wars: The Clone Wars...
    ...these three are part of the same family! They're redundant and take up space (ha) other fandoms could use.

    Alternatively, we could try to scrape AO3 for parent-child relations. Ex:
        "Star Wars: The Clone Wars" has the meta tag "Star Wars - All Media Type"
    ...that is, we go up the fandom relation until we hit the one with NO meta tag (the root of the tree).

    Going the opposite direction (Subtags) is harder if just because sometimes the element IS the the leaf already,
    even though subtags still exist on the tag. For example:
        "Star Wars: The Clone Wars" has the subtag "Star Wars: Dark Disciple - Christie Golden"
    ...which I have never read fic for. So going to subtags would be foolhardy.

    I'm going to go for a "best-effort" hacky-ish approach: if we already have a member on the top 5
    that shares the first 10 characters with another one, we'll only include the first one.
    This should broadly take care of stuff like Star Wars VS Star Trek, though overlap like
        "Batman - All Media Types" has meta tag "DCU"
    ...wouldn't end up being caught, and for this iteration of this project, that's fine.
    """
    prefixes = set()
    top_5 = []
    for row in rows:
        if len(top_5) == 5:
            return top_5

        # Clean for prefix
        name = row[0]
        name = name.split(':')[0]  # Strip out delimiters like -, :, (
        name = name.split(' - ')[0]
        name = name.split(' (')[0]

        # Compute prefix
        prefix_end = min(len(name), 9)  # TODO 9 is very fine-tuned for my results; Star Wars is 9 characters.
                                        # Totally useless # for other-language fandoms like 魔道祖师 - 墨香铜臭
        prefix = name[:prefix_end]

        if prefix not in prefixes:
            prefixes.add(prefix)
            top_5.append(row)

    return top_5


def get_top_five_active(rows):
    """"
    This one is specific for authors. There are two special author ids in ao3:
    - orphan_account (means the person has disowned their work), and
    - Anonymous (work is visible on the author's profile... providing you find it. Not accessible on the fic.)

    Neither are very interesting to see in top 5 imo (how do you go about thanking orphan_account or Anonymous?),
    so this skips them.
    """
    top_5 = []
    for row in rows:
        if len(top_5) == 5:
            break

        author_id = row[0]
        if (author_id != 'Anonymous') and (author_id != 'orphan_account'):
            top_5.append(row)
    return top_5


def set_up_parser():
    parser = argparse.ArgumentParser(
        prog='year_in_review_make_cards.py',
        description='Makes shareable JPGs ("cards") based on AO3 data stored in ao3_yir.db sqlite instance.'
                    'Requires populating that instance first, such as via '
                    '\n\t./ficscraper_cli.sh --scrape bookmarks',
        epilog='https://github.com/thehaou/ficscraper#contact-info'
    )
    parser.add_argument('year',
                        help='Year to calculate year-in-review for. A four-digit number.'
                             'EX: to calculate year-in-review for 2022:'
                             '  ./ficscraper_cli.sh --generate year_in_review 2022')
    return parser


if __name__ == '__main__':
    # Set up logging
    logging.basicConfig(level=logging.INFO,  # Switch to logging.INFO for less output
                        format="%(levelname)s - %(message)s")

    # Set up parser
    logging.info('Parsing arguments...')
    parser = set_up_parser()
    args = parser.parse_args()
    try:
        datetime.datetime.strptime(args.year, '%Y')
    except ValueError:
        raise ValueError("Incorrect format for year passed in: should be YYYY")
    year = int(args.year)

    # Start making cards
    logging.info('Kicking off card-creating process...')
    make_top_5_fandom_card(image_name='{}_top_5_fandoms.jpg'.format(year))
    make_top_5_authors_wc_card(image_name='{}_top_5_authors_wc.jpg'.format(year))
    make_top_5_authors_count_card(image_name='{}_top_5_authors_works.jpg'.format(year))
    make_first_fic_of_top_5_fandoms(image_name='{}_top_5_fandoms_first_fic.jpg'.format(year))
    make_top_5_longest_works_card(image_name='{}_top_5_longest_works.jpg'.format(year))

    logging.info('Done creating card JPGs (you can find them in output/cards).')
    logging.info('ficscraper successfully finished running.')
