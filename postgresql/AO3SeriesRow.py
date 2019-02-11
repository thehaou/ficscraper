class AO3SeriesRow:
    def __init__(self, work_id, series_id, series_name):
        self._work_id = work_id
        self._series_id = series_id
        self._series_name = series_name

    def __repr__(self):
        return 'AO3SeriesRow ' + self._work_id

    def __str__(self):
        return ('<AO3SeriesRow \n_work_id:%s \n_series_id:%s \n_series_name:%s>' %
                (self._work_id, self._series_id, self._series_name))\
            .encode('utf-8')

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._work_id == other._work_id and self._series_id == other._series_id
        else:
            return False

    def __hash__(self):
        return hash(tuple(self.__dict__))

    def get_insert_query(self):
        return 'INSERT INTO AO3Series (work_id, series_id, series_name) '\
               'VALUES (%s, %s, %s)'

    def get_insert_tuple(self):
        return self._work_id, self._series_id, self._series_name
