class FFNGenreRow:
    def __init__(self, work_id, genre_name):
        self._work_id = work_id
        self._genre_name = genre_name

    def __repr__(self):
        return 'FFNGenreRow ' + self._work_id + ' ' + self._genre_name

    def __str__(self):
        return ('<FFNGenreRow \n_work_id:%s \n_genre_name:%s>' %
                (self._work_id, self._genre_name))\
            .encode('utf-8')

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._work_id == other._work_id and self._genre_name == other._genre_name
        else:
            return False

    def __hash__(self):
        return hash(tuple(self.__dict__))

    def get_insert_query(self):
        return 'INSERT INTO FFNGenre (work_id, genre_name) '\
               'VALUES (%s, %s)'

    def get_insert_tuple(self):
        return self._work_id, self._genre_name