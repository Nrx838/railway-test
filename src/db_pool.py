# DB connection pooling
import psycopg2.pool

pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=2,
    maxconn=10,
    dsn='postgresql://localhost/app'
)

def get_conn():
    return pool.getconn()

def release_conn(conn):
    pool.putconn(conn)
