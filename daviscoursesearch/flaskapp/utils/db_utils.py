from ...common import config
import psycopg2

conn = psycopg2.connect("dbname={}".format(config.db_name))
conn.autocommit = True

import redis
redis_conn = redis.StrictRedis(host=config.redis_host, password=config.redis_password)

# Debug logging to print queries from all cursors
# from psycopg2.extras import LoggingConnection
# import logging

# logging.basicConfig(level=logging.DEBUG)
# logger = logging.getLogger(__name__)

# conn = psycopg2.connect("dbname={}".format(config.db_name), connection_factory=LoggingConnection)
# conn.initialize(logger)
