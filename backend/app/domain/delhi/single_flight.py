"""Single-flight guard for the expensive process-wide structure builders.

Why this exists
---------------
The Delhi model caches its heavy static structures with
``functools.lru_cache(maxsize=1)`` (road graph, surface/DEM structure, curb
inlet index, road-to-cell match index). ``lru_cache`` is thread-safe for its
own bookkeeping but it does NOT serialise the wrapped call: on a cold cache,
every concurrent caller runs the FULL build. The FastAPI endpoints are
synchronous (``def``), so uvicorn dispatches them on a threadpool and a
burst of first-touch dashboard requests really do execute in parallel —
measured at 722-753 MB peak against Render's 512 MB free-tier limit, i.e.
N simultaneous copies of a ~100 MB structure.

The fix is deliberately narrow: one lock PER builder, and only around the
cold build. A warm request never touches a lock (it is rejected by the
``cache_info()`` fast path), so normal traffic is untouched. Builders form a
DAG (match index -> graph + surface; inlet index -> surface; graph and
surface are leaves), and the lock is reentrant, so nested builds on the same
thread cannot self-deadlock while a leaf builder never waits on anything.
"""
from __future__ import annotations

import functools
import threading
from functools import lru_cache
from typing import Callable, TypeVar

T = TypeVar("T")


def single_flight_cached(builder: Callable[..., T]) -> Callable[..., T]:
    """Wrap a zero/low-arg expensive builder in an lru cache plus a lock.

    The returned callable keeps the ``lru_cache`` management surface used by
    the app and the tests (``cache_info``, ``cache_clear``,
    ``cache_parameters``) so existing cache introspection keeps working.
    """
    cached = lru_cache(maxsize=1)(builder)
    lock = threading.RLock()

    @functools.wraps(builder)
    def wrapper(*args, **kwargs):  # noqa: ANN001 - mirrors the builder
        if cached.cache_info().currsize:
            # Warm cache: no lock, same speed as a plain lru_cache hit.
            return cached(*args, **kwargs)
        with lock:
            # Exactly one thread builds; the others arrive here after it
            # finished and get the cached object (lru_cache re-checks).
            return cached(*args, **kwargs)

    wrapper.cache_info = cached.cache_info          # type: ignore[attr-defined]
    wrapper.cache_clear = cached.cache_clear        # type: ignore[attr-defined]
    wrapper.cache_parameters = cached.cache_parameters  # type: ignore[attr-defined]
    return wrapper
