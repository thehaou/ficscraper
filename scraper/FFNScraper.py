class FFNScraper:
    def __init__(self, html_link, queue):
        self._html_link = html_link
        self._queue = queue

    def processFandoms(self, input_string):
        utf8_string = input_string.encode('utf-8')

        fandom_split = set(utf8_string.split(' & '))
        return fandom_split

    def errorAndQuit(self, error_msg, input_string):
        print error_msg
        print input_string
        exit(-1)
