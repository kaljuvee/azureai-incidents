import os
import logging
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.ai.textanalytics import TextAnalyticsClient
from dotenv import load_dotenv
import argparse

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variables
INDEX_NAME = "incident-small"

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
    search_client = SearchClient(endpoint=search_endpoint, index_name=INDEX_NAME, credential=search_credential)
    text_analytics_client = TextAnalyticsClient(endpoint=text_analytics_endpoint, credential=text_analytics_credential)
    logging.info("Azure clients initialized successfully")
except Exception as e:
    logging.error(f"Error initializing Azure clients: {str(e)}")
    raise

def count_incidents(query_incident):
    logging.info(f"Counting incidents for query: '{query_incident}'")
    try:
        # Search for relevant documents, increase top to 50
        results = list(search_client.search(query_incident, top=50))
        logging.info(f"Found {len(results)} relevant documents")
        
        if not results:
            logging.info(f"No documents found for query: '{query_incident}'")
            return 0
        
        # Combine relevant documents
        combined_content = "\n\n".join([doc['content'] for doc in results])
        logging.info(f"Combined content length: {len(combined_content)} characters")
        
        # Use Azure Text Analytics to extract key phrases
        key_phrases_response = text_analytics_client.extract_key_phrases([combined_content])
        
        if not key_phrases_response or not key_phrases_response[0].key_phrases:
            logging.info(f"No key phrases extracted for query: '{query_incident}'")
            return 0
        
        key_phrases = key_phrases_response[0].key_phrases
        logging.info(f"Extracted {len(key_phrases)} key phrases")
        
        # Count occurrences of query_incident in key phrases and content
        phrase_count = sum(1 for phrase in key_phrases if query_incident.lower() in phrase.lower())
        content_count = combined_content.lower().count(query_incident.lower())
        
        # Take the maximum of the two counts
        count = max(phrase_count, content_count)
        
        logging.info(f"Incident count for '{query_incident}': {count} (phrase count: {phrase_count}, content count: {content_count})")
        return count
    except Exception as e:
        logging.error(f"Error in count_incidents: {str(e)}")
        return 0  # Return 0 instead of raising an exception

def main():
    logging.info("Starting the analysis process")
    
    parser = argparse.ArgumentParser(description="Analyze incident reports using Azure AI services.")
    parser.add_argument("incident_type", type=str, help="The type of incident to query for (use quotes for composite terms)")
    args = parser.parse_args()

    try:
        # Set the query incident from command line argument
        query_incident = args.incident_type
        logging.info(f"Query incident set to: '{query_incident}'")

        # Count incidents
        total_count = count_incidents(query_incident)

        # Print total count
        logging.info(f"Analysis complete. Total count for '{query_incident}' incidents: {total_count}")
        print(f"Total count for '{query_incident}' incidents: {total_count}")
    except Exception as e:
        logging.error(f"An error occurred during the main process: {str(e)}")
        print(f"An error occurred. Please check the logs for details.")

if __name__ == "__main__":
    main()