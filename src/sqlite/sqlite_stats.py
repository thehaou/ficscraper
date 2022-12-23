import datetime

from sqlite.utils_sqlite import setup_sqlite_connection, format_date_where


def select_all(cur, year: int = None):
    print("Running select-all")
    date_where = ''
    if year:
        epoch_start = datetime.datetime(year=year, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        epoch_end = datetime.datetime(year=year + 1, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        date_where = 'WHERE date_bookmarked >= {epoch_start} AND date_bookmarked < {epoch_end}' \
            .format(epoch_start=epoch_start, epoch_end=epoch_end)

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
        date_where = format_date_where(year=year)

    calc_query = """
    SELECT sum(word_count) as total_word_count 
    FROM works
    {date_where}
    """.format(date_where=date_where)
    rows = cur.execute(calc_query).fetchall()
    # for r in rows:
    #     print(r)
    return rows


def select_biggest_works(cur, year: int = None):
    print("Running biggest works of the year")
    date_where = ''
    if year:
        date_where = format_date_where(year=year)

    select_query = """
    SELECT works.title, works.word_count, authors.author_id
    FROM works
    INNER JOIN authors on works.work_id = authors.work_id
    {date_where}
    ORDER BY word_count DESC
    """.format(date_where=date_where)
    rows = cur.execute(select_query).fetchall()
    # for r in rows:
    #     print(r)
    return rows


def calc_most_per_fandom(cur):
    print("Running # of fics per fandom")
    calc_query = """
    SELECT fandom_name, count(work_id) as num_fics
    FROM fandoms
    GROUP BY fandom_name 
    ORDER BY num_fics DESC
    """
    rows = cur.execute(calc_query).fetchall()
    # for r in rows:
    #     print(r)
    return rows

def calc_wc_and_works_per_fandom(cur, year: int = None):
    print("Running wordcount per fandom")
    date_where = ''
    if year:
        epoch_start = datetime.datetime(year=year, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        epoch_end = datetime.datetime(year=year + 1, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        date_where = 'WHERE date_bookmarked >= {epoch_start} AND date_bookmarked < {epoch_end}' \
            .format(epoch_start=epoch_start, epoch_end=epoch_end)

    calc_query = """
    SELECT fandoms.fandom_name, SUM(works.word_count) as total_wc, COUNT(works.work_id) as num_works
    FROM works
    INNER JOIN fandoms ON works.work_id = fandoms.work_id
    {date_where}    
    GROUP BY fandoms.fandom_name
    ORDER BY total_wc DESC
    """.format(date_where=date_where)
    rows = cur.execute(calc_query).fetchall()
    # for r in rows:
    #     print(r)
    return rows


def select_first_fic_per_fandom_wc(cur, year: int = None):
    print("Running first fic per fandom")
    date_where = ''
    if year:
        epoch_start = datetime.datetime(year=year, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        epoch_end = datetime.datetime(year=year + 1, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        date_where = 'WHERE date_bookmarked >= {epoch_start} AND date_bookmarked < {epoch_end}' \
            .format(epoch_start=epoch_start, epoch_end=epoch_end)

    calc_query = """
    SELECT fandoms.fandom_name, min(works.date_bookmarked) as first_bookmark, count(works.work_id) as num_works, sum(works.word_count) as total_wc, title, works.work_id, authors.author_id
    FROM works
    INNER JOIN fandoms ON works.work_id = fandoms.work_id
    INNER JOIN authors on works.work_id = authors.work_id
    {date_where}    
    GROUP BY fandoms.fandom_name
    ORDER BY total_wc DESC
    """.format(date_where=date_where)
    rows = cur.execute(calc_query).fetchall()
    # for r in rows:
    #     print(r)
    return rows


def calc_wc_per_author(cur, year: int = None):
    print("Running wordcount per author")
    date_where = ''
    if year:
        epoch_start = datetime.datetime(year=year, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        epoch_end = datetime.datetime(year=year + 1, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        date_where = 'WHERE date_bookmarked >= {epoch_start} AND date_bookmarked < {epoch_end}' \
            .format(epoch_start=epoch_start, epoch_end=epoch_end)

    calc_query = """
    SELECT authors.author_id, SUM(works.word_count) as total_wc
    FROM works
    INNER JOIN authors ON works.work_id = authors.work_id
    {date_where}    
    GROUP BY authors.author_id
    ORDER BY total_wc DESC
    """.format(date_where=date_where)
    rows = cur.execute(calc_query).fetchall()
    # for r in rows:
    #     print(r)
    return rows


def calc_works_per_author(cur, year: int = None):
    print("Running works per author")
    date_where = ''
    if year:
        epoch_start = datetime.datetime(year=year, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        epoch_end = datetime.datetime(year=year + 1, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        date_where = 'WHERE date_bookmarked >= {epoch_start} AND date_bookmarked < {epoch_end}' \
            .format(epoch_start=epoch_start, epoch_end=epoch_end)

    calc_query = """
    SELECT authors.author_id, COUNT(works.work_id) as total_wc
    FROM works
    INNER JOIN authors ON works.work_id = authors.work_id
    {date_where}    
    GROUP BY authors.author_id
    ORDER BY total_wc DESC
    """.format(date_where=date_where)
    rows = cur.execute(calc_query).fetchall()
    # for r in rows:
    #     print(r)
    return rows


def calc_works_per_rating(cur, year: int = None):
    print("Running works per rating")
    date_where = ''
    if year:
        epoch_start = datetime.datetime(year=year, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        epoch_end = datetime.datetime(year=year + 1, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        date_where = 'WHERE date_bookmarked >= {epoch_start} AND date_bookmarked < {epoch_end}' \
            .format(epoch_start=epoch_start, epoch_end=epoch_end)

    calc_query = """
    SELECT content_rating, COUNT(work_id) as num_works
    FROM works    
    {date_where}    
    GROUP BY content_rating
    ORDER BY num_works DESC
    """.format(date_where=date_where)
    rows = cur.execute(calc_query).fetchall()
    # for r in rows:
    #     print(r)
    return rows


def select_top_10_wrangled_addn_tags_per_rating(cur, year: int = None):
    print("Running top 10 wrangled additional tags per work rating (ex E/M/T/G/unrated)")
    date_where = ''
    if year:
        epoch_start = datetime.datetime(year=year, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        epoch_end = datetime.datetime(year=year + 1, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        date_where = 'WHERE date_bookmarked >= {epoch_start} AND date_bookmarked < {epoch_end}' \
            .format(epoch_start=epoch_start, epoch_end=epoch_end)

    calc_query = """    
    WITH tag_counts_cte AS 
    (
        SELECT cr, tag_id, num_occ, ROW_NUMBER() OVER ( 
                                        PARTITION BY cr 
                                        ORDER BY num_occ DESC ) row_number
        FROM (    
            SELECT 
                works.content_rating as cr, 
                wrangled_work_tags.wrangled_tag_id as tag_id, 
                COUNT(works.work_id) as num_occ                 
            FROM works    
            INNER JOIN work_tags ON works.work_id = work_tags.work_id
            INNER JOIN wrangled_work_tags ON work_tags.work_tag_id = wrangled_work_tags.work_tag_id    
            {date_where}        
            GROUP BY works.content_rating, wrangled_work_tags.wrangled_tag_id
            ORDER BY num_occ DESC
        )        
    ) 
    SELECT cr, tag_id, num_occ
    FROM tag_counts_cte
    WHERE row_number <= 10
    ORDER BY cr DESC     
    """.format(date_where=date_where)
    rows = cur.execute(calc_query).fetchall()
    # for r in rows:
        # print(r)
    return rows


def select_top_10_addn_tags_per_rating(cur, year: int = None):
    print("Running top 10 additional tags per work rating (ex E/M/T/G/unrated)")
    date_where = ''
    if year:
        epoch_start = datetime.datetime(year=year, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        epoch_end = datetime.datetime(year=year + 1, month=1, day=1, hour=0, minute=0, second=0).strftime('%s')
        date_where = 'WHERE date_bookmarked >= {epoch_start} AND date_bookmarked < {epoch_end}' \
            .format(epoch_start=epoch_start, epoch_end=epoch_end)

    calc_query = """    
    WITH tag_counts_cte AS 
    (
        SELECT cr, tag_id, num_occ, ROW_NUMBER() OVER ( 
                                        PARTITION BY cr 
                                        ORDER BY num_occ DESC ) row_number
        FROM (    
            SELECT 
                works.content_rating as cr, 
                work_tags.work_tag_id as tag_id, 
                COUNT(works.work_id) as num_occ                 
            FROM works    
            INNER JOIN work_tags ON works.work_id = work_tags.work_id                
            {date_where}        
            GROUP BY works.content_rating, work_tags.work_tag_id
            ORDER BY num_occ DESC
        )        
    ) 
    SELECT cr, tag_id, num_occ
    FROM tag_counts_cte
    WHERE row_number <= 10
    ORDER BY cr DESC     
    """.format(date_where=date_where)
    rows = cur.execute(calc_query).fetchall()
    # for r in rows:
    #     print(r)
    return rows


def calc_num_unwrangled_work_tags(cur):
    print("Calculating # of unwrangled work tags")
    select_query = """
        SELECT work_tags.work_tag_id
        FROM works
        INNER JOIN work_tags ON works.work_id = work_tags.work_id
        WHERE work_tags.work_tag_id NOT IN
            (SELECT wrangled_work_tags.work_tag_id
             FROM wrangled_work_tags
            ) 
            AND work_tags.work_tag_id NOT IN
            (SELECT unwrangleable_tag_id
             FROM unwrangleable_work_tags
            )         
        GROUP BY work_tags.work_tag_id
        """
    rows = cur.execute(select_query).fetchall()
    print("{} rows".format(len(rows)))
    # for r in rows:
    #     print(r)

    if len(rows) > 0:
        print('You can run the following to capture these: \n\t./ficscraper --wrangle work_tags')
    return set(rows)


if __name__ == '__main__':
    # Setup
    sql_connection, sqlite_cursor = setup_sqlite_connection()

    # Let's calculate stats
    # --- Just works
    # select_all(sqlite_cursor)  # Testing
    calc_total_wc_read(sqlite_cursor, year=2022)
    select_biggest_works(sqlite_cursor, year=2022)
    calc_works_per_rating(sqlite_cursor, year=2022)

    # --- Just fandoms
    calc_most_per_fandom(sqlite_cursor)

    # --- Works AND fandoms
    calc_wc_and_works_per_fandom(sqlite_cursor, year=2022)
    select_first_fic_per_fandom_wc(sqlite_cursor, year=2022)

    # --- Works AND authors
    calc_wc_per_author(sqlite_cursor, year=2022)
    calc_works_per_author(sqlite_cursor, year=2022)

    # --- Top 20 additional tags per work ratings
    select_top_10_wrangled_addn_tags_per_rating(sqlite_cursor, year=2022)
    select_top_10_addn_tags_per_rating(sqlite_cursor, year=2022)

    # --- # of unwrangled works
    calc_num_unwrangled_work_tags(sqlite_cursor)

    # Cleanup
    sql_connection.commit()
    sql_connection.close()
