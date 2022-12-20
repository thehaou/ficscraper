import csv
import json

import pandas as pd

from sqlite.constants import ROOT_DIR


def import_unwrangleable_work_tags(cur):
    with open(ROOT_DIR + '/src/scrapers/ao3/caches/additional_tags_cache.json', 'r') as f:
        data = json.load(f)

        insert_records = """
        INSERT INTO unwrangleable_work_tags(
        unwrangleable_tag_id) VALUES(         
        ?)
        """
        content = [(key,) for key in data.keys()]
        cur.executemany(insert_records, content)


def import_wrangled_work_tags(cur):
    # TODO - really need to change this to a separate "get wrangled tags wragggh"
    with open(ROOT_DIR + '/output/csvs/work_tags_wrangled.csv', 'r') as f:
        contents = csv.reader(f)
        headers = next(contents)  # Skip headers

        insert_records = """
        INSERT INTO wrangled_work_tags(
        work_tag_id, 
        wrangled_tag_id) VALUES(
        ?, 
        ?)
        """

        cur.executemany(insert_records, contents)


def import_work_tags(cur):
    # Clean CSV - move this out to another step
    df = pd.read_csv(ROOT_DIR + '/output/csvs/work_tags.csv')
    df.drop_duplicates(inplace=True)
    df.to_csv(ROOT_DIR + '/output/csvs/deduped/work_tags.csv', index=False)

    with open(ROOT_DIR + '/output/csvs/deduped/work_tags.csv', 'r') as f:
        contents = csv.reader(f)
        headers = next(contents)  # Skip headers TODO make the table insert & create based on headers

        insert_records = """
        INSERT INTO work_tags(
        work_id, 
        work_tag_id) VALUES(
        ?, 
        ?)
        """

        cur.executemany(insert_records, contents)


def import_warnings_csv(cur):
    # Clean CSV - move this out to another step
    df = pd.read_csv(ROOT_DIR + '/output/csvs/warnings.csv')
    df.drop_duplicates(inplace=True)
    df.to_csv(ROOT_DIR + '/output/csvs/deduped/warnings.csv', index=False)
    with open(ROOT_DIR + '/output/csvs/deduped/warnings.csv', 'r') as f:
        contents = csv.reader(f)
        headers = next(contents)  # Skip headers TODO make the table insert & create based on headers

        insert_records = """
        INSERT INTO warnings(
        work_id, 
        warning) VALUES(
        ?, 
        ?)
        """

        cur.executemany(insert_records, contents)


def import_authors_csv(cur):
    # Clean CSV - move this out to another step
    df = pd.read_csv(ROOT_DIR + '/output/csvs/authors.csv')
    df.drop_duplicates(inplace=True)
    df.to_csv(ROOT_DIR + '/output/csvs/deduped/authors.csv', index=False)

    with open(ROOT_DIR + '/output/csvs/deduped/authors.csv', 'r') as f:
        # # Real fast, need to find dupe ids
        # work_ids = {}
        # contents = csvs.reader(f)
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
    # Clean CSV - move this out to another step
    df = pd.read_csv(ROOT_DIR + '/output/csvs/fandoms.csv')
    df.drop_duplicates(inplace=True)
    df.to_csv(ROOT_DIR + '/output/csvs/deduped/fandoms.csv', index=False)

    with open(ROOT_DIR + '/output/csvs/deduped/fandoms.csv', 'r') as f:
        # # Real fast, need to find dupe ids
        # work_ids = {}
        # contents = csvs.reader(f)
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
    # Clean CSV - move this out to another step
    df = pd.read_csv(ROOT_DIR + '/output/csvs/works.csv')
    df.drop_duplicates(inplace=True)
    df.to_csv(ROOT_DIR + '/output/csvs/deduped/works.csv', index=False)

    with open(ROOT_DIR + '/output/csvs/deduped/works.csv', 'r') as f:
        # # Real fast, need to find dupe ids
        # work_ids = {}
        # contents = csvs.reader(f)
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

