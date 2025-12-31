import time
import functools
import logging

# Configure basic logging if not already configured
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("metrics")

import asyncio

def time_execution(func):
    """
    Decorator to measure and log the execution time of a function.
    Supports both synchronous and asynchronous functions.
    """
    if asyncio.iscoroutinefunction(func):
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                duration = end_time - start_time
                logger.info(f"Function '{func.__name__}' execution time: {duration:.6f} seconds")
        return async_wrapper
    else:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.perf_counter()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                end_time = time.perf_counter()
                duration = end_time - start_time
                logger.info(f"Function '{func.__name__}' execution time: {duration:.6f} seconds")
        return wrapper
