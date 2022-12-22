import pathlib

from sqlite.constants import SQLITE_DIR, SRC_DIR, ROOT_DIR
from sqlite.utils_sqlite import clean_slate_sqlite

if __name__ == '__main__':
    clean_slate_sqlite()
