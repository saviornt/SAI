# backend/action_interfaces/device_interaction.py

import json
import paramiko
from utils import configure_logging
from memory import MemoryManagement
from database import MongoHandler
from files import FileHandler

# Configure logging
logger = configure_logging()

class DeviceInteraction:
    """
    A class to handle interaction with various devices.

    This class is responsible for managing interactions with devices, including sending commands,
    receiving data, and maintaining device states.
    """
    def __init__(self):
        """
        Initialize the DeviceInteraction class with the MemoryManagement instance.
        """
        self.memory = MemoryManagement()
        self.mongo_handler = MongoHandler()
        self.file_handler = FileHandler()

    async def send_command(self, device_id, command, parameters=None):
        """
        Send a command to a specified device.

        Args:
            device_id (str): The identifier of the device to interact with.
            command (str): The command to be sent to the device.
            parameters (dict, optional): Additional parameters for the command.

        Returns:
            dict: A dictionary containing the result of the command execution.
        """
        parameters = parameters or {}
        try:
            # Retrieve the list of known commands for the device from the database
            device_data = await self.mongo_handler.find_document("devices", {"_id": device_id})
            if not device_data:
                logger.error(f"Device '{device_id}' not found in the database.")
                return {"status": "error", "message": "Device not found."}

            known_commands = device_data.get("commands", [])
            device_location = device_data.get("device_location", "unknown")

            logger.info(f"Sending command '{command}' to device '{device_id}' with parameters: {parameters}")

            # Validate if the command is known
            if command in known_commands:
                if command == "ssh_command":
                    return await self._ssh_command(device_id, parameters)
                else:
                    return await self._execute_known_command(device_id, command, parameters)
            else:
                # Attempt to execute the unknown command and log any errors
                logger.warning(f"Unknown command '{command}' for device '{device_id}', attempting to execute it.")
                result = await self._execute_unknown_command(device_id, command, parameters)
                if result["status"] == "error":
                    logger.error(f"Failed to execute unknown command '{command}' on device '{device_id}': {result['message']}")
                return result
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while sending command to device '{device_id}', command: '{command}', parameters: {parameters}: {e}")
            return {"status": "error", "message": "Failed to send command."}

    async def _execute_known_command(self, device_id, command, parameters):
        """
        Execute a known command on the device.

        Args:
            device_id (str): The identifier of the device.
            command (str): The command to be executed.
            parameters (dict): Additional parameters for the command.

        Returns:
            dict: A dictionary containing the result of the command execution.
        """
        logger.info(f"Executing known command '{command}' on device '{device_id}' with parameters: {parameters}")
        # Simulate command execution logic
        # In a real implementation, this might involve sending a request to the device API or using specific device SDKs
        if command == "reboot":
            # Example of reboot command logic
            return {"status": "success", "message": f"Device '{device_id}' is rebooting."}
        elif command == "update_firmware":
            # Example of firmware update command logic
            return {"status": "success", "message": f"Device '{device_id}' firmware update initiated."}
        else:
            # Default known command execution
            return {"status": "success", "message": f"Command '{command}' executed successfully on device '{device_id}'."}

    async def _execute_unknown_command(self, device_id, command, parameters):
        """
        Attempt to execute an unknown command on the device and learn from the result.

        Args:
            device_id (str): The identifier of the device.
            command (str): The command to be executed.
            parameters (dict): Additional parameters for the command.

        Returns:
            dict: A dictionary containing the result of the command execution.
        """
        logger.info(f"Attempting to execute unknown command '{command}' on device '{device_id}' with parameters: {parameters}")
        try:
            # Execute the command on the device (simulate for now)
            # If the command succeeds, store it in the known commands for future use
            result = {"status": "success", "message": f"Command '{command}' executed successfully on device '{device_id}'."}
            if result["status"] == "success":
                await self.mongo_handler.update_document("devices", {"_id": device_id}, {"$push": {"commands": command}})
            return result
        except Exception as e:
            logger.exception(f"Failed to execute unknown command '{command}' on device '{device_id}': {e}")
            return {"status": "error", "message": "Failed to execute command."}

    async def _ssh_command(self, device_id, parameters):
        """
        Execute a command on a network device via SSH.

        Args:
            device_id (str): The identifier of the network device.
            parameters (dict): The parameters containing SSH details and the command.

        Returns:
            dict: A dictionary containing the result of the SSH command execution.
        """
        hostname = parameters.get("hostname")
        username = parameters.get("username")
        password = parameters.get("password")
        command = parameters.get("command")

        if not all([hostname, username, password, command]):
            logger.error(f"Invalid parameters for SSH command on device '{device_id}': {parameters}")
            return {"status": "error", "message": "Invalid parameters. 'hostname', 'username', 'password', and 'command' are required."}

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(hostname, username=username, password=password)
            stdin, stdout, stderr = client.exec_command(command)
            output = stdout.read().decode()
            error = stderr.read().decode()
            client.close()

            if error:
                logger.error(f"Error executing SSH command on device '{device_id}': {error}")
                return {"status": "error", "message": error}
            else:
                logger.info(f"SSH command executed successfully on device '{device_id}': {output}")
                return {"status": "success", "message": output}
        except Exception as e:
            logger.exception(f"Failed to execute SSH command on device '{device_id}': {e}")
            return {"status": "error", "message": "Failed to execute SSH command."}

    async def store_device_state(self, device_id, state):
        """
        Store the state of a device in memory.

        Args:
            device_id (str): The identifier of the device.
            state (dict): The state data to be stored.

        Returns:
            bool: True if the state was stored successfully, False otherwise.
        """
        try:
            logger.info(f"Storing state for device '{device_id}': {state}")
            state_str = json.dumps(state)  # Convert state to JSON string for storage
            success = await self.memory.store_data(device_id, state_str)
            if success:
                logger.info(f"Device state stored successfully for device '{device_id}'")
            else:
                logger.error(f"Failed to store device state for device '{device_id}'")
            return success
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while storing device state for device '{device_id}': {e}")
            return False

    async def learn_device_usage(self, device_id):
        """
        Learn how to use the specified device by gathering available documentation and analyzing it.

        Args:
            device_id (str): The identifier of the device.

        Returns:
            dict: The result of the learning process, or an error message if failed.
        """
        try:
            logger.info(f"Learning how to use device '{device_id}'")
            documentation = await self.file_handler.load_file(f"./device_docs/{device_id}.json")
            if not documentation:
                return await self._try_and_learn_device(device_id)

            logger.info(f"Analyzing device '{device_id}' documentation...")
            # Parse the documentation and learn the commands and capabilities of the device
            device_commands = json.loads(documentation).get("commands", [])
            if device_commands:
                await self.mongo_handler.update_document("devices", {"_id": device_id}, {"$set": {"commands": device_commands}})
                logger.info(f"Device '{device_id}' learning completed, commands updated in the database.")
                return {"status": "success", "message": f"Learning process completed for device '{device_id}'."}
            else:
                return {"status": "error", "message": f"No commands found in the documentation for device '{device_id}'."}
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while learning to use device '{device_id}': {e}")
            return {"status": "error", "message": "Failed to learn device usage."}

    async def _try_and_learn_device(self, device_id):
      """
      Attempt to learn how to interact with a device without existing documentation by trial and error.
  
      Args:
          device_id (str): The identifier of the device.
  
      Returns:
          dict: The result of the learning attempt.
      """
      try:
          logger.info(f"Attempting to learn device '{device_id}' by trial and error.")
          # Simulate trial and error learning by sending random commands and observing the responses
          possible_commands = ["turn_on", "turn_off", "get_status", "set_mode"]
          learned_commands = []
          for command in possible_commands:
              result = await self._execute_unknown_command(device_id, command, {})
              if result["status"] == "success":
                  learned_commands.append(command)
  
          if learned_commands:
              await self.mongo_handler.update_document("devices", {"_id": device_id}, {"$set": {"commands": learned_commands}})
              logger.info(f"Trial and error learning completed for device '{device_id}', learned commands: {learned_commands}")
              return {"status": "success", "message": f"Trial and error learning completed for device '{device_id}'"}
          else:
              logger.warning(f"No commands were successfully learned for device '{device_id}' during trial and error.")
              return {"status": "error", "message": f"Failed to learn any commands for device '{device_id}'"}
      except Exception as e:
          logger.exception(f"Unexpected exception occurred while attempting trial and error learning for device '{device_id}': {e}")
          return {"status": "error", "message": "Failed to learn device usage."}

