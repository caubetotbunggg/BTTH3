import redis
import json

CACHE_TTL = 300

redis_client = redis.Redis(host="redis", port=6379, db=0)

def get_cache(key: str):
    value = redis_client.get(key)
    if value:
        return json.loads(value)
    return None

def set_cache(key: str, value: dict):
    redis_client.setex(key, CACHE_TTL, json.dumps(value))
