# backend/memory/memory_management.py

from redis.exceptions import RedisError
from database import redis_pool
from utils import configure_logging

# Configure logging
logger = configure_logging()

def validate_key(key, name='key'):
    """
    Validate that the provided key is a non-empty string.

    Args:
        key (str): The key to validate.
        name (str): The name of the key (for error messages).

    Returns:
        bool: True if the key is valid, False otherwise.
    """
    if not isinstance(key, str) or not key:
        logger.error(f"Invalid {name}: {name} must be a non-empty string.")
        return False
    return True

class MemoryManagement:
    """
    A class to handle memory management using Redis.

    This class provides higher-level methods to interact with Redis for memory storage and retrieval operations.
    """
    def __init__(self):
        """
        Initialize the MemoryManagement class with the Redis connection pool.
        """
        self.redis = redis_pool

    async def store_data(self, key, value, expire_seconds=None):
        """
        Store data in Redis with an optional expiration time.

        Args:
            key (str): The key under which the value should be stored.
            value (str): The value to store.
            expire_seconds (int, optional): The expiration time in seconds. Defaults to None.

        Returns:
            bool: True if the value was set successfully, False otherwise.
        """
        if not validate_key(key) or not validate_key(value, name='value'):
            return False
        try:
            await self.redis.set(key, value, ex=expire_seconds, timeout=5)
            logger.info(f"Data stored with key: {key}")
            return True
        except RedisError as e:
            logger.exception(f"Redis error occurred while storing data for key '{key}': {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while storing data for key '{key}': {e}")
            return False

    async def retrieve_data(self, key):
        """
        Retrieve data from Redis by key.

        Args:
            key (str): The key whose value should be retrieved.

        Returns:
            str: The value associated with the key, or a default value of "" if not found.
        """
        if not validate_key(key):
            return None
        try:
            value = await self.redis.get(key, timeout=5)
            if value is not None:
                logger.info(f"Data retrieved for key: {key}")
                return value
            else:
                logger.info(f"No data found for key: {key}")
                return ""
        except RedisError as e:
            logger.exception(f"Redis error occurred while retrieving data for key '{key}': {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while retrieving data for key '{key}': {e}")
            return None

    async def delete_data(self, key):
        """
        Delete data from Redis by key.

        Args:
            key (str): The key to be deleted.

        Returns:
            bool: True if the key was deleted, False otherwise.
        """
        if not validate_key(key):
            return False
        try:
            result = await self.redis.delete(key, timeout=5)
            if result > 0:
                logger.info(f"Data with key '{key}' deleted successfully.")
                return True
            else:
                logger.info(f"No data found for key '{key}' to delete.")
                return False
        except RedisError as e:
            logger.exception(f"Redis error occurred while deleting data for key '{key}': {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while deleting data for key '{key}': {e}")
            return False

    async def store_hash_data(self, name, key, value):
        """
        Store a field in a Redis hash.

        Args:
            name (str): The name of the hash.
            key (str): The field key within the hash.
            value (str): The value to set for the field.

        Returns:
            bool: True if the field was set successfully, False otherwise.
        """
        if not validate_key(name, name='hash name') or not validate_key(key) or not validate_key(value, name='value'):
            return False
        try:
            await self.redis.hset(name, key, value, timeout=5)
            logger.info(f"Data stored in hash '{name}' with field '{key}'.")
            return True
        except RedisError as e:
            logger.exception(f"Redis error occurred while storing hash field '{key}' in '{name}': {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while storing hash field '{key}' in '{name}': {e}")
            return False

    async def retrieve_hash_data(self, name, key):
        """
        Retrieve a field value from a Redis hash.

        Args:
            name (str): The name of the hash.
            key (str): The field key within the hash.

        Returns:
            str: The value of the hash field, or a default value of "" if not found.
        """
        if not validate_key(name, name='hash name') or not validate_key(key):
            return None
        try:
            value = await self.redis.hget(name, key, timeout=5)
            if value is not None:
                logger.info(f"Data retrieved from hash '{name}' with field '{key}'.")
                return value
            else:
                logger.info(f"No data found in hash '{name}' for field '{key}'.")
                return ""
        except RedisError as e:
            logger.exception(f"Redis error occurred while retrieving hash field '{key}' from '{name}': {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while retrieving hash field '{key}' from '{name}': {e}")
            return None
