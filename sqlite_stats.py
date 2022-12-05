import csv
import datetime
import sqlite3

def setup_sqlite():
    # Make a new db; open connection
    con = sqlite3.connect("ao3_yir.db")

    # Get a cursor so we can execute SQL
    cur = con.cursor()

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
    work_id INTEGER,
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
    work_id INTEGER,
    author_id TEXT NOT NULL,
    author_name TEXT NOT NULL,
    PRIMARY KEY(work_id, author_id));
    '''
    cur.execute(create_table)

    return con, cur

def import_authors_csv(cur):
    with open('csv_output/authors.csv', 'r') as f:
        # # Real fast, need to find dupe ids
        # work_ids = {}
        # contents = csv.reader(f)
        # headers = next(contents)  # Skip headers
        # dupes = []
        # for row in contents:
        #     work_id = row[0]
        #     author_id = row[1]
        #     primary_key = work_id + author_id
        #     if primary_key in work_ids:
        #         print("The dupe work id is")
        #         print(row)
        #         dupes.append(row)
        #     else:
        #         work_ids[primary_key] = 1
        # return

        contents = csv.reader(f)
        headers = next(contents)  # Skip headers TODO make the table insert & create based on headers

        insert_records = """
        INSERT INTO authors(
        work_id, 
        author_id,
        author_name) VALUES(
        ?, 
        ?,
        ?)
        """

        cur.executemany(insert_records, contents)

def import_fandoms_csv(cur):
    with open('csv_output/fandoms.csv', 'r') as f:
        # # Real fast, need to find dupe ids
        # work_ids = {}
        # contents = csv.reader(f)
        # headers = next(contents)  # Skip headers
        # dupes = []
        # for row in contents:
        #     work_id = row[0]
        #     fandom_name = row[1]
        #     primary_key = work_id + fandom_name
        #     if primary_key in work_ids:
        #         print("The dupe work id is")
        #         print(row)
        #         dupes.append(row)
        #     else:
        #         work_ids[primary_key] = 1
        # return

        contents = csv.reader(f)
        headers = next(contents)  # Skip headers TODO make the table insert & create based on headers

        insert_records = """
        INSERT INTO fandoms(
        work_id, 
        fandom_name) VALUES(
        ?, 
        ?)
        """

        cur.executemany(insert_records, contents)

def import_works_csv(cur):
    with open('csv_output/works.csv', 'r') as f:
        # # Real fast, need to find dupe ids
        # work_ids = {}
        # contents = csv.reader(f)
        # headers = next(contents)  # Skip headers
        # dupes = []
        # for row in contents:
        #     work_id = row[0]
        #     if work_id in work_ids:
        #         print("The dupe work id is")
        #         print(row)
        #         dupes.append(row)
        #     else:
        #         work_ids[work_id] = 1
        # return

        contents = csv.reader(f)
        headers = next(contents)  # Skip headers TODO make the table insert & create based on headers

        insert_records = """
        INSERT INTO works(
        work_id, 
        title, 
        word_count, 
        publish_epoch_sec, 
        update_epoch_sec,
        released_chapters_count,
        total_chapters_count,
        is_complete,
        content_rating,
        date_bookmarked) VALUES(
        ?, 
        ?, 
        ?, 
        ?, 
        ?,
        ?,
        ?,
        ?,
        ?,
        ?)
        """

        cur.executemany(insert_records, contents)

def select_all(cur, year: int = None):
    print("Running select-all")
    date_where = ''
    if year:
        epoch = datetime.datetime(year=year, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        date_where = 'WHERE date_bookmarked >= {epoch}'.format(epoch=epoch)

    select_all_query = """
    SELECT * 
    FROM works
    {date_where}
    """.format(date_where=date_where)
    rows = cur.execute(select_all_query).fetchall()
    for r in rows:
        print(r)

def calc_total_wc_read(cur, year: int = None):
    print("Running word count summation")
    date_where = ''
    if year:
        epoch = datetime.datetime(year=year, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        date_where = 'WHERE date_bookmarked >= {epoch}'.format(epoch=epoch)

    calc_query = """
    SELECT sum(word_count) as total_word_count 
    FROM works
    {date_where}
    """.format(date_where=date_where)
    rows = cur.execute(calc_query).fetchall()
    for r in rows:
        print(r)

def select_biggest_works(cur, year: int = None):
    print("Running biggest works of the year")
    date_where = ''
    if year:
        epoch = datetime.datetime(year=year, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        date_where = 'WHERE date_bookmarked >= {epoch}'.format(epoch=epoch)

    select_query = """
    SELECT title, word_count  
    FROM works
    {date_where}
    ORDER BY word_count DESC
    """.format(date_where=date_where)

    rows = cur.execute(select_query).fetchall()
    for r in rows:
        print(r)

def calc_most_per_fandom(cur):
    print("Running # of fics per fandom")
    calc_query = """
    SELECT fandom_name, count(work_id) as num_fics
    FROM fandoms
    GROUP BY fandom_name 
    ORDER BY num_fics DESC
    """
    rows = cur.execute(calc_query).fetchall()
    for r in rows:
        print(r)

def calc_wc_per_fandom(cur, year: int = None):
    print("Running wordcount per fandom")
    date_where = ''
    if year:
        epoch = datetime.datetime(year=year, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        date_where = 'WHERE date_bookmarked >= {epoch}'.format(epoch=epoch)

    calc_query = """
    SELECT fandoms.fandom_name, SUM(works.word_count) as total_wc
    FROM works
    INNER JOIN fandoms ON works.work_id = fandoms.work_id
    {date_where}    
    GROUP BY fandoms.fandom_name
    ORDER BY total_wc DESC
    """.format(date_where=date_where)
    rows = cur.execute(calc_query).fetchall()
    for r in rows:
        print(r)

def select_first_fic_per_fandom(cur, year: int = None):
    print("Running first fic per fandom")
    date_where = ''
    if year:
        epoch = datetime.datetime(year=year, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        date_where = 'WHERE date_bookmarked >= {epoch}'.format(epoch=epoch)

    calc_query = """
    SELECT fandoms.fandom_name, min(works.date_bookmarked) as first_bookmark, count(works.work_id) as num_works, sum(works.word_count) as total_wc, title, works.work_id
    FROM works
    INNER JOIN fandoms ON works.work_id = fandoms.work_id
    {date_where}    
    GROUP BY fandoms.fandom_name
    ORDER BY num_works DESC
    """.format(date_where=date_where)
    rows = cur.execute(calc_query).fetchall()
    for r in rows:
        print(r)

def calc_wc_per_author(cur, year: int = None):
    print("Running wordcount per author")
    date_where = ''
    if year:
        epoch = datetime.datetime(year=year, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        date_where = 'WHERE date_bookmarked >= {epoch}'.format(epoch=epoch)

    calc_query = """
    SELECT authors.author_id, COUNT(works.work_id) as total_wc
    FROM works
    INNER JOIN authors ON works.work_id = authors.work_id
    {date_where}    
    GROUP BY authors.author_id
    ORDER BY total_wc DESC
    """.format(date_where=date_where)
    rows = cur.execute(calc_query).fetchall()
    for r in rows:
        print(r)

if __name__ == '__main__':
    # Setup
    sql_connection, sqlite_cursor = setup_sqlite()
    import_works_csv(sqlite_cursor)
    import_fandoms_csv(sqlite_cursor)
    import_authors_csv(sqlite_cursor)

    # Let's calculate stats
    # --- Just works
    # select_all(sqlite_cursor)  # Testing
    # calc_total_wc_read(sqlite_cursor, year=2022)
    # select_biggest_works(sqlite_cursor, year=2022)

    # --- Just fandoms
    # calc_most_per_fandom(sqlite_cursor)

    # --- Works AND fandoms
    # calc_wc_per_fandom(sqlite_cursor, year=2022)
    select_first_fic_per_fandom(sqlite_cursor, year=2022)

    # --- Works AND authors
    # calc_wc_per_author(sqlite_cursor, year=2022)

    # Cleanup
    sql_connection.commit()
    sql_connection.close()
