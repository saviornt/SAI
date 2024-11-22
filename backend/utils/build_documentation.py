import asyncio
import os
import subprocess
import shlex
from dotenv import load_dotenv
from .logging_utils import configure_logging
from .optimization_utils import retry_on_exception
from .helper_functions import get_env_var, execute_command

# Load environment variables from .env file
load_dotenv()

# Initialize logger
logger = configure_logging()

# Retry decorator for common retry logic
@retry_on_exception(max_retries=int(get_env_var("SPHINX_BUILD_RETRIES", "2", int)), delay=int(get_env_var("SPHINX_BUILD_DELAY", "3", int)), exceptions=(asyncio.TimeoutError, subprocess.CalledProcessError))
async def build_sphinx_docs() -> None:
    """
    Build the Sphinx documentation.

    This function asynchronously runs the `make html` and `make latexpdf` commands in the specified Sphinx documentation directory
    to generate both HTML and PDF documentation using Sphinx.

    Raises:
        Exception: If an error occurs while building the documentation.
    """
    sphinx_docs_path = get_env_var("SPHINX_DOCS_PATH", "./sphinx_docs")
    timeout = get_env_var("SPHINX_BUILD_TIMEOUT", 300, int)

    if not (os.path.exists(sphinx_docs_path) and os.path.isdir(sphinx_docs_path)):
        logger.error(f"The specified Sphinx documentation path does not exist or is not a directory: {sphinx_docs_path}")
        return

    # Clean documentation before building
    await clean_sphinx_docs()

    commands = [
        shlex.split("make html"),
        shlex.split("make latexpdf")
    ]

    # Execute commands concurrently to improve efficiency
    tasks = [execute_command(command, sphinx_docs_path, timeout) for command in commands]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    for command, result in zip(commands, results):
        if isinstance(result, Exception):
            logger.error(f"Failed to execute command '{' '.join(command)}': {result}")
        else:
            returncode, stdout, stderr = result
            if returncode == 0:
                logger.info(f"Sphinx documentation built successfully with command '{' '.join(command)}': {stdout}")
            else:
                logger.error(f"Error building Sphinx documentation with command '{' '.join(command)}': {stderr}")

@retry_on_exception(max_retries=int(get_env_var("SPHINX_BUILD_RETRIES", "2", int)), delay=int(get_env_var("SPHINX_BUILD_DELAY", "3", int)), exceptions=(asyncio.TimeoutError, subprocess.CalledProcessError))
async def clean_sphinx_docs() -> None:
    """
    Clean the Sphinx documentation.

    This function asynchronously runs the `make clean` command in the specified Sphinx documentation directory
    to remove the generated documentation files.

    Raises:
        Exception: If an error occurs while cleaning the documentation.
    """
    sphinx_docs_path = get_env_var("SPHINX_DOCS_PATH", "./sphinx_docs")
    timeout = get_env_var("SPHINX_BUILD_TIMEOUT", 300, int)

    if not (os.path.exists(sphinx_docs_path) and os.path.isdir(sphinx_docs_path)):
        logger.error(f"The specified Sphinx documentation path does not exist or is not a directory: {sphinx_docs_path}")
        return

    command = shlex.split("make clean")

    try:
        returncode, stdout, stderr = await execute_command(command, sphinx_docs_path, timeout)
        if returncode == 0:
            logger.info(f"Sphinx documentation cleaned successfully: {stdout}")
        else:
            logger.error(f"Error cleaning Sphinx documentation: {stderr}")
    except asyncio.TimeoutError:
        logger.error("Failed to clean Sphinx documentation after maximum retries.")

if __name__ == "__main__":
    asyncio.run(clean_sphinx_docs())
    asyncio.run(build_sphinx_docs())
