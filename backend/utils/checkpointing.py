# backend/utils/checkpointing.py

import asyncio
import random
import json
import time
from utils import configure_logging, generate_timestamp
from memory import MemoryManagement, cache_cleanup
from files import FileOperations
from redis import RedisError


# Configure logging
logger = configure_logging()

def validate_checkpoint_data(checkpoint):
    """
    Validate the structure of checkpoint data.

    Args:
        checkpoint (dict): The checkpoint data to validate.

    Returns:
        bool: True if the checkpoint data is valid, False otherwise.
    """
    return (
        isinstance(checkpoint, dict) and
        "name" in checkpoint and
        "timestamp" in checkpoint and
        "state_data" in checkpoint
    )

class Checkpointing:
    """
    A class to handle checkpointing operations for the system.

    This class provides methods to create, store, and load checkpoints to save the state of the system
    at different stages of execution.
    """
    def __init__(self, cache_expiration_time=300):
        """
        Initialize the Checkpointing class with the MemoryManagement instance.

        Args:
            cache_expiration_time (int): Cache expiration time in seconds (default: 300).
        """
        self.memory = MemoryManagement()
        self.file_operations = FileOperations()
        self.checkpoint_cache = {}
        self.cache_expiration_time = cache_expiration_time

    @cache_cleanup(cache="self.checkpoint_cache", expiration_time="self.cache_expiration_time")
    async def create_checkpoint(self, checkpoint_name, state_data):
        """
        Create and store a checkpoint with the given state data.

        Args:
            checkpoint_name (str): The name of the checkpoint.
            state_data (dict): The state data to be saved as part of the checkpoint.

        Returns:
            bool: True if the checkpoint was stored successfully, False otherwise.
        """
        try:
            logger.info(f"Creating checkpoint '{checkpoint_name}' with state data.")
            timestamp = await generate_timestamp()
            checkpoint = {
                "name": checkpoint_name,
                "timestamp": timestamp,
                "state_data": state_data
            }
            try:
                checkpoint_str = json.dumps(checkpoint)
            except TypeError as e:
                logger.error(f"Failed to serialize state data for checkpoint '{checkpoint_name}': {e}")
                return False

            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    success = await self.memory.store_data(checkpoint_name, checkpoint_str)
                    if success:
                        # Update cache with new checkpoint
                        self.checkpoint_cache[checkpoint_name] = {
                            "timestamp": time.time(),
                            "data": checkpoint_str
                        }
                        logger.info(f"Checkpoint '{checkpoint_name}' created successfully.")
                        return True
                except (ConnectionError, RedisError) as conn_error:
                    logger.warning(f"Connection error on attempt {attempt + 1} to store checkpoint '{checkpoint_name}': {conn_error}")
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} to store checkpoint '{checkpoint_name}' failed: {e}")
                backoff_time = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff with jitter
                await asyncio.sleep(backoff_time)
            logger.error(f"Failed to create checkpoint '{checkpoint_name}' after multiple attempts.")
            return False
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while creating checkpoint '{checkpoint_name}': {e}")
            return False

    @cache_cleanup(cache="self.checkpoint_cache", expiration_time="self.cache_expiration_time")
    async def load_checkpoint(self, checkpoint_name):
        """
        Load a checkpoint by its name.

        Args:
            checkpoint_name (str): The name of the checkpoint to load.

        Returns:
            dict: The loaded checkpoint data, or None if the checkpoint could not be loaded.
        """
        try:
            logger.info(f"Loading checkpoint '{checkpoint_name}'.")

            # Check if the checkpoint is in the cache and still valid
            if checkpoint_name in self.checkpoint_cache:
                cache_entry = self.checkpoint_cache[checkpoint_name]
                logger.info(f"Loaded checkpoint '{checkpoint_name}' from cache.")
                checkpoint = json.loads(cache_entry["data"])
                return checkpoint

            max_attempts = 3
            for attempt in range(max_attempts):
                try:
                    checkpoint_str = await self.memory.retrieve_data(checkpoint_name)
                    if checkpoint_str is not None:
                        break
                except (ConnectionError, RedisError) as conn_error:
                    logger.warning(f"Connection error on attempt {attempt + 1} to retrieve checkpoint '{checkpoint_name}': {conn_error}")
                except Exception as e:
                    logger.warning(f"Attempt {attempt + 1} to retrieve checkpoint '{checkpoint_name}' failed: {e}")
                backoff_time = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff with jitter
                await asyncio.sleep(backoff_time)
            else:
                logger.error(f"Checkpoint '{checkpoint_name}' not found after multiple attempts. It may have been deleted or never created.")
                return None

            try:
                checkpoint = json.loads(checkpoint_str)
                if not validate_checkpoint_data(checkpoint):
                    raise ValueError(f"Checkpoint data for '{checkpoint_name}' is corrupted or not in the expected format.")
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"Failed to load checkpoint '{checkpoint_name}': {e}. The data might be corrupted.")
                return None

            # Update cache with loaded checkpoint
            self.checkpoint_cache[checkpoint_name] = {
                "timestamp": time.time(),
                "data": checkpoint_str
            }

            logger.info(f"Checkpoint '{checkpoint_name}' loaded successfully.")
            return checkpoint
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while loading checkpoint '{checkpoint_name}': {e}")
            return None

    @cache_cleanup(cache="self.checkpoint_cache", expiration_time="self.cache_expiration_time")
    async def delete_checkpoint(self, checkpoint_name):
        """
        Delete a checkpoint by its name.

        Args:
            checkpoint_name (str): The name of the checkpoint to delete.

        Returns:
            bool: True if the checkpoint was deleted successfully, False otherwise.
        """
        try:
            logger.info(f"Deleting checkpoint '{checkpoint_name}'.")
            success = await self.memory.delete_data(checkpoint_name)
            if success:
                # Remove from cache if present
                if checkpoint_name in self.checkpoint_cache:
                    del self.checkpoint_cache[checkpoint_name]
                logger.info(f"Checkpoint '{checkpoint_name}' deleted successfully.")
            else:
                logger.error(f"Failed to delete checkpoint '{checkpoint_name}'. It may not exist.")
            return success
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while deleting checkpoint '{checkpoint_name}': {e}")
            return False

    async def list_checkpoints(self, page_size=10, page_number=1):
        """
        List available checkpoints with pagination support.

        Args:
            page_size (int): The number of checkpoints per page.
            page_number (int): The page number to retrieve.

        Returns:
            list: A list of checkpoint names for the specified page.
        """
        try:
            logger.info(f"Listing checkpoints for page {page_number} with page size {page_size}.")
            keys = await self.memory.list_keys(prefix="checkpoint_")
            start_index = (page_number - 1) * page_size
            end_index = start_index + page_size
            checkpoints = list(keys)[start_index:end_index]
            logger.info(f"Found {len(checkpoints)} checkpoints on page {page_number}.")
            return checkpoints
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while listing checkpoints: {e}")
            return []

    async def save_checkpoint_to_file(self, checkpoint_name, file_path):
        """
        Save a checkpoint to a file for backup purposes.

        Args:
            checkpoint_name (str): The name of the checkpoint to save.
            file_path (str): The file path where the checkpoint should be saved.

        Returns:
            bool: True if the checkpoint was saved to file successfully, False otherwise.
        """
        try:
            logger.info(f"Saving checkpoint '{checkpoint_name}' to file '{file_path}'.")
            checkpoint = await self.load_checkpoint(checkpoint_name)
            if checkpoint is None:
                logger.error(f"Failed to load checkpoint '{checkpoint_name}' for saving to file. The checkpoint might be missing or corrupted.")
                return False
            success = await self.file_operations.save_file(file_path, checkpoint)
            if success:
                logger.info(f"Checkpoint '{checkpoint_name}' saved to file '{file_path}' successfully.")
            return success
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while saving checkpoint '{checkpoint_name}' to file '{file_path}': {e}")
            return False

    async def load_checkpoint_from_file(self, file_path):
        """
        Load a checkpoint from a file.

        Args:
            file_path (str): The file path from which to load the checkpoint.

        Returns:
            dict: The loaded checkpoint data, or None if the file could not be read.
        """
        try:
            logger.info(f"Loading checkpoint from file '{file_path}'.")
            checkpoint = await self.file_operations.load_file(file_path)
            if checkpoint is None or not validate_checkpoint_data(checkpoint):
                logger.error(f"Checkpoint data from file '{file_path}' is corrupted or not in the expected format.")
                return None
            logger.info(f"Checkpoint loaded from file '{file_path}' successfully.")
            return checkpoint
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while loading checkpoint from file '{file_path}': {e}")
            return None

    async def delete_checkpoint_file(self, file_path):
        """
        Delete a checkpoint file.

        Args:
            file_path (str): The file path of the checkpoint to delete.

        Returns:
            bool: True if the file was deleted successfully, False otherwise.
        """
        try:
            logger.info(f"Deleting checkpoint file '{file_path}'.")
            success = await self.file_operations.delete_file(file_path)
            if success:
                logger.info(f"Checkpoint file '{file_path}' deleted successfully.")
            else:
                logger.error(f"Failed to delete checkpoint file '{file_path}'. The file may not exist or may be locked.")
            return success
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while deleting checkpoint file '{file_path}': {e}")
            return False
