# WIP: Redis cache layer (not ready for review)
import redis

r = redis.Redis(host='localhost')

def get_cached(key: str):
    # TODO: add TTL, serialization, error handling
    return r.get(key)
