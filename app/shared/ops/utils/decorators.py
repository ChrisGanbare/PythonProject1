"""Shared decorators for retry and execution logging."""

from __future__ import annotations

import functools
import logging
import time
from typing import Callable, Iterable, Type


def retry(
    max_attempts: int = 3,
    backoff_factor: float = 2.0,
    exceptions: Iterable[Type[BaseException]] = (Exception,),
):
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = 1.0
            last_exc: BaseException | None = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except tuple(exceptions) as exc:
                    last_exc = exc
                    if attempt == max_attempts:
                        break
                    time.sleep(delay)
                    delay *= backoff_factor

            raise last_exc  # type: ignore[misc]

        return wrapper

    return decorator


def log_execution(log_level: str = "info"):
    def decorator(func: Callable):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            logger = logging.getLogger(func.__module__)
            level = getattr(logging, log_level.upper(), logging.INFO)
            logger.log(level, "start %s", func.__name__)
            try:
                result = func(*args, **kwargs)
                logger.log(level, "finish %s", func.__name__)
                return result
            except Exception:
                logger.exception("error in %s", func.__name__)
                raise

        return wrapper

    return decorator
