class AO3WarningRow:
    def __init__(self, work_id, warning):
        self._work_id = work_id
        self._warning = warning

    def __repr__(self):
        return 'AO3WarningRow ' + self._work_id

    def __str__(self):
        return ('<AO3WarningRow \n_work_id:%s \n_warning:%s>' %
                (self._work_id, self._warning))\
            .encode('utf-8')

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._work_id == other._work_id and self._warning == other._warning
        else:
            return False

    def __hash__(self):
        return hash(tuple(self.__dict__))

    def get_insert_query(self):
        return 'INSERT INTO AO3Warning (work_id, warning) '\
               'VALUES (%s, %s)'

    def get_insert_tuple(self):
        return self._work_id, self._warning
