from html2image import Html2Image

if __name__ == '__main__':
    hti = Html2Image(output_path="card_output",
                     size=(180, 320))  # size: (width, height)

    print("Screenshotting...")
    hti.screenshot(
        html_file='card_templates/card.html', css_file='card_templates/card.css',
        save_as='test.jpg'
    )
    print("Done")
