from enum import Enum

class ContentRating(Enum):
    K = 'K'
    K_plus = 'K+'
    G = 'G'
    T = 'T'
    M = 'M'
    E = 'E'


class WorkRow:
    def __init__(self, work_id, title, website, word_count, publish_epoch_sec, update_epoch_sec, released_chapters_count
                 , total_chapters_count, personal_rating, is_complete, content_rating):
        self._work_id = work_id
        self._title = title
        self._website = website
        self._word_count = word_count
        self._publish_epoch_sec = publish_epoch_sec
        self._update_epoch_sec = update_epoch_sec
        self._released_chapters_count = released_chapters_count
        self._total_chapters_count = total_chapters_count
        self._personal_rating = personal_rating
        self._is_complete = is_complete
        self._content_rating = content_rating

    def __repr__(self):
        return 'WorkRow ' + self._work_id

    def __str__(self):
        return ('<WorkRow \n_work_id:%s \n_title:%s \n_website:%s \n_word_count:%s \n_publish_epoch_sec:%s ' \
               '\n_update_epoch_sec:%s \n_released_chapters_count:%s \n_total_chapters_count:%s \n_personal_rating:%s ' \
               '\n_is_complete:%s \n_content_rating:%s>' % (self._work_id, self._title, self._website, self._word_count,
                                                            self._publish_epoch_sec, self._update_epoch_sec,
                                                            self._released_chapters_count, self._total_chapters_count,
                                                            self._personal_rating, self._is_complete,
                                                            self._content_rating))\
            .encode('utf-8')

    def __eq__(self, other):
        if isinstance(other, self.__class__):
            return self._work_id == other._work_id
        else:
            return False

    def __hash__(self):
        return hash(tuple(self.__dict__))

    @staticmethod
    def check_content_rating_enum(prospective):
        return prospective is None or prospective in ContentRating.__members__

    def get_insert_query(self):
        return 'INSERT INTO Work (work_id, title, website, word_count, publish_epoch_sec, update_epoch_sec, '\
               'released_chapters_count, total_chapters_count, personal_rating, is_complete, content_rating) '\
               'VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'

    def get_insert_tuple(self):
        return self._work_id, self._title, self._website, self._word_count, self._publish_epoch_sec,\
               self._update_epoch_sec, self._released_chapters_count, self._total_chapters_count,\
               self._personal_rating, self._is_complete, self._content_rating
