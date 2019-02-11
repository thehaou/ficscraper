class AO3OtherTagRow:
    def __init__(self, work_id, other_tag):
        self._work_id = work_id
        self._other_tag = other_tag

    def __repr__(self):
        return 'AO3OtherTagRow ' + self._work_id

    def __str__(self):
        return ('<AO3OtherTagRow \n_work_id:%s \n_other_tag:%s>' %
                (self._work_id, self._other_tag))\
            .encode('utf-8')

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._work_id == other._work_id and self._other_tag == other._other_tag
        else:
            return False

    def __hash__(self):
        return hash(tuple(self.__dict__))

    def get_insert_query(self):
        return 'INSERT INTO AO3OtherTag (work_id, other_tag) '\
               'VALUES (%s, %s)'

    def get_insert_tuple(self):
        return self._work_id, self._other_tag
