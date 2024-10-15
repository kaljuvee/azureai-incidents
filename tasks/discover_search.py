import os
import logging
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.ai.textanalytics import TextAnalyticsClient
from dotenv import load_dotenv
import base64
from collections import Counter
import json

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