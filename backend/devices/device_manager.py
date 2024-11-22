# backend/services/device_manager.py

import asyncio
from utils import configure_logging
from utils import handle_exceptions, log_execution_time
from devices.attached_devices import AttachedDevices
from devices.iot_devices import IoTDevices
from devices.network_devices import NetworkDevices
from devices.device_interaction import DeviceInteraction
from datetime import datetime, timezone

# Initialize logger
logger = configure_logging()

def format_log_entry(device_id, action, status, timestamp):
    return {
        "device_id": device_id,
        "action": action,
        "status": status,
        "timestamp": timestamp
    }

class DeviceManager:
    """
    Centralized management of all device types: Attached, IoT, and Network Devices.
    """

    def __init__(self):
        self.attached_devices_manager = AttachedDevices()
        self.iot_devices_manager = IoTDevices()
        self.network_devices_manager = NetworkDevices()
        self.device_interaction = DeviceInteraction()
        self.device_registry = {}  # Keeps track of device states and configurations

    @handle_exceptions(default_return_value=None)
    @log_execution_time(threshold=0.5)
    async def discover_all_devices(self):
        """
        Discover and register all types of devices: attached, IoT, and network devices.
        """
        try:
            logger.info("Starting discovery for all devices...")
            attached_devices = await self.attached_devices_manager.scan_attached_devices()
            logger.info(f"Attached devices discovered: {attached_devices}")

            iot_discovery_status = await self.iot_devices_manager.discover_iot_devices()
            logger.info(f"IoT devices discovery status: {iot_discovery_status}")

            network_discovery_status = await self.network_devices_manager.discover_network_devices()
            logger.info(f"Network devices discovery status: {network_discovery_status}")
        except Exception as e:
            logger.error(f"Failed to discover devices: {e}")

    @handle_exceptions(default_return_value=None)
    @log_execution_time(threshold=0.5)
    async def discover_attached_devices(self):
        """
        Discover and register attached devices.
        """
        try:
            logger.info("Starting discovery for attached devices...")
            attached_devices = await self.attached_devices_manager.scan_attached_devices()
            logger.info(f"Attached devices discovered: {attached_devices}")
        except Exception as e:
            logger.error(f"Failed to discover attached devices: {e}")

    @handle_exceptions(default_return_value=None)
    @log_execution_time(threshold=0.5)
    async def discover_iot_devices(self):
        """
        Discover and register IoT devices.
        """
        try:
            logger.info("Starting discovery for IoT devices...")
            iot_discovery_status = await self.iot_devices_manager.discover_iot_devices()
            logger.info(f"IoT devices discovery status: {iot_discovery_status}")
        except Exception as e:
            logger.error(f"Failed to discover IoT devices: {e}")

    @handle_exceptions(default_return_value=None)
    @log_execution_time(threshold=0.5)
    async def discover_network_devices(self):
        """
        Discover and register network devices.
        """
        try:
            logger.info("Starting discovery for network devices...")
            network_discovery_status = await self.network_devices_manager.discover_network_devices()
            logger.info(f"Network devices discovery status: {network_discovery_status}")
        except Exception as e:
            logger.error(f"Failed to discover network devices: {e}")

    @handle_exceptions(default_return_value=None)
    @log_execution_time(threshold=0.5)
    async def monitor_device_status(self, device_id):
        """
        Monitor the status of a specific device.

        Args:
            device_id (str): The ID of the device to monitor.
        """
        try:
            logger.info(f"Monitoring status of device: {device_id}")
            try:
                status = await self.device_interaction.get_device_status(device_id)
                logger.info(f"Device {device_id} status: {status}")
            except Exception as e:
                logger.error(f"Failed to retrieve status for device {device_id}: {e}")
        except Exception as e:
            logger.error(f"Failed to monitor device {device_id}: {e}")

    @handle_exceptions(default_return_value=None)
    @log_execution_time(threshold=0.5)
    async def control_device(self, device_id, command, parameters=None):
        """
        Control a device by sending a command.

        Args:
            device_id (str): The ID of the device to control.
            command (str): The command to send to the device.
            parameters (dict, optional): Additional parameters for the command.
        """
        try:
            logger.info(f"Sending command '{command}' to device: {device_id}")
            # Validate if the command is supported by the target device
            device_info = await self.device_interaction.get_device_info(device_id)
            if command not in device_info.get('supported_commands', []):
                logger.error(f"Command '{command}' is not supported by device {device_id}")
                return
            response = await self.device_interaction.send_command(device_id, command, parameters)
            logger.info(f"Command response from device {device_id}: {response}")
        except Exception as e:
            logger.error(f"Failed to control device {device_id}: {e}")

    @handle_exceptions(default_return_value=None)
    @log_execution_time(threshold=0.5)
    async def schedule_device_task(self, device_id, task, interval_minutes):
        """
        Schedule a recurring task for a device.

        Args:
            device_id (str): The ID of the device.
            task (str): The task to schedule.
            interval_minutes (int): The interval in minutes for the task.
        """
        try:
            logger.info(f"Scheduling task '{task}' for device {device_id} every {interval_minutes} minutes")
            loop = asyncio.get_event_loop()
            while True:
                await asyncio.sleep(interval_minutes * 60)
                await self.control_device(device_id, task)
        except Exception as e:
            logger.error(f"Failed to schedule task for device {device_id}: {e}")

    @handle_exceptions(default_return_value=None)
    @log_execution_time(threshold=0.5)
    async def remove_device(self, device_id):
        """
        Remove a device from the registry.

        Args:
            device_id (str): The ID of the device to remove.
        """
        try:
            logger.info(f"Removing device: {device_id}")
            # Logic to remove device from database and registry
            await self.device_interaction.remove_device_from_database(device_id)
            if device_id in self.device_registry:
                del self.device_registry[device_id]
                logger.info(f"Device {device_id} removed successfully.")
            else:
                logger.warning(f"Device {device_id} not found in registry.")
        except Exception as e:
            logger.error(f"Failed to remove device {device_id}: {e}")

    @handle_exceptions(default_return_value=None)
    @log_execution_time(threshold=0.5)
    async def batch_action(self, action, device_ids, parameters=None):
        """
        Perform a batch action on multiple devices.

        Args:
            action (str): The action to perform (e.g., 'reboot', 'update').
            device_ids (list): List of device IDs to perform the action on.
            parameters (dict, optional): Additional parameters for the action.
        """
        try:
            logger.info(f"Performing batch action '{action}' on devices: {device_ids}")
            for device_id in device_ids:
                await self.control_device(device_id, action, parameters)
        except Exception as e:
            logger.error(f"Failed to perform batch action '{action}': {e}")

    @handle_exceptions(default_return_value=None)
    @log_execution_time(threshold=0.5)
    async def device_event_handler(self, event):
        """
        Handle events related to devices, such as connection or disconnection events.

        Args:
            event (dict): The event data.
        """
        try:
            event_type = event.get("type")
            device_id = event.get("device_id")
            logger.info(f"Handling event '{event_type}' for device {device_id}")
            # Logic to handle different event types
        except Exception as e:
            logger.error(f"Failed to handle event for device {device_id}: {e}")

    @handle_exceptions(default_return_value=None)
    @log_execution_time(threshold=0.5)
    async def device_history_log(self, device_id, action, status):
        """
        Log the history of actions performed on a device.

        Args:
            device_id (str): The ID of the device.
            action (str): The action performed.
            status (str): The result of the action.
        """
        try:
            timestamp = datetime.now(timezone.utc).isoformat()
            log_entry = format_log_entry(device_id, action, status, timestamp)
            # Logic to save log_entry to the database
            logger.info(f"Device history logged: {log_entry}")
        except Exception as e:
            logger.error(f"Failed to log history for device {device_id}: {e}")

# Example usage
if __name__ == "__main__":
    device_manager = DeviceManager()
    asyncio.run(device_manager.discover_all_devices())
