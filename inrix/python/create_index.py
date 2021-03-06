#!/usr/bin/python3
'''Create indexes for each table in the Inrix database.'''
import logging
from psycopg2 import connect

def get_yyyymm(yyyy, mm):
    '''Combine integer yyyy and mm into a string yyyymm.'''
    if mm < 10:
        return str(yyyy)+'0'+str(mm)
    else:
        return str(yyyy)+str(mm)

def _index_table(yyyymm, logger, con, cursor):
    '''Create indexes on the inrix.raw_data partitioned table with yyyymm.'''
    table = 'inrix.raw_data'+yyyymm
    logger.info('Creating indexes on table %s', table)

    logger.info('Creating score index')
    cursor.execute("CREATE INDEX ON {table}(score);".format(table=table))

    logger.info('Creating tmc index')
    cursor.execute("CREATE INDEX ON {table}(tmc);".format(table=table))

    logger.info('Creating timestamp index')
    #Reducing timestamp index size by applying it only to rows
    #where the speed record is based on observed data (score=30)
    cursor.execute("CREATE INDEX ON {table}(tx) WHERE score = 30;".format(table=table))


def index_tables(years, dbset, logger):
    '''Create indexes for a series of tables based on the years dictionary \
    and the dbset database connection.'''

    logger.info('Connecting to host:%s database: %s with user %s',
                dbset['database'],
                dbset['host'],
                dbset['user'])
    con = connect(database=dbset['database'],
                  host=dbset['host'],
                  user=dbset['user'],
                  password=dbset['password'])
    #Necessary for index building
    con.autocommit=True
    
    cursor = con.cursor()

    for year in years:
        for month in years[year]:
            yyyymm = get_yyyymm(year, month)
            
            #Execution retry loop
            while True:
                #Connection retry loop
                while True:
                    try:
                        logger.info('Testing Connection')
                        cursor.execute('SELECT 1')
                    except OperationalError as oe:
                        logger.error(oe)
                        logger.info('Retrying connection in 2 minutes')
                        sleep(120)
                        con = connect(database=dbset['database'],
                                      host=dbset['host'],
                                      user=dbset['user'],
                                      password=dbset['password'])
                        cursor = con.cursor()
                    else:
                        break
                
                try:
                    _index_table(yyyymm, logger, con, cursor)
                except OperationalError as oe:
                    logger.error(oe)
                else:
                    break

    con.close()
    logger.info('Processing complete, connection to %s database %s closed',
                dbset['host'],
                dbset['database'])

    con.close()

if __name__ == "__main__":
    #For initial run, creating years and months of available data as a python dictionary
    #YEARS = {#"2012":range(7, 13),
     #        "2013":range(1, 13)},
#             "2016":range(1, 7),
#             "2014":range(1, 13),             
#             "2015":range(1, 13)}
    '''Phase 1'''
    YEARS = {"2011":range(8,13),
             "2013":range(7,13)}
    #Configure logging
    FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(level=logging.INFO, format=FORMAT)
    LOGGER = logging.getLogger(__name__)
    from dbsettings import dbsetting
    index_tables(YEARS, dbsetting, LOGGER)
