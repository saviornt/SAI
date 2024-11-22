# backend/action_interfaces/action_planner.py

import json
from utils import configure_logging
from memory import MemoryManagement

# Configure logging
logger = configure_logging()

class ActionPlanner:
    """
    A class to handle action planning for an AI system.

    This class is responsible for planning and executing actions based on input data and state information.
    It interacts with the memory management system to retrieve or store necessary information.
    """
    def __init__(self):
        """
        Initialize the ActionPlanner class with the MemoryManagement instance.
        """
        self.memory = MemoryManagement()

    async def plan_action(self, input_data):
        """
        Plan an action based on the provided input data.

        Args:
            input_data (dict): The input data to be used for planning an action.

        Returns:
            dict: A dictionary containing the planned action and any relevant information.
        """
        try:
            logger.info("Planning action based on input data...")
            # Determine the context type from input data
            context = input_data.get("context")

            # Validate the context value
            valid_contexts = ["physical_world", "text_analysis", "system_command"]
            if context not in valid_contexts:
                logger.warning(f"Invalid context type: {context}")
                return {"error": "Invalid context type provided."}

            # Example of retrieving state information from memory
            state_key = input_data.get("state_key")
            if state_key:
                state_info = await self.memory.retrieve_data(state_key)
                if state_info is not None:
                    logger.info(f"State information retrieved for key '{state_key}': {state_info}")
                    # Use state information in action planning
                else:
                    logger.info(f"No state information found for key '{state_key}'")

            # Plan the action based on context, input data, and state information
            if context == "physical_world":
                planned_action = self._plan_physical_world_action(input_data)
            elif context == "text_analysis":
                planned_action = self._plan_text_analysis_action(input_data)
            elif context == "system_command":
                planned_action = self._plan_system_command_action(input_data)
            else:
                # Fallback action for unknown context
                planned_action = {
                    "action": "no_op",
                    "parameters": {
                        "reason": "No valid action available for the provided context."
                    }
                }

            logger.info(f"Planned action: {planned_action}")
            return planned_action
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while planning action with input data {input_data}: {e}")
            return {"error": "Failed to plan action."}

    def _plan_physical_world_action(self, input_data):
        """
        Plan an action for the physical world context.

        Args:
            input_data (dict): The input data to be used for planning an action.

        Returns:
            dict: The planned action.
        """
        return {
            "action": "move_forward",
            "parameters": {
                "speed": input_data.get("speed", 1)
            }
        }

    def _plan_text_analysis_action(self, input_data):
        """
        Plan an action for the text analysis context.

        Args:
            input_data (dict): The input data to be used for planning an action.

        Returns:
            dict: The planned action.
        """
        return {
            "action": "analyze_text",
            "parameters": {
                "text": input_data.get("text", "")
            }
        }

    def _plan_system_command_action(self, input_data):
        """
        Plan an action for the system command context.

        Args:
            input_data (dict): The input data to be used for planning an action.

        Returns:
            dict: The planned action.
        """
        return {
            "action": "restart_service",
            "parameters": {
                "service_name": input_data.get("service_name", "unknown_service")
            }
        }

    async def execute_action(self, action):
        """
        Execute the planned action.

        Args:
            action (dict): The action to be executed.

        Returns:
            bool: True if the action was executed successfully, False otherwise.
        """
        try:
            logger.info(f"Executing action: {action}")
            # Example execution of action
            action_type = action.get("action")
            parameters = action.get("parameters", {})

            if action_type == "move_forward":
                return await self._execute_move_forward(parameters)
            elif action_type == "analyze_text":
                return await self._execute_analyze_text(parameters)
            elif action_type == "restart_service":
                return await self._execute_restart_service(parameters)
            elif action_type == "no_op":
                logger.info(f"No operation performed: {parameters.get('reason')}")
                return True
            else:
                logger.warning(f"Unknown action type: {action_type}")
                return False
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while executing action: {e}")
            return False

    async def _execute_move_forward(self, parameters):
        """
        Execute the move forward action.

        Args:
            parameters (dict): The parameters for the action.

        Returns:
            bool: True if the action was executed successfully, False otherwise.
        """
        speed = parameters.get("speed", 1)
        logger.info(f"Moving forward with speed {speed}")
        # Code to execute the physical movement would go here
        return True

    async def _execute_analyze_text(self, parameters):
        """
        Execute the analyze text action.

        Args:
            parameters (dict): The parameters for the action.

        Returns:
            bool: True if the action was executed successfully, False otherwise.
        """
        text = parameters.get("text", "")
        logger.info(f"Analyzing text: {text}")
        # Code to perform text analysis would go here
        return True

    async def _execute_restart_service(self, parameters):
        """
        Execute the restart service action.

        Args:
            parameters (dict): The parameters for the action.

        Returns:
            bool: True if the action was executed successfully, False otherwise.
        """
        service_name = parameters.get("service_name")
        logger.info(f"Restarting service: {service_name}")
        # Code to execute the system command would go here
        return True

    async def store_action_result(self, action_key, result):
        """
        Store the result of an action in memory.

        Args:
            action_key (str): The key under which the action result should be stored.
            result (dict): The result data to be stored.

        Returns:
            bool: True if the result was stored successfully, False otherwise.
        """
        try:
            logger.info(f"Storing action result for key '{action_key}'...")
            result_str = json.dumps(result)  # Convert result to JSON string for storage
            success = await self.memory.store_data(action_key, result_str)
            if success:
                logger.info(f"Action result stored successfully for key '{action_key}'")
            else:
                logger.error(f"Failed to store action result for key '{action_key}'")
            return success
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while storing action result: {e}")
            return False
