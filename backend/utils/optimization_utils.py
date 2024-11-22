# backend/utils/optimization_utils.py

import time
import functools
from .logging_utils import configure_logging
from cachetools import TTLCache
import hashlib
import json
import threading
from collections import defaultdict
import asyncio

logger = configure_logging()

def log_execution_time(threshold=0.1):
    """
    A decorator that logs the execution time of the wrapped function if it exceeds a specified threshold.

    Args:
        threshold (float): The minimum execution time (in seconds) that will trigger a log entry.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            end_time = time.perf_counter()
            execution_time = end_time - start_time
            if execution_time > threshold:
                logger.info(f"Execution time of {func.__name__}: {execution_time:.4f} seconds")
            return result
        return wrapper
    return decorator

def retry_on_exception(max_retries=3, delay=2, exceptions=(Exception,)):
    """
    A decorator that retries the wrapped function if it raises an exception.

    Args:
        max_retries (int): The maximum number of retries.
        delay (int): The delay between retries in seconds.
        exceptions (tuple): A tuple of exception types to catch and retry.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    retries += 1
                    logger.warning(f"Exception occurred in {func.__name__}: {e}. Retrying {retries}/{max_retries}...")
                    if retries < max_retries:
                        time.sleep(delay * (2 ** (retries - 1)))  # Exponential backoff
            # If max retries are exceeded, raise the last exception
            raise e
        return wrapper
    return decorator

def handle_exceptions(default_return_value=None):
    """
    A decorator that handles exceptions raised by the wrapped function and logs the error.

    Args:
        default_return_value (any): The default value to return in case of an exception.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                logger.error(f"Exception occurred in {func.__name__}: {e}")
                return default_return_value
        return wrapper
    return decorator

def cache_result(ttl=60, maxsize=128):
    """
    A decorator that caches the result of the wrapped function for a specified time-to-live (TTL).

    Args:
        ttl (int): The time-to-live in seconds for the cache.
        maxsize (int): The maximum size of the cache.
    """
    cache = TTLCache(maxsize=maxsize, ttl=ttl)

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                key = hashlib.sha256(json.dumps((args, kwargs), sort_keys=True).encode()).hexdigest()
            except (TypeError, ValueError):
                logger.warning(f"Arguments for {func.__name__} are not serializable. Skipping caching.")
                return func(*args, **kwargs)

            if key in cache:
                logger.info(f"Cache hit for {func.__name__}")
                return cache[key]
            # Cache miss, call the function
            result = func(*args, **kwargs)
            cache[key] = result
            logger.info(f"Cache set for {func.__name__}")
            return result

        return wrapper
    return decorator

def rate_limiter(calls_per_second):
    """
    A decorator that limits the rate at which a function can be called.

    Args:
        calls_per_second (float): The number of allowed calls per second.
    """
    min_interval = 1.0 / calls_per_second

    def decorator(func):
        last_call = [0.0]

        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            elapsed = time.perf_counter() - last_call[0]
            wait = min_interval - elapsed
            if wait > 0:
                await asyncio.sleep(wait)
            last_call[0] = time.perf_counter()
            return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        return wrapper
    return decorator

def throttle(concurrent_calls=1):
    """
    A decorator to control the number of concurrent executions of a given function.

    Args:
        concurrent_calls (int): The maximum number of concurrent calls allowed.
    """
    semaphore = asyncio.Semaphore(concurrent_calls)

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            async with semaphore:
                return await func(*args, **kwargs) if asyncio.iscoroutinefunction(func) else func(*args, **kwargs)
        return wrapper
    return decorator

def timeout(seconds=10):
    """
    A decorator to add a timeout to a function. If the function takes longer than the specified duration, it will raise a TimeoutError.

    Args:
        seconds (int): The maximum time allowed for the function to run.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = [None]
            exception = [None]
            completed = [False]

            def target():
                try:
                    result[0] = func(*args, **kwargs)
                except Exception as e:
                    exception[0] = e
                finally:
                    completed[0] = True

            thread = threading.Thread(target=target)
            thread.start()
            thread.join(seconds)
            if not completed[0]:
                logger.error(f"Thread did not complete in time. Forcefully terminating {func.__name__}.")
                raise TimeoutError(f"Execution of {func.__name__} timed out after {seconds} seconds")
            if exception[0]:
                raise exception[0] from None
            return result[0]
        return wrapper
    return decorator

# Example Usage
if __name__ == "__main__":
    @log_execution_time(threshold=0.1)
    @retry_on_exception(max_retries=3, delay=1, exceptions=(ValueError,))
    @handle_exceptions(default_return_value=-1)
    @cache_result(ttl=10, maxsize=128)
    @rate_limiter(calls_per_second=2)
    @throttle(concurrent_calls=2)
    @timeout(seconds=5)
    async def sample_function(x):
        """A sample function to demonstrate the use of the decorators."""
        if x < 0:
            raise ValueError("Negative value not allowed.")
        await asyncio.sleep(1)  # Simulate a delay
        return x ** 2

    # Run sample function
    try:
        print(asyncio.run(sample_function(5)))
        print(asyncio.run(sample_function(-1)))  # This will trigger retries
    except ValueError as e:
        logger.error(f"Error: {e}")
    except TimeoutError as e:
        logger.error(f"Timeout: {e}")

    # Demonstrate caching
    print(asyncio.run(sample_function(5)))  # Cache hit
    asyncio.run(asyncio.sleep(11))
    print(asyncio.run(sample_function(5)))  # Cache expired, re-execute
