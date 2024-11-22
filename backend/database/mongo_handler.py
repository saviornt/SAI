# backend/memory/mongo_handler.py

from bson.objectid import ObjectId
from pymongo.errors import DuplicateKeyError, PyMongoError
from database import mongo_db
from utils import configure_logging

# Configure logging
logger = configure_logging()

class MongoHandler:
    """
    A class to handle memory operations using MongoDB.

    This class provides methods to interact with MongoDB for storing and retrieving data.
    """
    def __init__(self, collection_name):
        """
        Initialize the MongoMemoryHandler with a specific collection.

        Args:
            collection_name (str): The name of the MongoDB collection to be used.
        """
        if collection_name not in mongo_db.list_collection_names():
            raise ValueError(f"Collection '{collection_name}' does not exist in the database.")
        self.collection = mongo_db[collection_name]

    async def insert_document(self, data):
        """
        Insert a document into the collection.

        Args:
            data (dict): The data to insert as a document.

        Returns:
            str: The ID of the inserted document.
        """
        try:
            result = await self.collection.insert_one(data)
            logger.info(f"Document inserted with ID: {result.inserted_id}")
            return str(result.inserted_id)
        except DuplicateKeyError as e:
            logger.error(f"Duplicate key error while inserting document: {e}")
            return None
        except PyMongoError as e:
            logger.exception(f"PyMongo error occurred while inserting document: {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while inserting document: {e}")
            return None

    async def find_document(self, query):
        """
        Find a single document in the collection.

        Args:
            query (dict): The query to find the document.

        Returns:
            dict: The document found, or None if not found.
        """
        try:
            document = await self.collection.find_one(query)
            if document:
                logger.info(f"Document found: {document}")
            else:
                logger.info("No document matches the query.")
            return document
        except PyMongoError as e:
            logger.exception(f"PyMongo error occurred while finding document: {e}")
            return None
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while finding document: {e}")
            return None

    async def update_document(self, document_id, update_data):
        """
        Update a document in the collection by ID.

        Args:
            document_id (str): The ID of the document to update.
            update_data (dict): The data to update in the document.

        Returns:
            bool: True if the document was updated, False otherwise.
        """
        if not ObjectId.is_valid(document_id):
            logger.error(f"Invalid document ID: {document_id}")
            return False
        if not isinstance(update_data, dict):
            logger.error("Update data must be a dictionary.")
            return False
        try:
            result = await self.collection.update_one(
                {"_id": ObjectId(document_id)},
                {"$set": update_data}
            )
            if result.modified_count > 0:
                logger.info(f"Document with ID {document_id} updated successfully.")
                return True
            else:
                logger.info(f"No document found with ID {document_id} to update.")
                return False
        except PyMongoError as e:
            logger.exception(f"PyMongo error occurred while updating document: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while updating document: {e}")
            return False

    async def delete_document(self, document_id):
        """
        Delete a document in the collection by ID.

        Args:
            document_id (str): The ID of the document to delete.

        Returns:
            bool: True if the document was deleted, False otherwise.
        """
        try:
            result = await self.collection.delete_one({"_id": ObjectId(document_id)})
            if result.deleted_count > 0:
                logger.info(f"Document with ID {document_id} deleted successfully.")
                return True
            else:
                logger.info(f"No document found with ID {document_id} to delete.")
                return False
        except PyMongoError as e:
            logger.exception(f"PyMongo error occurred while deleting document: {e}")
            return False
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while deleting document: {e}")
            return False

    async def find_documents(self, query, limit=0):
        """
        Find multiple documents in the collection.

        Args:
            query (dict): The query to find the documents.
            limit (int): The maximum number of documents to return. Defaults to 0 (no limit).

        Returns:
            list: A list of documents that match the query.
        """
        try:
            # Ensure frequently queried fields have an index to improve performance
            cursor = self.collection.find(query).limit(limit)
            documents = await cursor.to_list(length=limit)
            logger.info(f"Found {len(documents)} document(s).")
            return documents
        except PyMongoError as e:
            logger.exception(f"PyMongo error occurred while finding documents: {e}")
            return []
        except Exception as e:
            logger.exception(f"Unexpected exception occurred while finding documents: {e}")
            return []
