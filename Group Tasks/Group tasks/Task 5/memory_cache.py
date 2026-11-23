"""In-process session memory and response cache; reset on server restart."""
from collections import OrderedDict
from threading import RLock
import hashlib
import json

_lock = RLock()
_sessions = OrderedDict()
_cache = OrderedDict()
_revision = 0
MAX_MESSAGES = 20
MAX_CACHE = 128
MAX_SESSIONS = 128


def get_history(session_id):
    with _lock:
        return [dict(item) for item in _sessions.get(session_id, [])]


def remember(session_id, question, answer):
    with _lock:
        history = _sessions.setdefault(session_id, [])
        _sessions.move_to_end(session_id)
        history.extend([{"role": "user", "content": question},
                        {"role": "assistant", "content": answer}])
        del history[:-MAX_MESSAGES]
        if len(_sessions) > MAX_SESSIONS:
            _sessions.popitem(last=False)


def cache_key(question, history):
    with _lock:
        rev = _revision
    payload = json.dumps([rev, question, history], ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()


def get_cached(key):
    with _lock:
        if key not in _cache:
            return None
        _cache.move_to_end(key)
        return dict(_cache[key])


def put_cached(key, value):
    with _lock:
        _cache[key] = dict(value)
        _cache.move_to_end(key)
        if len(_cache) > MAX_CACHE:
            _cache.popitem(last=False)


def invalidate_cache():
    global _revision
    with _lock:
        _revision += 1
        _cache.clear()


def clear_session(session_id):
    with _lock:
        _sessions.pop(session_id, None)
