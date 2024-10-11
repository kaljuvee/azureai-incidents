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
from azure.ai.textanalytics import TextAnalyticsClient
from dotenv import load_dotenv
import base64
import argparse
import heapq
from collections import Counter
import json

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variables
DATA_DIR = "data/small"
INDEX_NAME = "incident-reports"

# Azure AI Search configuration
search_endpoint = os.getenv("AZURE_SEARCH_ENDPOINT")
search_key = os.getenv("AZURE_SEARCH_KEY")
logging.info(f"Azure Search Endpoint: {search_endpoint}")
logging.info(f"Azure Search Key: {'*' * len(search_key) if search_key else 'Not found'}")

# Azure Text Analytics configuration
text_analytics_endpoint = os.getenv("AZURE_TEXT_ANALYTICS_ENDPOINT")
text_analytics_key = os.getenv("AZURE_TEXT_ANALYTICS_KEY")
logging.info(f"Azure Text Analytics Endpoint: {text_analytics_endpoint}")
logging.info(f"Azure Text Analytics Key: {'*' * len(text_analytics_key) if text_analytics_key else 'Not found'}")

try:
    search_credential = AzureKeyCredential(search_key)
    text_analytics_credential = AzureKeyCredential(text_analytics_key)
    logging.info("Azure credentials created successfully")
except ValueError as e:
    logging.error(f"Error creating Azure credentials: {str(e)}")
    raise

try:
    # Initialize clients
    search_index_client = SearchIndexClient(endpoint=search_endpoint, credential=search_credential)
    search_client = SearchClient(endpoint=search_endpoint, index_name=INDEX_NAME, credential=search_credential)
    text_analytics_client = TextAnalyticsClient(endpoint=text_analytics_endpoint, credential=text_analytics_credential)
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

def find_top_incidents(top_n=20, batch_size=10):
    logging.info(f"Finding top {top_n} incident types")
    try:
        results = list(search_client.search("*", top=1000))
        logging.info(f"Found {len(results)} documents")
        
        if not results:
            logging.info("No documents found")
            return []
        
        all_key_phrases = []
        
        # Process documents in batches of 10
        for i in range(0, len(results), batch_size):
            batch = results[i:i+batch_size]
            batch_content = [doc['content'] for doc in batch]
            
            key_phrases_response = text_analytics_client.extract_key_phrases(batch_content)
            
            for doc_key_phrases in key_phrases_response:
                if doc_key_phrases.is_error:
                    logging.warning(f"Error in key phrase extraction: {doc_key_phrases.error}")
                else:
                    all_key_phrases.extend(doc_key_phrases.key_phrases)
        
        logging.info(f"Extracted a total of {len(all_key_phrases)} key phrases")
        
        # Count occurrences of each key phrase
        phrase_counts = Counter(phrase.lower() for phrase in all_key_phrases)
        
        # Get top N incident types
        top_incidents = phrase_counts.most_common(top_n)
        
        logging.info(f"Top {top_n} incident types found")
        return top_incidents
    except Exception as e:
        logging.error(f"Error in find_top_incidents: {str(e)}")
        return []

def write_top_incidents_to_json(top_incidents):
    logging.info("Writing top incidents to JSON file")
    try:
        os.makedirs('reports', exist_ok=True)
        with open('reports/terms_discovered.json', 'w') as f:
            json.dump(top_incidents, f, indent=2)
        logging.info("Successfully wrote top incidents to reports/terms_discovered.json")
    except Exception as e:
        logging.error(f"Error writing top incidents to JSON: {str(e)}")

def main():
    logging.info("Starting the analysis process")
    
    try:
        # Create search index
        create_search_index()

        # Read and index documents
        read_and_index_documents(DATA_DIR)

        # Find top 20 incident types
        top_incidents = find_top_incidents(top_n=20)

        # Write top incident types to JSON file
        write_top_incidents_to_json(top_incidents)

        # Print top incident types
        logging.info("Analysis complete. Top incident types:")
        print("Top incident types:")
        for incident, count in top_incidents:
            logging.info(f"- {incident}: {count}")
            print(f"- {incident}: {count}")
    except Exception as e:
        logging.error(f"An error occurred during the main process: {str(e)}")
        print("An error occurred. Please check the logs for details.")

if __name__ == "__main__":
    main()