class AuthorRow:
    def __init__(self, work_id, author_id, author_name):
        self._work_id = work_id
        self._author_id = author_id
        self._author_name = author_name
        
    def __repr__(self):
        return 'AuthorRow ' + self._work_id + ' ' + self._author_id

    def __str__(self):
        return ('<AuthorRow \n_work_id:%s \n_author_id:%s \n_author_name:%s>' %
                (self._work_id, self._author_id, self._author_name))\
            .encode('utf-8')

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._work_id == other._work_id and self._author_id == other._author_id
        else:
            return False

    def __hash__(self):
        return hash(tuple(self.__dict__))

    def get_insert_query(self):
        return 'INSERT INTO Author (work_id, author_id, author_name) '\
               'VALUES (%s, %s, %s)'

    def get_insert_tuple(self):
        return self._work_id, self._author_id, self._author_name