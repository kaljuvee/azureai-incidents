import os
import logging
import json
import csv
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.indexes import SearchIndexClient
from azure.ai.textanalytics import TextAnalyticsClient
from dotenv import load_dotenv
import base64
import argparse
from datetime import datetime

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variables
DATA_DIR = "data/small"
INDEX_NAME = "incident-small"
CONFIG_FILE = "config/incident_type_distribution.json"

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
            for r in result:
                if not r.succeeded:
                    logging.error(f"Document {r.key} failed to index. Error: {r.error}")
        
        # Add this check to verify documents were indexed
        total_docs = search_client.get_document_count()
        logging.info(f"Total documents in index after indexing: {total_docs}")
    except Exception as e:
        logging.error(f"Error in read_and_index_documents: {str(e)}")
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

def load_incident_types():
    logging.info(f"Loading incident types from {CONFIG_FILE}")
    try:
        with open(CONFIG_FILE, 'r') as f:
            incident_types = json.load(f)
        
        # Create a new dictionary with modified keys
        modified_incident_types = {}
        for term, count in incident_types.items():
            if ' ' in term:
                modified_incident_types[f'"""{term}"""'] = count
            else:
                modified_incident_types[term] = count
        
        return modified_incident_types
    except Exception as e:
        logging.error(f"Error loading incident types: {str(e)}")
        raise

def generate_report(results, output_file):
    logging.info(f"Generating report and saving to {output_file}")
    try:
        # Generate timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save JSON report
        json_file = f"{os.path.splitext(output_file)[0]}_{timestamp}.json"
        with open(json_file, 'w') as f:
            json.dump(results, f, indent=2)
        logging.info(f"JSON report saved successfully to {json_file}")

        # Save CSV report
        csv_file = f"{os.path.splitext(output_file)[0]}_{timestamp}.csv"
        with open(csv_file, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=['name', 'ground_truth_count', 'discovered_count'])
            writer.writeheader()
            for row in results:
                writer.writerow(row)
        logging.info(f"CSV report saved successfully to {csv_file}")

    except Exception as e:
        logging.error(f"Error generating report: {str(e)}")
        raise

def main():
    logging.info("Starting the analysis process")
    
    parser = argparse.ArgumentParser(description="Analyze incident reports using Azure AI services.")
    parser.add_argument("--output", default="reports/terms_discovered.json", help="Output file for the report (JSON and CSV)")
    args = parser.parse_args()

    try:
        # Read and index documents
        logging.info("Starting document indexing process")
        read_and_index_documents(DATA_DIR)
        logging.info("Document indexing process completed")

        # Load incident types
        logging.info("Loading incident types")
        incident_types = load_incident_types()
        logging.info(f"Loaded {len(incident_types)} incident types")

        results = []
        for incident_type, ground_truth_count in incident_types.items():
            logging.info(f"Processing incident type: '{incident_type}'")
            
            # Count incidents
            discovered_count = count_incidents(incident_type)

            results.append({
                "name": incident_type,
                "ground_truth_count": ground_truth_count,
                "discovered_count": discovered_count
            })

            logging.info(f"Analysis complete for '{incident_type}'. Ground truth: {ground_truth_count}, Discovered: {discovered_count}")

        # Generate report
        logging.info("Generating final report")
        generate_report(results, args.output)

        logging.info("Analysis complete for all incident types.")
        print(f"Analysis complete. Reports saved with timestamp.")
        print(f"Check the 'reports' directory for the generated JSON and CSV files.")
    except Exception as e:
        logging.error(f"An error occurred during the main process: {str(e)}")
        print(f"An error occurred. Please check the logs for details.")

if __name__ == "__main__":
    main()