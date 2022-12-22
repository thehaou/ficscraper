import csv
import json
import logging

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
    logging.info('Deduping & importing work_tags.csv...')
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
    logging.info('Deduping & importing warnings.csv...')
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
    logging.info('Deduping & importing authors.csv...')
    # Clean CSV - move this out to another step
    df = pd.read_csv(ROOT_DIR + '/output/csvs/authors.csv')
    df.drop_duplicates(inplace=True)
    df.to_csv(ROOT_DIR + '/output/csvs/deduped/authors.csv', index=False)

    with open(ROOT_DIR + '/output/csvs/deduped/authors.csv', 'r') as f:
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
    logging.info('Deduping & importing fandoms.csv...')
    # Clean CSV - move this out to another step
    df = pd.read_csv(ROOT_DIR + '/output/csvs/fandoms.csv')
    df.drop_duplicates(inplace=True)
    df.to_csv(ROOT_DIR + '/output/csvs/deduped/fandoms.csv', index=False)

    with open(ROOT_DIR + '/output/csvs/deduped/fandoms.csv', 'r') as f:
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
    logging.info('Deduping & importing works.csv...')
    # Clean CSV - move this out to another step
    df = pd.read_csv(ROOT_DIR + '/output/csvs/works.csv')
    df.drop_duplicates(inplace=True)
    df.to_csv(ROOT_DIR + '/output/csvs/deduped/works.csv', index=False)  # TODO for some reason pd is converting total_chapters_count to float?

    with open(ROOT_DIR + '/output/csvs/deduped/works.csv', 'r') as f:
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
