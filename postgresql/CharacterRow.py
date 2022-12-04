class CharacterRow:
    def __init__(self, work_id, character_name):
        self._work_id = work_id
        self._character_name = character_name

    def __repr__(self):
        return 'CharacterRow ' + self._work_id

    def __str__(self):
        return ('<CharacterRow \n_work_id:%s \n_character_name:%s>' %
                (self._work_id, self._character_name))\
            .encode('utf-8')

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._work_id == other._work_id and self._character_name == other._character_name
        else:
            return False

    def __hash__(self):
        return hash(tuple(self.__dict__))

    def get_insert_query(self):
        return 'INSERT INTO Character (work_id, character_name) '\
               'VALUES (%s, %s)'

    def get_insert_tuple(self):
        return self._work_id, self._character_name

    def get_csv_headers(self):
        return ['work_id',
                'character_name']

    def get_csv_values(self):
        return [self._work_id,
                self._character_name]