import datetime
import logging
import sqlite3

from sqlite.constants import SQLITE_DIR
from sqlite.utils_import_csv import import_works_csv, import_fandoms_csv, import_authors_csv, import_warnings_csv, \
    import_work_tags


def setup_sqlite_connection():
    # Make a new db; open connection
    logging.info('Connecting to sqlite instance ao3_yir.db...')
    con = sqlite3.connect(SQLITE_DIR + "/ao3_yir.db")

    # Get a cursor so we can execute SQL
    cur = con.cursor()
    logging.info('Connected!')
    return con, cur


def drop_and_setup_wrangled_tags(cur):
    # First we set up the tags that we have successfully wrangled (reduced) to a more common tag id
    drop_query = """
    DROP TABLE IF EXISTS wrangled_work_tags;
    """
    cur.execute(drop_query)

    create_table = '''
    CREATE TABLE wrangled_work_tags(
    work_tag_id TEXT NOT NULL,
    wrangled_tag_id TEXT NOT NULL,
    PRIMARY KEY(work_tag_id, wrangled_tag_id));    
    '''
    cur.execute(create_table)

    # Then we set up the tags that we have tried to wrangled and found cannot (they are Additional Category tags)
    drop_query = """
    DROP TABLE IF EXISTS unwrangleable_work_tags;
    """
    cur.execute(drop_query)

    create_table = '''
    CREATE TABLE unwrangleable_work_tags(
    unwrangleable_tag_id TEXT PRIMARY KEY);    
    '''
    cur.execute(create_table)


def drop_and_setup_sqlite():
    con, cur = setup_sqlite_connection()

    logging.info('\n')
    logging.info('/ ~~~~~~~~~~~~~~~~~~~~~~~ \\')
    logging.info('|   sqlite - drop & load   |')
    logging.info('\\ ~~~~~~~~~~~~~~~~~~~~~~~ /')
    logging.info('Due to the constantly updating nature of fic (such as word count & chapters), '
                 'ficscraper drops & recreates all db tables used to calculate fanfic stats.')

    # Create tables for works first
    logging.info('Dropping works table...')
    drop_query = """
    DROP TABLE IF EXISTS works;
    """
    cur.execute(drop_query)

    logging.info('Creating works table...')
    create_table = '''
    CREATE TABLE works(
    work_id INTEGER PRIMARY KEY,
    title TEXT NOT NULL,
    word_count INTEGER NOT NULL,
    publish_epoch_sec INTEGER NOT NULL,
    update_epoch_sec INTEGER NOT NULL,
    released_chapters_count INTEGER NOT NULL,
    total_chapters_count INTEGER,
    is_complete INTEGER NOT NULL,
    content_rating TEXT,
    date_bookmarked INTEGER NOT NULL);
    '''
    cur.execute(create_table)

    # Then for fandoms...
    logging.info('Dropping fandoms table...')
    drop_query = """
    DROP TABLE IF EXISTS fandoms;
    """
    cur.execute(drop_query)

    logging.info('Creating fandoms table...')
    create_table = '''
    CREATE TABLE fandoms(
    work_id INTEGER NOT NULL,
    fandom_name TEXT NOT NULL,
    PRIMARY KEY(work_id, fandom_name));
    '''
    cur.execute(create_table)

    # Then authors...
    logging.info('Dropping authors table...')
    drop_query = """
    DROP TABLE IF EXISTS authors;
    """
    cur.execute(drop_query)

    logging.info('Creating authors table...')
    create_table = '''
    CREATE TABLE authors(
    work_id INTEGER NOT NULL,
    author_id TEXT NOT NULL,
    author_name TEXT NOT NULL,
    PRIMARY KEY(work_id, author_id));
    '''
    cur.execute(create_table)

    # Then warnings...
    logging.info('Dropping warnings table...')
    drop_query = """
    DROP TABLE IF EXISTS warnings;
    """
    cur.execute(drop_query)

    logging.info('Creating warnings table...')
    create_table = '''
    CREATE TABLE warnings(
    work_id INTEGER NOT NULL,
    warning TEXT NOT NULL,
    PRIMARY KEY(work_id, warning));    
    '''
    cur.execute(create_table)

    # Then additional tags... (this is separate from wrangled tags, and we pretty much never want to drop wrangled tags)
    logging.info('Dropping work_tags table... (this is separate from our cache of known wrangled tags)')
    drop_query = """
    DROP TABLE IF EXISTS work_tags;
    """
    cur.execute(drop_query)

    logging.info('Creating work_tags table...')
    create_table = '''
    CREATE TABLE work_tags(
    work_id INTEGER NOT NULL,
    work_tag_id TEXT NOT NULL,
    PRIMARY KEY(work_id, work_tag_id));    
    '''
    cur.execute(create_table)

    logging.info('Done dropping & creating tables')
    return con, cur


def clean_slate_sqlite():
    # Setup
    sql_connection, sqlite_cursor = drop_and_setup_sqlite()
    import_works_csv(sqlite_cursor)
    import_authors_csv(sqlite_cursor)
    import_fandoms_csv(sqlite_cursor)
    import_warnings_csv(sqlite_cursor)
    import_work_tags(sqlite_cursor)
    # import_user_tags_csv(sqlite_cursor)           # TODO Unimplemented
    # import_series_tags_csv(sqlite_cursor)         # TODO Unimplemented
    # import_character_tags_csv(sqlite_cursor)      # TODO Unimplemented
    # import_relationship_tags_csv(sqlite_cursor)   # TODO Unimplemented

    # Setup for wrangled tags - # DO NOT UNCOMMENT UNLESS YOU KNOW WHAT YOU'RE DOING
    # drop_and_setup_wrangled_tags(sqlite_cursor)  # DO NOT UNCOMMENT UNLESS YOU KNOW WHAT YOU'RE DOING
    # import_wrangled_work_tags(sqlite_cursor)  # DO NOT UNCOMMENT UNLESS YOU KNOW WHAT YOU'RE DOING
    # import_unwrangleable_work_tags(sqlite_cursor)  # DO NOT UNCOMMENT UNLESS YOU KNOW WHAT YOU'RE DOING

    # Cleanup
    logging.info('Committing changes back to sqlite db')
    sql_connection.commit()
    logging.info('Closing connection to sqlite db')
    sql_connection.close()


def format_date_where(year: int):
    epoch_start = datetime.datetime(year=year, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
    epoch_end = datetime.datetime(year=year + 1, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
    date_where = 'WHERE date_bookmarked >= {epoch_start} AND date_bookmarked < {epoch_end}' \
        .format(epoch_start=epoch_start, epoch_end=epoch_end)
    return date_where
