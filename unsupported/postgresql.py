"""
I used Postgresql because it sounded cool and I knew nothing about dbs at the time. Since this is in Python,
I could use sqlite; I may also be able to get away with using just CSV. I'm not sure yet. Either way,
Postgresql is too much to ask other folks to download to calculate stats, I think, so it's going into the
"maybe support it later but probably not" bin.
-sorcrane 12/1/2022
"""
from configparser import ConfigParser
from postgresql.PostgresqlConnector import PostgresqlConnector

if __name__ == '__main__':
    config = ConfigParser.RawConfigParser()
    config.read('SETUP.INI')

    # postgresql
    hostname = config.get('database', 'hostname')
    username = config.get('database', 'username')
    password = config.get('database', 'password')
    database = config.get('database', 'database')
    db_connector = PostgresqlConnector(hostname, username, password, database)


    # After queues joined
    # db_connector.processPostgresql(ao3_lists, global_dict)
    db_connector.processPostgresql(ffn_lists.union(ao3_lists), global_dict)