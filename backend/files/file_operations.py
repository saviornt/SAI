# backend/files/file_operations.py

import os
import logging
import asyncio
import aiofiles
import tempfile
import shutil
from files import file_handler

logger = logging.getLogger(__name__)

class FileOperations:
    def __init__(self):
        pass

    async def file_exists(self, file_path: str) -> bool:
        """
        Check if a file exists.

        Args:
            file_path (str): The file path to check.

        Returns:
            bool: True if the file exists, False otherwise.
        """
        return os.path.isfile(file_path)

    async def validate_filepath(self, filepath: str) -> bool:
        """
        Validate the file path.

        Args:
            filepath (str): The file path to validate.

        Returns:
            bool: True if the filepath is valid, False otherwise.
        """
        try:
            if not filepath or not isinstance(filepath, str):
                logger.error("Invalid file path: must be a non-empty string.")
                return False
            parent_dir = os.path.dirname(filepath)
            if parent_dir and not os.path.exists(parent_dir):
                logger.error(f"Directory does not exist for file path: {filepath}")
                return False
            return True
        except Exception as e:
            logger.exception(f"Unexpected error occurred during filepath validation: {e}")
            return False

    async def validate_permissions(self, filepath: str, mode: str = 'w') -> bool:
        """
        Validate file operation permissions.

        Args:
            filepath (str): The file path to validate permissions for.
            mode (str): The mode to validate, such as 'r' for read or 'w' for write (default: 'w').

        Returns:
            bool: True if the permissions are valid, False otherwise.
        """
        try:
            if mode not in ['r', 'w']:
                logger.error(f"Invalid mode '{mode}': must be 'r' or 'w'.")
                return False
            if mode == 'w':
                try:
                    with open(filepath, mode='a'):
                        pass
                except IOError:
                    logger.error(f"No write permission for directory: {os.path.dirname(filepath)}")
                    return False
            elif mode == 'r':
                try:
                    with open(filepath, mode='r'):
                        pass
                except IOError:
                    logger.error(f"No read permission for file: {filepath}")
                    return False
            return True
        except Exception as e:
            logger.exception(f"Unexpected error occurred during permission validation: {e}")
            return False

    async def validate_file_contents(self, file_path: str, retry_count: int = 3) -> bool:
        """
        Validate that the file content is not empty or corrupted.

        Args:
            file_path (str): The file path to validate.
            retry_count (int): The number of retry attempts in case of a timeout (default: 3).

        Returns:
            bool: True if the file content is valid, False otherwise.
        """
        try:
            if not await self.validate_file_path_and_permissions(file_path, mode='r'):
                return False

            while retry_count > 0:
                try:
                    async with aiofiles.open(file_path, mode='r', encoding='utf-8') as file:
                        content = await file.read()
                        if not content:
                            logger.error(f"File '{file_path}' is empty.")
                            return False
                    return True
                except asyncio.TimeoutError:
                    retry_count -= 1
                    if retry_count == 0:
                        logger.error(f"Timeout occurred while trying to open file '{file_path}' after multiple attempts.")
                        return False
                    logger.warning(f"Timeout occurred while trying to open file '{file_path}', retrying... ({3 - retry_count}/3)")
        except Exception as e:
            logger.exception(f"Unexpected error occurred during file content validation: {e}")
            return False

    async def validate_file_path_and_permissions(self, file_path: str, mode: str = 'w') -> bool:
        """
        Validate the file path and permissions.

        Args:
            file_path (str): The file path to validate.
            mode (str): The mode to validate, such as 'r' for read or 'w' for write (default: 'w').

        Returns:
            bool: True if the file path and permissions are valid, False otherwise.
        """
        if not await self.validate_filepath(file_path):
            return False
        if not await self.validate_permissions(file_path, mode=mode):
            return False
        return True

    async def generate_temp_file_path(self, suffix: str) -> str:
        """
        Generate a temporary file path.

        Args:
            suffix (str): The file extension suffix for the temp file.

        Returns:
            str: Path of the generated temporary file.
        """
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp_file:
                temp_path = temp_file.name
            return temp_path
        except Exception as e:
            logger.exception(f"Unexpected error occurred during temporary file generation: {e}")
            raise

    async def save_file(self, data, file_path: str, file_format: str) -> bool:
        """
        Save a file with the specified format.

        Args:
            data (any): The data to be saved.
            file_path (str): The file path where data should be saved.
            file_format (str): The format of the file.

        Returns:
            bool: True if the file was saved successfully, False otherwise.
        """
        temp_path = None
        try:
            if not isinstance(data, (str, bytes, dict, list)):  # Add explicit type check
                logger.error(f"Invalid data type for saving: {type(data)}. Supported types are str, bytes, dict, and list.")
                return False
            handlers = await file_handler(file_format)
            save_handler = handlers['save']
            temp_path = await self.generate_temp_file_path(suffix=f'.{file_format}')
            await save_handler(temp_path, data)
            os.replace(temp_path, file_path)  # Atomic operation to replace the file
            logger.info(f"Data saved to file '{file_path}' successfully. Data type: {type(data)}, Data size: {len(data) if hasattr(data, '__len__') else 'unknown'} bytes.")
            return True
        except Exception as e:
            logger.exception(f"Error occurred while saving file '{file_path}': {e}")
            return False
        finally:
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                except Exception as e:
                    logger.warning(f"Failed to delete temporary file '{temp_path}': {e}")

    async def load_file(self, file_path: str, file_format: str):
        """
        Load a file with the specified format.

        Args:
            file_path (str): The file path to load data from.
            file_format (str): The format of the file.

        Returns:
            any: The loaded data, or None if loading failed.
        """
        try:
            if not await self.validate_file_path_and_permissions(file_path, mode='r'):
                return None
            handlers = await file_handler(file_format)
            load_handler = handlers['load']
            return await load_handler(file_path)
        except Exception as e:
            logger.exception(f"Error occurred while loading file '{file_path}': {e}")
            return None

    async def delete_file(self, file_path: str) -> bool:
        """
        Delete a file.

        Args:
            file_path (str): The file path to delete.

        Returns:
            bool: True if the file was deleted successfully, False otherwise.
        """
        try:
            if not await self.validate_file_path_and_permissions(file_path, mode='w'):
                return False
            shutil.rmtree(file_path) if os.path.isdir(file_path) else os.remove(file_path)
            logger.info(f"File '{file_path}' deleted successfully.")
            return True
        except OSError as e:
            logger.error(f"Error occurred while deleting file '{file_path}': {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected error occurred during file deletion: {e}")
            return False
