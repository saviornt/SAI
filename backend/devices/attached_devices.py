# backend/devices/attached_devices.py

import usb.core
import usb.util
import psutil
import platform
import traceback
from .devices import Device
from utils import handle_exceptions, log_execution_time, retry_on_exception, configure_logging

# Initialize logger
logger = configure_logging()

class AttachedDevices(Device):
    """
    Class for managing attached devices (e.g., USB devices).
    Inherits from the base Device class.
    """
    def __init__(self):
        super().__init__()

    @handle_exceptions
    @log_execution_time
    @retry_on_exception
    async def discover_attached_devices(self):
        """
        Discover attached devices (e.g., USB devices) and register them in the database.

        Returns:
            list: A list of discovered attached devices.
        """
        try:
            attached_devices = []

            # Scan for USB devices
            try:
                devices = usb.core.find(find_all=True)
                for device in devices:
                    device_info = {
                        "idVendor": hex(device.idVendor),
                        "idProduct": hex(device.idProduct),
                        "manufacturer": usb.util.get_string(device, device.iManufacturer),
                        "product": usb.util.get_string(device, device.iProduct),
                        "serial_number": usb.util.get_string(device, device.iSerialNumber),
                    }
                    attached_devices.append(device_info)
                    device_id = f"usb_device_{device.idVendor}_{device.idProduct}"
                    await self.register_device(device_id, "USB Port", commands=[])
            except usb.core.USBError as usb_error:
                logger.error(f"USB scanning failed: {usb_error}\n{traceback.format_exc()}")

            # Scan for storage devices
            try:
                partitions = psutil.disk_partitions()
                for partition in partitions:
                    try:
                        device_info = {
                            "device": partition.device,
                            "mountpoint": partition.mountpoint,
                            "fstype": partition.fstype,
                            "opts": partition.opts,
                        }
                        attached_devices.append(device_info)
                        device_id = f"storage_device_{partition.device.replace('/', '_')}"
                        await self.register_device(device_id, "Storage Device", commands=[])
                    except PermissionError as perm_error:
                        logger.warning(f"Permission denied while accessing partition {partition.device}: {perm_error}")
            except Exception as partition_error:
                logger.error(f"Error occurred while scanning storage devices: {partition_error}\n{traceback.format_exc()}")

            # Scan for other hardware devices (e.g., CPU, GPU)
            system_info = {
                "system": platform.system(),
                "node": platform.node(),
                "machine": platform.machine(),
                "processor": platform.processor(),
            }
            attached_devices.append(system_info)
            device_id = f"system_{system_info['node']}"
            await self.register_device(device_id, "System Device", commands=[])

            logger.info(f"Attached devices scanned and registered: {attached_devices}")
            return attached_devices
        except Exception as e:
            logger.error(f"Failed to scan attached devices: {e}\n{traceback.format_exc()}")
            return []

    @handle_exceptions
    @log_execution_time
    async def get_attached_device_info(self, device_id):
        """
        Retrieve information about a specific attached device.

        Args:
            device_id (str): Unique identifier for the device.

        Returns:
            dict: Device information if found, None otherwise.
        """
        return await self.get_device(device_id)

    @handle_exceptions
    @log_execution_time
    @retry_on_exception
    async def update_attached_device(self, device_id, update_data):
        """
        Update information for a specific attached device.

        Args:
            device_id (str): Unique identifier for the device.
            update_data (dict): The data to update for the device.

        Returns:
            bool: True if the device was updated successfully, False otherwise.
        """
        return await self.update_device(device_id, update_data)

    @handle_exceptions
    @log_execution_time
    async def remove_attached_device(self, device_id):
        """
        Remove an attached device from the database.

        Args:
            device_id (str): Unique identifier for the device.

        Returns:
            bool: True if the device was removed successfully, False otherwise.
        """
        return await self.delete_device(device_id)
