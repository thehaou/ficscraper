import psycopg2


class PostgresqlConnector:
    def __init__(self, hostname, username, password, database):
        self._hostname = hostname
        self._username = username
        self._password = password
        self._database = database

    def processPostgresql(self, lists, insert_dict):
        perform_postgresql = True

        # postgresql
        print '\n'
        print '+ ---------------------- +'
        print '|       Postgresql       |'
        print '+ ---------------------- +'

        # postgresql perform
        if perform_postgresql:
            for list_name in lists:
                print 'list name is ' + list_name
                if list_name in insert_dict:
                    self.performPostgresql(insert_dict.get(list_name))
                else:
                    print 'list name ' + list_name + ' is not in the dictionary'

    def performPostgresql(self, row_list):
        conn = self.getPostgresqlConnection()

        for row in row_list:
            self.doInsert(conn, row)

        # Close communication with the _database
        self.shutdownConnection(conn)

    def getPostgresqlConnection(self):
        print 'database: ' + self._database

        # Connect to an existing _database
        return psycopg2.connect(host=self._hostname, user=self._username, password=self._password,
                                dbname=self._database)

    def doInsert(self, conn, insert_object):
        print 'work_id...' + insert_object._work_id
        print 'trying to add new ' + repr(insert_object)

        # Open a cursor to perform _database operations
        cur = conn.cursor()

        # Pass data to fill a query placeholders and let Psycopg perform
        # the correct conversion (no more SQL injections!)
        try:
            cur.execute(insert_object.get_insert_query(), insert_object.get_insert_tuple())
        except psycopg2.IntegrityError as e:
            print e.message
            print 'shutting down cursor'
            self.shutdownCursor(cur)
            return

        # Make the changes to the _database persistent
        conn.commit()

        # Close communication with the _database
        self.shutdownCursor(cur)

        print 'added ' + repr(insert_object)

    def shutdownCursor(self, curr):
        curr.close()

    def shutdownConnection(self, conn):
        conn.close()
