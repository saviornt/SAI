# backend/services/agent_manager.py

import asyncio
from database import mongo_init
from memory import RedisHandler
from utils import configure_logging
from utils import handle_exceptions, retry_on_exception, log_execution_time

# Initialize logger
logger = configure_logging()

class AgentManager:
    """
    Manages agents, including creating, managing state, assigning tasks, and coordinating their actions.
    """

    def __init__(self):
        self.mongo_db = mongo_init()
        self.redis_handler = RedisHandler()
        self.agents = {}

    @handle_exceptions(default_return_value=None)
    @log_execution_time(threshold=0.5)
    def create_agent(self, agent_id: str, agent_data: dict) -> bool:
        """
        Creates an agent and stores it in the MongoDB database.

        Args:
            agent_id (str): The ID of the agent.
            agent_data (dict): The data to initialize the agent.

        Returns:
            bool: True if the agent was created successfully, False otherwise.
        """
        try:
            # Check if the agent already exists
            if self.mongo_db.agents.find_one({"_id": agent_id}):
                logger.warning(f"Agent {agent_id} already exists.")
                return False

            self.mongo_db.agents.insert_one({"_id": agent_id, **agent_data})
            self.agents[agent_id] = agent_data
            logger.info(f"Agent {agent_id} created successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to create agent {agent_id}: {e}")
            return False

    @handle_exceptions(default_return_value=None)
    @log_execution_time(threshold=0.5)
    def get_agent(self, agent_id: str) -> dict:
        """
        Retrieves an agent's data from MongoDB.

        Args:
            agent_id (str): The ID of the agent.

        Returns:
            dict: The agent's data if found, otherwise None.
        """
        try:
            agent_data = self.mongo_db.agents.find_one({"_id": agent_id})
            if agent_data:
                logger.info(f"Agent {agent_id} retrieved successfully.")
                return agent_data
            else:
                logger.warning(f"Agent {agent_id} not found.")
                return None
        except Exception as e:
            logger.error(f"Failed to retrieve agent {agent_id}: {e}")
            return None

    @handle_exceptions(default_return_value=False)
    @log_execution_time(threshold=0.5)
    def update_agent(self, agent_id: str, update_data: dict) -> bool:
        """
        Updates an agent's data in MongoDB.

        Args:
            agent_id (str): The ID of the agent.
            update_data (dict): The updated data for the agent.

        Returns:
            bool: True if the update was successful, False otherwise.
        """
        try:
            result = self.mongo_db.agents.update_one({"_id": agent_id}, {"$set": update_data})
            logger.info(f"Update data for agent {agent_id}: {update_data}")
            if result.modified_count > 0:
                self.agents[agent_id] = {**self.agents.get(agent_id, {}), **update_data}
                logger.info(f"Agent {agent_id} updated successfully.")
                return True
            else:
                logger.warning(f"No modifications made for agent {agent_id}. Update data: {update_data}")
                return False
        except Exception as e:
            logger.error(f"Failed to update agent {agent_id}: {e}")
            return False

    @handle_exceptions(default_return_value=False)
    @log_execution_time(threshold=0.5)
    def delete_agent(self, agent_id: str) -> bool:
        """
        Deletes an agent from MongoDB.

        Args:
            agent_id (str): The ID of the agent.

        Returns:
            bool: True if the deletion was successful, False otherwise.
        """
        try:
            result = self.mongo_db.agents.delete_one({"_id": agent_id})
            if result.deleted_count > 0:
                self.agents.pop(agent_id, None)
                logger.info(f"Agent {agent_id} deleted successfully.")
                return True
            else:
                logger.warning(f"Agent {agent_id} not found for deletion.")
                return False
        except Exception as e:
            logger.error(f"Failed to delete agent {agent_id}: {e}")
            return False

    @handle_exceptions(default_return_value=None)
    @retry_on_exception(max_retries=3, delay=1)
    async def assign_task(self, agent_id: str, task_data: dict) -> bool:
        """
        Assigns a task to an agent and stores it in Redis for quick access.

        Args:
            agent_id (str): The ID of the agent.
            task_data (dict): The task to be assigned.

        Returns:
            bool: True if the task was assigned successfully, False otherwise.
        """
        try:
            task_key = f"agent:{agent_id}:task"
            await self.redis_handler.set(task_key, task_data, expire=3600)  # Adding expiration time of 1 hour
            logger.info(f"Task assigned to agent {agent_id} successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to assign task to agent {agent_id}: {e}")
            return False

    @handle_exceptions(default_return_value=None)
    @log_execution_time(threshold=0.5)
    def list_agents(self, page: int = 1, page_size: int = 10) -> list:
        """
        Lists all agents managed by the system with pagination.

        Args:
            page (int): The page number to retrieve.
            page_size (int): The number of agents per page.

        Returns:
            list: A list of agent data for the specified page.
        """
        try:
            skip = (page - 1) * page_size
            agents_cursor = self.mongo_db.agents.find().skip(skip).limit(page_size)
            agents_list = list(agents_cursor)
            logger.info(f"Retrieved list of agents for page {page} successfully.")
            return agents_list
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            return []

    @handle_exceptions(default_return_value=None)
    @log_execution_time(threshold=0.5)
    async def coordinate_agents(self) -> bool:
        """
        Coordinates tasks among multiple agents, facilitating collaboration.

        Returns:
            bool: True if the coordination was successful, False otherwise.
        """
        try:
            agents = self.list_agents()
            if not agents:
                logger.warning("No agents available for coordination.")
                return False

            # Example of assigning complementary tasks
            for agent in agents:
                agent_id = agent.get("_id")
                if agent_id:
                    task_data = {"task": "collaborate", "details": "Assist in data analysis."}
                    await self.assign_task(agent_id, task_data)

            logger.info("Agents coordinated successfully.")
            return True
        except Exception as e:
            logger.error(f"Failed to coordinate agents: {e}")
            return False

# Example usage
if __name__ == "__main__":
    agent_manager = AgentManager()
    agent_manager.create_agent("agent_1", {"name": "Test Agent", "status": "active"})
    asyncio.run(agent_manager.assign_task("agent_1", {"task": "collect_data", "deadline": "2024-11-30"}))
    asyncio.run(agent_manager.coordinate_agents())
