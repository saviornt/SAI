# backend/memory/redis_handler.py

import time
from functools import wraps
from redis.exceptions import RedisError
from utils import configure_logging

# Configure logging
logger = configure_logging()

def cache_cleanup(cache, expiration_time):
    """
    Decorator to clean up expired cache entries before executing a function.

    Args:
        cache (dict): The cache dictionary to clean up.
        expiration_time (int): The cache expiration time in seconds.
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            current_time = time.time()
            expired_keys = [key for key, value in cache.items() if current_time - value["timestamp"] >= expiration_time]
            for key in expired_keys:
                del cache[key]
            return await func(*args, **kwargs)
        return wrapper
    return decorator

class RedisHandler:
    """
    A class to handle memory operations using Redis.

    This class provides methods to interact with Redis for storing and retrieving data.
    """
    def __init__(self, redis_pool):
        """
        Initialize the RedisHandler with a Redis connection pool.

        Args:
            redis_pool (aioredis.Redis): The Redis connection pool to be used.
        """
        self.redis = redis_pool

    async def set_value(self, key, value, expire_seconds=None):
        """
        Set a value in Redis with an optional expiration time.

        Args:
            key (str): The key under which the value should be stored.
            value (str): The value to store.
            expire_seconds (int, optional): The expiration time in seconds. Defaults to None.

        Returns:
            bool: True if the value was set successfully, False otherwise.
        """
        if not isinstance(key, str) or not key:
            logger.error("Invalid key: Key must be a non-empty string.")
            return False
        if not isinstance(value, str) or not value:
            logger.error("Invalid value: Value must be a non-empty string.")
            return False
        try:
            await self.redis.set(key, value, ex=expire_seconds)
            logger.info(f"Value set for key: {key}")
            return True
        except RedisError as e:
            logger.exception(f"Redis error occurred while setting value for key '{key}': {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while setting value for key '{key}': {e}")
            return False

    async def get_value(self, key):
        """
        Get a value from Redis by key.

        Args:
            key (str): The key whose value should be retrieved.

        Returns:
            str: The value associated with the key, or a default value of "" if not found.
        """
        if not isinstance(key, str) or not key:
            logger.error("Invalid key: Key must be a non-empty string.")
            return None
        try:
            value = await self.redis.get(key)
            if value is not None:
                logger.info(f"Value retrieved for key: {key}")
                return value
            else:
                logger.info(f"No value found for key: {key}")
                return ""
        except RedisError as e:
            logger.exception(f"Redis error occurred while getting value for key '{key}': {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while getting value for key '{key}': {e}")
            return None

    async def delete_key(self, key):
        """
        Delete a key from Redis.

        Args:
            key (str): The key to be deleted.

        Returns:
            bool: True if the key was deleted, False otherwise.
        """
        if not isinstance(key, str) or not key:
            logger.error("Invalid key: Key must be a non-empty string.")
            return False
        try:
            result = await self.redis.delete(key)
            if result > 0:
                logger.info(f"Key '{key}' deleted successfully.")
                return True
            else:
                logger.info(f"Key '{key}' not found for deletion.")
                return False
        except RedisError as e:
            logger.exception(f"Redis error occurred while deleting key '{key}': {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while deleting key '{key}': {e}")
            return False

    async def set_hash(self, name, key, value):
        """
        Set a field in a Redis hash.

        Args:
            name (str): The name of the hash.
            key (str): The field key within the hash.
            value (str): The value to set for the field.

        Returns:
            bool: True if the field was set successfully, False otherwise.
        """
        if not isinstance(name, str) or not name:
            logger.error("Invalid hash name: Name must be a non-empty string.")
            return False
        if not isinstance(key, str) or not key:
            logger.error("Invalid key: Key must be a non-empty string.")
            return False
        if not isinstance(value, str) or not value:
            logger.error("Invalid value: Value must be a non-empty string.")
            return False
        try:
            await self.redis.hset(name, key, value)
            logger.info(f"Field '{key}' set in hash '{name}'.")
            return True
        except RedisError as e:
            logger.exception(f"Redis error occurred while setting hash field '{key}' in '{name}': {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while setting hash field '{key}' in '{name}': {e}")
            return False

    async def get_hash(self, name, key):
        """
        Get a field value from a Redis hash.

        Args:
            name (str): The name of the hash.
            key (str): The field key within the hash.

        Returns:
            str: The value of the hash field, or a default value of "" if not found.
        """
        if not isinstance(name, str) or not name:
            logger.error("Invalid hash name: Name must be a non-empty string.")
            return None
        if not isinstance(key, str) or not key:
            logger.error("Invalid key: Key must be a non-empty string.")
            return None
        try:
            value = await self.redis.hget(name, key)
            if value is not None:
                logger.info(f"Field '{key}' retrieved from hash '{name}'.")
                return value
            else:
                logger.info(f"Field '{key}' not found in hash '{name}'.")
                return ""
        except RedisError as e:
            logger.exception(f"Redis error occurred while getting hash field '{key}' from '{name}': {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while getting hash field '{key}' from '{name}': {e}")
            return None

    async def delete_hash_field(self, name, key):
        """
        Delete a field from a Redis hash.

        Args:
            name (str): The name of the hash.
            key (str): The field key within the hash.

        Returns:
            bool: True if the field was deleted, False otherwise.
        """
        if not isinstance(name, str) or not name:
            logger.error("Invalid hash name: Name must be a non-empty string.")
            return False
        if not isinstance(key, str) or not key:
            logger.error("Invalid key: Key must be a non-empty string.")
            return False
        try:
            result = await self.redis.hdel(name, key)
            if result > 0:
                logger.info(f"Field '{key}' deleted from hash '{name}'.")
                return True
            else:
                logger.info(f"Field '{key}' not found in hash '{name}' for deletion.")
                return False
        except RedisError as e:
            logger.exception(f"Redis error occurred while deleting hash field '{key}' from '{name}': {e} (type: {type(e).__name__})")
            return False
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while deleting hash field '{key}' from '{name}': {e} (type: {type(e).__name__})")
            return False