from html2image import Html2Image
from mako.template import Template
from mako.exceptions import RichTraceback



if __name__ == '__main__':
    try:
        mako_template = Template(filename='card_templates/top_5_fandom.html')
        rendered_template = mako_template.render(
            title="My Statistic Title",
            ranked_items=[{'name': 'Top Rank', 'details': 'The best'},
                          {'name': 'Second Rank', 'details': 'Overshadowed'},
                          {'name': 'Third Rank', 'details': 'Middle of the pack'},
                          {'name': 'Fourth Rank', 'details': 'At least they\'re not last'},
                          {'name': 'Fifth Rank', 'details': 'Happy to be on the list'}])
    except:
        traceback = RichTraceback()
        for (filename, lineno, function, line) in traceback.traceback:
            # print("File %s, line %s, in %s" % (filename, lineno, function))
            print(line)

    with open('card_templates/test.html', 'w') as f:
        f.write(rendered_template)

    # hti = Html2Image(output_path="card_output",
    #                  size=(360, 640))  # size: (width, height)
    #
    # print("Screenshotting...")
    # hti.screenshot(
    #     # html_file='card_templates/top_5_fandom.html',
    #     html_str=rendered_template,
    #     css_file='card_templates/card.css',
    #     save_as='test.jpg'
    # )
    # print("Done")
