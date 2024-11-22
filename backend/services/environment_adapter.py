# backend/services/environment_adapter.py

import os
import asyncio
from utils import configure_logging, handle_exceptions, log_execution_time, timeout
from database import mongo_init
from memory import RedisHandler


# Initialize logger
logger = configure_logging()

class EnvironmentAdapter:
    """
    Manages the environmental conditions to help the agent adapt to different scenarios.
    """

    def __init__(self, is_simulated: bool = False):
        self.is_simulated = is_simulated
        self.mongo_db = None
        self.redis_handler = RedisHandler()
        self.environment_collection = None

    def _initialize_mongo(self):
        if not self.mongo_db:
            try:
                self.mongo_db = mongo_init()
                self.environment_collection = self.mongo_db.get_collection("environment_data")
            except Exception as e:
                logger.error(f"Failed to connect to MongoDB collection 'environment_data': {e}")
                self.environment_collection = None

    @handle_exceptions(default_return_value=None)
    @log_execution_time(threshold=0.5)
    @timeout(10)
    async def get_environment_state(self, environment_id: str) -> dict:
        """
        Retrieve the current state of the environment.

        Args:
            environment_id (str): The unique identifier for the environment.

        Returns:
            dict: The state of the environment.
        """
        try:
            self._initialize_mongo()
            if not self.environment_collection:
                logger.error("Environment collection is not available.")
                return None
            env_state = await self.environment_collection.find_one(
                {"_id": environment_id},
                projection={"temperature": 1, "humidity": 1, "status": 1, "high_temp_threshold": 1, "low_temp_threshold": 1}  # Limiting the fields returned
            )
            if env_state:
                logger.info(f"Retrieved environment state for {environment_id} successfully.")
                return env_state
            else:
                logger.warning(f"Environment {environment_id} not found.")
                return None
        except Exception as e:
            logger.error(f"Failed to retrieve environment state for {environment_id}: {e}")
            return None

    @handle_exceptions(default_return_value=False)
    @log_execution_time(threshold=0.5)
    @timeout(10)
    async def update_environment_state(self, environment_id: str, new_state: dict) -> bool:
        """
        Update the current state of the environment.

        Args:
            environment_id (str): The unique identifier for the environment.
            new_state (dict): A dictionary containing new state information.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        try:
            self._initialize_mongo()
            if not self.environment_collection:
                logger.error("Environment collection is not available.")
                return False
            result = await self.environment_collection.update_one(
                {"_id": environment_id}, {"$set": new_state}, upsert=True
            )
            if result.modified_count > 0 or result.upserted_id is not None:
                logger.info(f"Environment state updated for {environment_id}.")
                return True
            else:
                logger.warning(f"No modifications made for environment {environment_id}.")
                return False
        except Exception as e:
            logger.error(f"Failed to update environment state for {environment_id}: {e}")
            return False

    @handle_exceptions(default_return_value=False)
    @log_execution_time(threshold=0.5)
    async def monitor_environment_changes(self, stop_signal: asyncio.Event) -> bool:
        """
        Monitor the environment for changes and adapt accordingly.

        Args:
            stop_signal (asyncio.Event): An event to signal when to stop monitoring.

        Returns:
            bool: True if the monitoring was successful, False otherwise.
        """
        try:
            logger.info("Starting to monitor environment changes...")
            backoff_time = 1
            while not stop_signal.is_set():
                environment_data = await self.redis_handler.get_all("environment_updates")
                if environment_data:
                    for env_id, new_state in environment_data.items():
                        await self.update_environment_state(env_id, new_state)
                    backoff_time = 1  # Reset backoff time if there is data to process
                else:
                    backoff_time = min(backoff_time * 2, 60)  # Exponential backoff with a maximum limit
                await asyncio.sleep(backoff_time)
            logger.info("Stopped monitoring environment changes.")
            return True
        except Exception as e:
            logger.error(f"Failed during environment monitoring: {e}")
            return False

    @handle_exceptions(default_return_value=False)
    @log_execution_time(threshold=0.5)
    async def adapt_to_environment(self, environment_id: str, agent_id: str) -> bool:
        """
        Adapt the agent to changes in the environment.

        Args:
            environment_id (str): The unique identifier for the environment.
            agent_id (str): The unique identifier of the agent.

        Returns:
            bool: True if adaptation was successful, False otherwise.
        """
        try:
            env_state = await self.get_environment_state(environment_id)
            if not env_state:
                return False
            logger.info(f"Adapting agent {agent_id} to environment {environment_id}. Simulated: {self.is_simulated}")
            # Example adaptation logic
            high_temp_threshold = env_state.get("high_temp_threshold", int(os.getenv("HIGH_TEMPERATURE_THRESHOLD", 30)))
            low_temp_threshold = env_state.get("low_temp_threshold", int(os.getenv("LOW_TEMPERATURE_THRESHOLD", 10)))
            if env_state.get("temperature", 0) > high_temp_threshold:
                logger.info(f"Agent {agent_id} adapting to high temperature in environment {environment_id}. Threshold: {high_temp_threshold}")
            elif env_state.get("temperature", 0) < low_temp_threshold:
                logger.info(f"Agent {agent_id} adapting to low temperature in environment {environment_id}. Threshold: {low_temp_threshold}")
            # More complex adaptation logic can be added here
            return True
        except Exception as e:
            logger.error(f"Failed to adapt agent {agent_id} to environment {environment_id}: {e}")
            return False

# Example usage
if __name__ == "__main__":
    adapter = EnvironmentAdapter(is_simulated=True)
    stop_signal = asyncio.Event()

    try:
        loop = asyncio.get_event_loop()
        loop.run_until_complete(adapter.monitor_environment_changes(stop_signal))
    except KeyboardInterrupt:
        stop_signal.set()
        logger.info("Received stop signal, terminating monitoring...")
        loop.run_until_complete(adapter.monitor_environment_changes(stop_signal))
    finally:
        loop.close()
