# backend/utils/helper_functions.py

import asyncio
import os
import subprocess
from datetime import datetime, timezone
from dotenv import load_dotenv
from .logging_utils import configure_logging
from .optimization_utils import log_execution_time

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = configure_logging()

# Helper function to validate and get environment variables
def get_env_var(var_name: str, default_value: str, var_type: type = str) -> any:
    try:
        value = os.getenv(var_name, default_value)
        return var_type(value)
    except (ValueError, TypeError):
        logger.warning(f"Invalid value for {var_name}. Falling back to default: {default_value}")
        return var_type(default_value)

# Common command execution function
@log_execution_time(threshold=0.5)
async def execute_command(command: list, cwd: str, timeout: int) -> tuple:
    try:
        process = await asyncio.create_subprocess_exec(
            *command,
            cwd=cwd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        stdout, stderr = await process.communicate(timeout=timeout)
        return process.returncode, stdout.decode(), stderr.decode()
    except asyncio.TimeoutError:
        logger.error(f"Command '{' '.join(command)}' timed out after {timeout} seconds.")
        raise
    except subprocess.CalledProcessError as e:
        logger.error(f"Subprocess error occurred: {e}")
        raise

# Helper function to generate a consistent UTC timestamp
def generate_timestamp() -> str:
    """
    Generate a consistent UTC timestamp.

    Returns:
        str: The generated timestamp in ISO format.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None).isoformat()
