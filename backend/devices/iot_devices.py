# backend/devices/iot_devices.py

import asyncio
from database import MongoHandler
from memory import RedisHandler
from utils import configure_logging, handle_exceptions, retry_on_exception, log_execution_time
from .devices import Device
import socket
from pysnmp.hlapi.v3arch.asyncio import *
import traceback
from tenacity import AsyncRetrying, stop_after_attempt, wait_exponential, retry_if_exception_type

# Initialize logger
logger = configure_logging()

class IoTDevices(Device):
    """
    Manages IoT devices, including discovery and monitoring on the network.
    """
    def __init__(self):
        super().__init__()
        self.mongo_handler = MongoHandler()
        self.redis_handler = RedisHandler()

    @handle_exceptions
    @log_execution_time
    @retry_on_exception
    async def discover_iot_devices(self) -> bool:
        """
        Discover IoT devices on the network.

        Returns:
            bool: True if IoT devices are discovered, False otherwise.
        """
        try:
            try:
                local_ip = socket.gethostbyname(socket.gethostname())
            except socket.error as e:
                logger.error(f"Failed to resolve local hostname: {e}")
                return False

            network_prefix = '.'.join(local_ip.split('.')[:-1])
            discovered_devices = []

            async def scan_ip_snmp(ip):
                try:
                    iterator = await get_cmd(SnmpEngine(),
                                             CommunityData('public', mpModel=0),
                                             UdpTransportTarget((ip, 161), timeout=1, retries=0),
                                             ContextData(),
                                             ObjectType(ObjectIdentity('1.3.6.1.2.1.1.1.0')))
                    errorIndication, errorStatus, errorIndex, varBinds = await iterator

                    if errorIndication is None and not errorStatus:
                        device_id = f"iot_device_{ip.split('.')[-1]}"
                        device_data = {
                            "ip_address": ip,
                            "status": "active",
                            "commands": []
                        }
                        if await self.retry_register_device(device_id, "IoT Device", device_data):
                            discovered_devices.append(device_data)
                    elif errorIndication:
                        logger.error(f"SNMP error for IP {ip}: {errorIndication}")
                    elif errorStatus:
                        logger.error(f"SNMP error status for IP {ip}: {errorStatus.prettyPrint()} at {errorIndex and varBinds[int(errorIndex) - 1] or '?'}")
                except Exception as e:
                    logger.error(f"SNMP scan failed for IP {ip}: {e}\n{traceback.format_exc()}")

            semaphore = asyncio.Semaphore(10)

            async def limited_scan_ip_snmp(ip):
                async with semaphore:
                    await scan_ip_snmp(ip)

            tasks = [limited_scan_ip_snmp(f"{network_prefix}.{i}") for i in range(1, 255)]
            await asyncio.gather(*tasks)

            if discovered_devices:
                logger.info(f"Discovered and registered IoT devices: {discovered_devices}")
                return True
            else:
                logger.info("No IoT devices discovered on the network.")
                return False
        except Exception as e:
            logger.error(f"Failed to discover IoT devices: {e}\n{traceback.format_exc()}")
            return False

    @handle_exceptions
    @log_execution_time
    async def retry_register_device(self, device_id, device_type, device_data):
        """
        Retry registering a device in case of temporary database connectivity issues.

        Args:
            device_id (str): Unique identifier for the device.
            device_type (str): The type of the device.
            device_data (dict): The data of the device.

        Returns:
            bool: True if the device was registered successfully, False otherwise.
        """
        retry_strategy = AsyncRetrying(
            stop=stop_after_attempt(5),
            wait=wait_exponential(min=2, max=20),
            retry=retry_if_exception_type(Exception)
        )
        async for attempt in retry_strategy:
            with attempt:
                try:
                    if await self.register_device(device_id, device_type, device_data):
                        logger.info(f"Successfully registered device {device_id} after {attempt.retry_state.attempt_number} attempts.")
                        return True
                except (ConnectionError, TimeoutError) as e:
                    logger.warning(f"Attempt {attempt.retry_state.attempt_number} failed for device {device_id} due to recoverable error: {e}")
                except Exception as e:
                    logger.error(f"Unrecoverable error occurred during registration for device {device_id}: {e}")
                    break
        return False

    @handle_exceptions
    @log_execution_time
    async def get_iot_device_info(self, device_id):
        """
        Retrieve information about a specific IoT device.

        Args:
            device_id (str): Unique identifier for the device.

        Returns:
            dict: Device information if found, None otherwise.
        """
        return await self.get_device(device_id)

    @handle_exceptions
    @log_execution_time
    @retry_on_exception
    async def update_iot_device(self, device_id, update_data):
        """
        Update information for a specific IoT device.

        Args:
            device_id (str): Unique identifier for the device.
            update_data (dict): The data to update for the device.

        Returns:
            bool: True if the device was updated successfully, False otherwise.
        """
        return await self.update_device(device_id, update_data)

    @handle_exceptions
    @log_execution_time
    async def remove_iot_device(self, device_id):
        """
        Remove an IoT device from the database.

        Args:
            device_id (str): Unique identifier for the device.

        Returns:
            bool: True if the device was removed successfully, False otherwise.
        """
        return await self.delete_device(device_id)
