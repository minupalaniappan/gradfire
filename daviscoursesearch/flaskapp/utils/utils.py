from datetime import datetime
from itertools import islice, filterfalse
from functools import wraps
from ...common import constants as const
from ...common import logging
from ...common import config
from .db_utils import redis_conn
from ..root import log_exception_to_sentry
import json
import redis
import re
import time
import pickle

def _subjectNumberPairsForCourses(courses):
 return ['{0} {1}'.format(course['subject'], course['number']) for course in courses]

class SchemaEncoder(json.JSONEncoder):
    """Encoder for converting Model objects into JSON."""

    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
        elif isinstance(obj, Model):
            return obj.__json__()
        return json.JSONEncoder.default(self, obj)

def stringify_obj_for_json(course):
  for key, value in course.items():
    if isinstance(value, datetime):
      date = value
      # Iso 8601
      course[key] = date.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
    elif isinstance(value, list):
      for item in value:
        if isinstance(item, dict):
          stringify_obj_for_json(item)
    elif isinstance(value, dict):
      course[key] = stringify_obj_for_json(value)

  return course

def timeit(method):

    def timed(*args, **kw):
        ts = time.time()
        result = method(*args, **kw)
        te = time.time()

        print('%r (%r, %r) %2.2f sec' % \
              (method.__name__, args, kw, te-ts))
        return result

    return timed

def uniq_by_key(list_dicts, dict_key):
    """
    http://stackoverflow.com/questions/4370660/unique-list-of-dicts-based-on-keys
    """
    seen = set()

    return [seen.add(obj[dict_key]) or obj for obj in list_dicts if obj[dict_key] not in seen]

def split_and_strip_nonalpha(text):
    """
    'HELLO$ my name IS #andy' -> ['hello', 'my', 'name',  'is',  'andy']
    """
    text_stripped = [re.sub(r'[^A-Za-z0-9]', '', kw.lower()) for kw in text.split()]
    return [kw for kw in text_stripped if kw]

def window(seq, n=2):
    "Returns a sliding window (of width n) over data from the iterable"
    "   s -> (s0,s1,...s[n-1]), (s1,s2,...,sn), ...                   "
    "https://docs.python.org/release/2.3.5/lib/itertools-example.html"
    it = iter(seq)
    result = tuple(islice(it, n))
    if len(result) == n:
        yield result
    for elem in it:
        result = result[1:] + (elem,)
        yield result

def unique_everseen(iterable, key=None):
    "List unique elements, preserving order. Remember all elements ever seen."
    # unique_everseen('AAAABBBCCDAABBB') --> A B C D
    # unique_everseen('ABBCcAD', str.lower) --> A B C D
    seen = set()
    seen_add = seen.add
    if key is None:
        for element in filterfalse(seen.__contains__, iterable):
            seen_add(element)
            yield element
    else:
        for element in iterable:
            k = key(element)
            if k not in seen:
                seen_add(k)
                yield element

def next_term(term_year, term_month):
    try:
        next_month = next(key for key in const.TERM_SESSION_BY_MONTH.keys() if key > term_month)
        return (term_year, next_month)
    except StopIteration:
        return (term_year + 1, min(const.TERM_SESSION_BY_MONTH.keys()))

def previous_term(term_year, term_month):
    try:
        months_desc = list(const.TERM_SESSION_BY_MONTH.keys())
        months_desc.reverse()
        prev_month = next(key for key in months_desc if key < term_month)
        return (term_year, prev_month)
    except StopIteration:
        return (term_year - 1, max(const.TERM_SESSION_BY_MONTH.keys()))

def term_range(start_term, end_term):
    term = start_term
    while term <= end_term:
        yield term
        term = next_term(*term)

NUMERIC_DAY_BY_LETTER = {
    'M': 0,
    'T': 1,
    'W': 2,
    'R': 3,
    'F': 4,
    'S': 5
}

RRULE_DAY_BY_LETTER = {
    'M': 'MO',
    'T': 'TU',
    'W': 'WE',
    'R': 'TH',
    'F': 'FR'
}

def format_units(units_low, units_hi):
    if not units_low and not units_hi:
        return

    if units_low and isinstance(units_low, float) and units_low.is_integer():
        units_low = int(units_low)
    if units_hi and isinstance(units_hi, float) and units_hi.is_integer():
        units_hi = int(units_hi)

    if units_low == units_hi:
        return str(units_low)
    else:
        return '{}-{}'.format(units_low, units_hi)

def redis_lru(capacity=5000, slice=slice(None)):
    """
    Simple Redis-based LRU cache decorator *.
    *conn*      Redis connection
    *capacity*  maximum number of entries in LRU cache
    *slice*    slice object for restricting prototype args

    Usage is as simple as prepending the decorator to a function,
    passing a Redis connection object, and the desired capacity
    of your cache.

    @redis_lru(capacity=10000)
    def func(foo, bar):
        # some expensive operation
        return baz

    Uses 4 Redis keys, all suffixed with the function name:
        lru:keys: - sorted set, stores hash keys
        lru:vals: - hash, stores function output values
        lru:hits: - string, stores hit counter
        lru:miss: - string, stores miss counter

    * Functions prototypes must be serializable equivalent!
    """
    def decorator(func):
        cache_keys = "lru:keys:%s" % (func.__name__,)
        cache_vals = "lru:vals:%s" % (func.__name__,)
        cache_hits = "lru:hits:%s" % (func.__name__,)
        cache_miss = "lru:miss:%s" % (func.__name__,)

        def add(key, value):
            try:
                eject()
            except redis.exceptions.RedisError as e:
                log_exception_to_sentry()
                logging.exception_logger.exception('Redis error')
                return value
            redis_conn.incr(cache_miss)
            redis_conn.hset(cache_vals, key, pickle.dumps(value))
            redis_conn.zadd(cache_keys, 0, key)
            return value

        def get(key):
            value = redis_conn.hget(cache_vals, key)
            if value:
                redis_conn.incr(cache_hits)
                redis_conn.zincrby(cache_keys, key, 1.0)
                value = pickle.loads(value)
            return value

        def eject():
            count = min((capacity // 10) or 1, 1000)
            if redis_conn.zcard(cache_keys) >= capacity:
                eject = redis_conn.zrange(cache_keys, 0, count)
                redis_conn.zremrangebyrank(cache_keys, 0, count)
                redis_conn.hdel(cache_vals, *eject)

        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                if not config.debug:
                    items = args + tuple(sorted(kwargs.items()))
                    key = pickle.dumps(items[slice])
                    return get(key) or add(key, func(*args, **kwargs))
            except redis.exceptions.RedisError as e:
                log_exception_to_sentry()
            return func(*args, **kwargs)

        def info():
            size = int(redis_conn.zcard(cache_keys) or 0)
            hits, misses = int(redis_conn.get(cache_hits) or 0), int(redis_conn.get(cache_miss) or 0)
            return hits, misses, capacity, size

        def clear():
            redis_conn.delete(cache_keys, cache_vals)
            redis_conn.delete(cache_hits, cache_miss)

        wrapper.info = info
        wrapper.clear = clear
        return wrapper
    return decorator
