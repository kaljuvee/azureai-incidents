import os
import logging
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.search.documents.indexes.models import (
    SearchIndex,
    SimpleField,
    SearchableField,
    SearchFieldDataType,
)
from dotenv import load_dotenv
import base64

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variables
DATA_DIR = "data/small"
INDEX_NAME = "incident-small"

# Azure AI Search configuration
search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
search_key = os.getenv("AZURE_SEARCH_KEY")
logging.info(f"Azure Search Endpoint: {search_endpoint}")
logging.info(f"Azure Search Key: {'*' * len(search_key) if search_key else 'Not found'}")

try:
    search_credential = AzureKeyCredential(search_key)
    logging.info("Azure credentials created successfully")
except ValueError as e:
    logging.error(f"Error creating Azure credentials: {str(e)}")
    raise

try:
    # Initialize clients
    search_index_client = SearchIndexClient(endpoint=search_endpoint, credential=search_credential)
    search_client = SearchClient(endpoint=search_endpoint, index_name=INDEX_NAME, credential=search_credential)
    logging.info("Azure clients initialized successfully")
except Exception as e:
    logging.error(f"Error initializing Azure clients: {str(e)}")
    raise

def create_search_index():
    logging.info(f"Creating search index: {INDEX_NAME}")
    try:
        fields = [
            SimpleField(name="id", type=SearchFieldDataType.String, key=True),
            SearchableField(name="content", type=SearchFieldDataType.String, analyzer_name="en.microsoft"),
        ]
        index = SearchIndex(name=INDEX_NAME, fields=fields)
        result = search_index_client.create_or_update_index(index)
        logging.info(f"Search index '{INDEX_NAME}' created successfully. Result: {result}")
    except Exception as e:
        logging.error(f"Error creating search index: {str(e)}")
        raise

def encode_filename(filename):
    # Remove the .txt extension, encode to bytes, then to base64, and decode to string
    return base64.urlsafe_b64encode(filename[:-4].encode()).decode()

def read_and_index_documents(input_folder):
    logging.info(f"Reading and indexing documents from {input_folder}")
    documents = []
    try:
        for filename in os.listdir(input_folder):
            if filename.endswith('.txt'):
                file_path = os.path.join(input_folder, filename)
                logging.info(f"Reading file: {file_path}")
                try:
                    with open(file_path, 'r') as file:
                        content = file.read().strip()
                        encoded_filename = encode_filename(filename)
                        documents.append({
                            "id": encoded_filename,
                            "content": content
                        })
                    logging.info(f"Successfully read file: {filename} (encoded as: {encoded_filename})")
                except IOError as e:
                    logging.error(f"Error reading file {filename}: {str(e)}")
        
        logging.info(f"Attempting to index {len(documents)} documents")
        result = search_client.upload_documents(documents)
        succeeded = sum(1 for r in result if r.succeeded)
        failed = sum(1 for r in result if not r.succeeded)
        logging.info(f"Indexing complete. Succeeded: {succeeded}, Failed: {failed}")
        if failed > 0:
            logging.warning(f"Some documents failed to index. Check individual results for details.")
        
        # Add this check to verify documents were indexed
        total_docs = search_client.get_document_count()
        logging.info(f"Total documents in index after indexing: {total_docs}")
    except Exception as e:
        logging.error(f"Error in read_and_index_documents: {str(e)}")
        raise

def main():
    logging.info("Starting the index creation and document upload process")

    try:
        # Create search index
        create_search_index()

        # Read and index documents
        read_and_index_documents(DATA_DIR)

        logging.info("Index creation and document upload complete.")
    except Exception as e:
        logging.error(f"An error occurred during the main process: {str(e)}")
        print(f"An error occurred. Please check the logs for details.")

if __name__ == "__main__":
    main()