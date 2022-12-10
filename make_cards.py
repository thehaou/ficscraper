from html2image import Html2Image
from mako.template import Template
from mako.exceptions import RichTraceback

from sqlite_stats import setup_sqlite, calc_wc_and_works_per_fandom


def get_test_5_ranked_items():
    return [{'name': 'Top Rank', 'details': 'The best'},
            {'name': 'Second Rank', 'details': 'Overshadowed'},
            {'name': 'Third Rank', 'details': 'Middle of the pack'},
            {'name': 'Fourth Rank', 'details': 'At least they\'re not last'},
            {'name': 'Fifth Rank', 'details': 'Happy to be on the list'}]


def get_test_card_title():
    return "My Statistic Title"


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
        name = name.split(':')[0]  # Strip out delimeters like -, :, (
        name = name.split(' - ')[0]
        name = name.split(' (')[0]

        # Compute prefix
        prefix_end = min(len(name), 9)  # 9 is very fine-tuned for my results; Star Wars is 9 characters
        prefix = name[:prefix_end]

        if prefix not in prefixes:
            prefixes.add(prefix)
            top_5.append(row)

    return top_5


def render_mako_template(template_file_name: str, template_args: dict):
    try:
        mako_template = Template(filename=template_file_name)
        rendered_template = mako_template.render(**template_args)
        return rendered_template
    except:
        traceback = RichTraceback()
        for (template_file_name, lineno, function, line) in traceback.traceback:
            # print("File %s, line %s, in %s" % (filename, lineno, function))
            print(line)
        exit(-1)


def make_top_5_fandom_card():
    # Get stats
    con, cur = setup_sqlite()
    top_rows = calc_wc_and_works_per_fandom(cur, year=2022)  # a tuple

    # Compute just the top five from all the rows we got back
    top_five_rows = get_top_five_from_prefix(top_rows)

    # Make the details for the template
    title = "Top 5 Fandoms"
    ranked_items = []
    for row in top_five_rows:
        fandom_name = row[0]
        total_wc = row[1]
        total_num_fics = row[2]
        details_template = "{:,} fics over {:,} words"  # We won't format here because I want the vars to be bolded
        details_template_vars = [total_num_fics, total_wc]
        ranked_items.append({'name': fandom_name,
                             'details_template': details_template,
                             'details_template_vars': details_template_vars})

    # Make the mako template
    rendered_template = render_mako_template(template_file_name="card_templates/top_5.html",
                                             template_args={"title": title, "ranked_items": ranked_items})

    # Write out the HTML to a test file. This is really just for testing CSS quickly in-browser
    # TODO test code, flesh out test folder with it...?
    with open('card_templates/test.html', 'w') as f:
        f.write(rendered_template)

    # Capture HTML to a jpg into our card_output folder
    export_html_as_image(html=rendered_template)
    print("Done")


def export_html_as_image(html: str):
    hti = Html2Image(output_path="card_output",
                     size=(360, 640))  # size: (width, height)

    print("Screenshotting...")
    hti.screenshot(
        # html_file='card_templates/top_5.html',
        html_str=html,
        css_file='card_templates/card.css',
        save_as='test.jpg'
    )


if __name__ == '__main__':
    make_top_5_fandom_card()
