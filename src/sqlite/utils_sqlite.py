import sqlite3

from sqlite.constants import SQLITE_DIR
from sqlite.utils_import_csv import import_works_csv, import_fandoms_csv, import_authors_csv, import_warnings_csv, \
    import_work_tags, import_wrangled_work_tags, import_unwrangleable_work_tags


def setup_sqlite_connection():
    # Make a new db; open connection
    con = sqlite3.connect(SQLITE_DIR + "/ao3_yir.db")

    # Get a cursor so we can execute SQL
    cur = con.cursor()
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

    # Create tables for works first
    drop_query = """
    DROP TABLE IF EXISTS works;
    """
    cur.execute(drop_query)

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
    drop_query = """
    DROP TABLE IF EXISTS fandoms;
    """
    cur.execute(drop_query)

    create_table = '''
    CREATE TABLE fandoms(
    work_id INTEGER NOT NULL,
    fandom_name TEXT NOT NULL,
    PRIMARY KEY(work_id, fandom_name));
    '''
    cur.execute(create_table)

    # Then authors...
    drop_query = """
    DROP TABLE IF EXISTS authors;
    """
    cur.execute(drop_query)

    create_table = '''
    CREATE TABLE authors(
    work_id INTEGER NOT NULL,
    author_id TEXT NOT NULL,
    author_name TEXT NOT NULL,
    PRIMARY KEY(work_id, author_id));
    '''
    cur.execute(create_table)

    # Then warnings...
    drop_query = """
    DROP TABLE IF EXISTS warnings;
    """
    cur.execute(drop_query)

    create_table = '''
    CREATE TABLE warnings(
    work_id INTEGER NOT NULL,
    warning TEXT NOT NULL,
    PRIMARY KEY(work_id, warning));    
    '''
    cur.execute(create_table)

    # Then additional tags... (this is separate from wrangled tags, and we pretty much never want to drop wrangled tags)
    drop_query = """
    DROP TABLE IF EXISTS work_tags;
    """
    cur.execute(drop_query)

    create_table = '''
    CREATE TABLE work_tags(
    work_id INTEGER NOT NULL,
    work_tag_id TEXT NOT NULL,
    PRIMARY KEY(work_id, work_tag_id));    
    '''
    cur.execute(create_table)

    return con, cur


def clean_slate_sqlite():
    # Setup
    sql_connection, sqlite_cursor = drop_and_setup_sqlite()
    import_works_csv(sqlite_cursor)
    import_fandoms_csv(sqlite_cursor)
    import_authors_csv(sqlite_cursor)
    import_warnings_csv(sqlite_cursor)
    import_work_tags(sqlite_cursor)

    # Setup for wrangled tags - # DO NOT UNCOMMENT UNLESS YOU KNOW WHAT YOU'RE DOING
    # drop_and_setup_wrangled_tags(sqlite_cursor)  # DO NOT UNCOMMENT UNLESS YOU KNOW WHAT YOU'RE DOING
    # import_wrangled_work_tags(sqlite_cursor)  # DO NOT UNCOMMENT UNLESS YOU KNOW WHAT YOU'RE DOING
    # import_unwrangleable_work_tags(sqlite_cursor)  # DO NOT UNCOMMENT UNLESS YOU KNOW WHAT YOU'RE DOING

    # Cleanup
    sql_connection.commit()
    sql_connection.close()
