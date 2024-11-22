# backend/utils/logging_utils.py

import logging
import os
from logging.handlers import RotatingFileHandler
from pymongo import MongoClient, errors
from datetime import datetime, timezone
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Default log folder path from environment variable
DEFAULT_LOG_LOCATION = os.getenv("DEFAULT_LOG_LOCATION", "backend/LOGS")
DEFAULT_LOG_NAME = os.getenv("DEFAULT_LOG_NAME", f"{__name__}.log")
DEFAULT_LOG_LEVEL = os.getenv("DEFAULT_LOG_LEVEL", "INFO")
DEFAULT_LOG_FORMAT = os.getenv("DEFAULT_LOG_FORMAT", "%(asctime)s - %(name)s - %(levelname)s - %(message)s")
MONGO_SERVER_SELECTION_TIMEOUT = int(os.getenv("MONGO_SERVER_SELECTION_TIMEOUT", 10000))
MONGO_MAX_RETRIES = int(os.getenv("MONGO_MAX_RETRIES", 3))
MONGO_RETRY_DELAY = int(os.getenv("MONGO_RETRY_DELAY", 5))
MONGO_MAX_FAILURES = int(os.getenv("MONGO_MAX_FAILURES", 5))
LOG_MAX_BYTES = int(os.getenv("LOG_MAX_BYTES", 5 * 1024 * 1024))
LOG_BACKUP_COUNT = int(os.getenv("LOG_BACKUP_COUNT", 3))

# Validate LOG_LEVEL
if DEFAULT_LOG_LEVEL.upper() not in logging._nameToLevel:
    logging.warning(f"Invalid LOG_LEVEL: {DEFAULT_LOG_LEVEL}. Defaulting to INFO.")
    DEFAULT_LOG_LEVEL = "INFO"

class MongoDBHandler(logging.Handler):
    def __init__(self, mongo_uri, db_name, collection_name, fallback_file_handler):
        super().__init__()
        self.fallback_file_handler = fallback_file_handler
        self.connected = False
        self.client = None
        self.db = None
        self.collection = None
        self.failure_count = 0

        for attempt in range(MONGO_MAX_RETRIES):
            try:
                self.client = MongoClient(mongo_uri, serverSelectionTimeoutMS=MONGO_SERVER_SELECTION_TIMEOUT)
                self.db = self.client[db_name]
                self.collection = self.db[collection_name]
                # Test the connection
                self.client.admin.command('ping')
                self.connected = True
                break
            except (errors.ConnectionFailure, errors.ConfigurationError, errors.OperationFailure) as e:
                logging.error(f"Attempt {attempt + 1} - Failed to connect to MongoDB: {e}")
                time.sleep(MONGO_RETRY_DELAY)

        if not self.connected:
            logging.error("Failed to connect to MongoDB after multiple attempts, logging to MongoDB will be disabled.")

    def emit(self, record):
        if self.connected:
            log_document = {
                "level": record.levelname,
                "message": record.getMessage(),
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
                "path": record.pathname,
            }
            try:
                self.collection.insert_one(log_document)
                self.failure_count = 0  # Reset failure count on success
            except errors.PyMongoError as e:
                logging.error(f"Failed to insert log into MongoDB: {e}")
                self.failure_count += 1
                if self.failure_count >= MONGO_MAX_FAILURES:
                    logging.error("Exceeded maximum MongoDB logging failures, disabling MongoDB logging.")
                    self.connected = False
                self.fallback_file_handler.emit(record)
        else:
            self.fallback_file_handler.emit(record)


def configure_logging():
    """
    Configure logging to log to both a file and optionally to a MongoDB collection.
    """
    logger = logging.getLogger(__name__)
    logger.setLevel(getattr(logging, DEFAULT_LOG_LEVEL.upper(), logging.INFO))

    # Log Formatter
    formatter = logging.Formatter(DEFAULT_LOG_FORMAT)

    # Rotating File Handler (logging to file)
    log_file_path = os.path.join(DEFAULT_LOG_LOCATION, f"{__name__}.log")
    os.makedirs(DEFAULT_LOG_LOCATION, exist_ok=True)
    file_handler = RotatingFileHandler(log_file_path, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    # MongoDB Handler (using static MongoDB URI and database name for logs)
    mongo_uri = os.getenv("MONGO_URI", "mongodb://localhost:27017")
    db_name = os.path.basename(DEFAULT_LOG_LOCATION)
    collection_name = __name__
    mongo_handler = MongoDBHandler(mongo_uri, db_name, collection_name, file_handler)
    mongo_handler.setFormatter(formatter)
    logger.addHandler(mongo_handler)

    return logger

# Example Usage
if __name__ == "__main__":
    # Configure logging
    logger = configure_logging()
    
    # Log some messages
    logger.info("This is an info message.")
    logger.error("This is an error message.")
