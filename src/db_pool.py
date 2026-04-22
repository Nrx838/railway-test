# Database connection pool (replaces per-request direct connections)
# See: docs/Database - Connection Management (OUTDATED - needs update)
import psycopg2.pool
import os

_pool = psycopg2.pool.ThreadedConnectionPool(
    minconn=2,
    maxconn=10,
    dsn=os.environ["DATABASE_URL"]
)

def get_conn():
    """Borrows a connection from the pool. Replaces psycopg2.connect() per request."""
    return _pool.getconn()

def release_conn(conn):
    """Returns connection to pool. Must be called after every get_conn()."""
    _pool.putconn(conn)

# NOTE: Per-request psycopg2.connect() / close_conn() pattern removed.
# All DB access must now use get_conn() / release_conn().
# Pool size: min=2, max=10. Configured via DATABASE_URL env var.
