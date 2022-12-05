from html2image import Html2Image
from mako.template import Template

if __name__ == '__main__':
    mako_template = Template(filename='card_templates/top_5_fandom.html')
    rendered_template = mako_template.render(items=[
        {'name': 'Batman - All Media Types', 'details': '526 fics over 7,450,240 words'}
    ])
    hti = Html2Image(output_path="card_output",
                     size=(360, 640))  # size: (width, height)

    print("Screenshotting...")
    hti.screenshot(
        # html_file='card_templates/top_5_fandom.html',
        html_str=rendered_template,
        css_file='card_templates/card.css',
        save_as='test.jpg'
    )
    print("Done")
