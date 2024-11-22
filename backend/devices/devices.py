# backend/devices/devices.py

import aiohttp
from bs4 import BeautifulSoup
import aiofiles
from utils import configure_logging
from database import MongoHandler
from utils import handle_exceptions, log_execution_time, retry_on_exception
import re

# Initialize logger
logger = configure_logging()

class Device:
    """
    Base class for managing devices, including generic functions shared by all devices.
    """
    def __init__(self):
        self.mongo_handler = MongoHandler()

    @handle_exceptions
    @log_execution_time
    @retry_on_exception
    async def register_device(self, device_id, device_location, commands=None):
        """
        Register a device by adding it to the database.

        Args:
            device_id (str): Unique identifier for the device.
            device_location (str): Location information (e.g., USB, network, etc.).
            commands (list, optional): List of commands that can be used with the device.

        Returns:
            bool: True if the device was registered successfully, False otherwise.
        """
        device_data = {
            "_id": device_id,
            "device_location": device_location,
            "commands": commands or [],
        }
        result = await self.mongo_handler.insert_document("devices", device_data)
        if result:
            logger.info(f"Device '{device_id}' registered successfully in the database.")
            return True
        else:
            logger.error(f"Failed to register device '{device_id}' in the database.")
            return False

    @handle_exceptions
    @log_execution_time
    async def get_device(self, device_id):
        """
        Retrieve a device's information from the database.

        Args:
            device_id (str): Unique identifier for the device.

        Returns:
            dict: Device information if found, None otherwise.
        """
        device_data = await self.mongo_handler.find_document("devices", {"_id": device_id})
        if device_data:
            logger.info(f"Device '{device_id}' retrieved successfully from the database.")
            return device_data
        else:
            logger.error(f"Device '{device_id}' not found in the database.")
            return None

    @handle_exceptions
    @log_execution_time
    @retry_on_exception
    async def update_device(self, device_id, update_data):
        """
        Update a device's information in the database.

        Args:
            device_id (str): Unique identifier for the device.
            update_data (dict): The data to update for the device.

        Returns:
            bool: True if the device was updated successfully, False otherwise.
        """
        result = await self.mongo_handler.update_document("devices", {"_id": device_id}, {"$set": update_data})
        if result:
            logger.info(f"Device '{device_id}' updated successfully in the database.")
            return True
        else:
            logger.error(f"Failed to update device '{device_id}' in the database.")
            return False

    @handle_exceptions
    @log_execution_time
    async def delete_device(self, device_id):
        """
        Delete a device from the database.

        Args:
            device_id (str): Unique identifier for the device.

        Returns:
            bool: True if the device was deleted successfully, False otherwise.
        """
        result = await self.mongo_handler.delete_document("devices", {"_id": device_id})
        if result:
            logger.info(f"Device '{device_id}' deleted successfully from the database.")
            return True
        else:
            logger.error(f"Failed to delete device '{device_id}' from the database.")
            return False

    @handle_exceptions
    @log_execution_time
    async def list_devices(self):
        """
        List all devices in the database.

        Returns:
            list: A list of all devices in the database, or an empty list if none are found.
        """
        devices = await self.mongo_handler.find_documents("devices", {})
        if devices:
            logger.info(f"Retrieved list of all devices from the database.")
            return devices
        else:
            logger.info("No devices found in the database.")
            return []

    @handle_exceptions
    @log_execution_time
    async def search_for_device_documentation(self, device_id):
        """
        Search for device documentation, either locally or online.

        Args:
            device_id (str): Unique identifier for the device.

        Returns:
            str: Path to the found documentation, or None if documentation wasn't found.
        """
        # Search locally for pdf, doc, or docx files
        local_path_pdf = f"./backend/device_docs/{device_id}.pdf"
        local_path_doc = f"./backend/device_docs/{device_id}.doc"
        local_path_docx = f"./backend/device_docs/{device_id}.docx"

        for local_path in [local_path_pdf, local_path_doc, local_path_docx]:
            if await self.mongo_handler.check_file_exists(local_path):
                logger.info(f"Found local documentation for device '{device_id}' at '{local_path}'.")
                return local_path

        # Search online if local documentation is not found
        logger.info(f"Searching for online documentation for device '{device_id}'...")
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"https://www.google.com/search?q={device_id}+documentation") as response:
                    if response.status == 200:
                        content = await response.text()
                        soup = BeautifulSoup(content, "html.parser")
                        links = []

                        for a_tag in soup.find_all("a", href=True):
                            href = a_tag["href"]
                            if "url?q=" in href:
                                link = re.search(r"url\?q=(.*?)&", href)
                                if link:
                                    links.append(link.group(1))

                        # Attempt to download and save relevant documentation files (pdf, doc, docx)
                        for link in links:
                            if link.endswith(('.pdf', '.doc', '.docx')):
                                file_name = link.split('/')[-1]
                                file_path = f"./backend/device_docs/{file_name}"
                                async with session.get(link) as file_response:
                                    if file_response.status == 200:
                                        async with aiofiles.open(file_path, mode='wb') as f:
                                            await f.write(await file_response.read())
                                        logger.info(f"Downloaded and saved documentation for device '{device_id}' at '{file_path}'.")
                                        return file_path
                        
                        # If no suitable file is found, return None
                        logger.info(f"No suitable downloadable documentation found for device '{device_id}'.")
                        return None
                    else:
                        logger.error(f"Failed to retrieve online documentation for device '{device_id}', status code: {response.status}")
                        return None
        except Exception as e:
            logger.exception(f"Failed to search for online documentation for device '{device_id}': {e}")
            return None
