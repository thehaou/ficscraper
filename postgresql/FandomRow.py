class FandomRow:
    def __init__(self, work_id, fandom_name):
        self._work_id = work_id
        self._fandom_name = fandom_name

    def __repr__(self):
        return 'FandomRow ' + self._work_id

    def __str__(self):
        return ('<FandomRow \n_work_id:%s \n_fandom_name:%s>' %
                (self._work_id, self._fandom_name))\
            .encode('utf-8')

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._work_id == other._work_id and self._fandom_name == other._fandom_name
        else:
            return False

    def __hash__(self):
        return hash(tuple(self.__dict__))

    def get_insert_query(self):
        return 'INSERT INTO Fandom (work_id, fandom_name) '\
               'VALUES (%s, %s)'

    def get_insert_tuple(self):
        return self._work_id, self._fandom_name

    def get_csv_headers(self):
        return ['work_id',
                'fandom_name']

    def get_csv_values(self):
        return [self._work_id,
                self._fandom_name]