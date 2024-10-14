import os
import json
import csv
import logging
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI
from dotenv import load_dotenv
import argparse
from datetime import datetime

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

# Azure OpenAI configuration
openai_endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
openai_key = os.getenv("AZURE_OPENAI_KEY")
openai_deployment = os.getenv("AZURE_OPENAI_DEPLOYMENT")
logging.info(f"Azure OpenAI Endpoint: {openai_endpoint}")
logging.info(f"Azure OpenAI Key: {'*' * len(openai_key) if openai_key else 'Not found'}")
logging.info(f"Azure OpenAI Deployment: {openai_deployment}")

# Initialize clients
try:
    search_credential = AzureKeyCredential(search_key)
    search_client = SearchClient(endpoint=search_endpoint, index_name=INDEX_NAME, credential=search_credential)
    openai_client = AzureOpenAI(
        api_key=openai_key,
        api_version="2023-05-15",
        azure_endpoint=openai_endpoint
    )
    logging.info("Azure clients initialized successfully")
except Exception as e:
    logging.error(f"Error initializing Azure clients: {str(e)}")
    raise

def count_incidents(query_incident):
    logging.info(f"Counting incidents for query: '{query_incident}'")
    try:
        # Search for relevant documents, increase top to 50
        results = list(search_client.search(query_incident, top=100))
        logging.info(f"Found {len(results)} relevant documents")
        
        if not results:
            logging.info(f"No documents found for query: '{query_incident}'")
            return 0
        
        # Combine relevant documents
        combined_content = "\n\n".join([doc['content'] for doc in results])
        logging.info(f"Combined content length: {len(combined_content)} characters")
        
        # Use Azure OpenAI to analyze the content
        system_message = "You are an AI assistant tasked with analyzing incident reports. Your job is to count the number of distinct incidents related to a specific query."
        user_message = f"Based on the following incident reports, how many distinct incidents related to '{query_incident}' can you identify? Please provide only a number as your response.\n\nIncident reports:\n{combined_content}"
        
        response = openai_client.chat.completions.create(
            model=openai_deployment,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": user_message}
            ],
            temperature=0,
            max_tokens=10
        )
        
        count = int(response.choices[0].message.content.strip())
        
        logging.info(f"Incident count for '{query_incident}': {count}")
        return count
    except Exception as e:
        logging.error(f"Error in count_incidents: {str(e)}")
        return 0  # Return 0 instead of raising an exception

def load_incident_types():
    try:
        with open('config/incident_type_distribution.json', 'r') as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"Error loading incident types: {str(e)}")
        raise

def generate_report(results, output_dir):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Ensure the output directory exists
    os.makedirs(output_dir, exist_ok=True)
    
    # Generate JSON report
    json_filename = os.path.join(output_dir, f"incident_analysis_{timestamp}.json")
    with open(json_filename, 'w') as f:
        json.dump(results, f, indent=2)
    
    # Generate CSV report with the new filename format
    csv_filename = os.path.join(output_dir, f"openai_report_{timestamp}.csv")
    with open(csv_filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=["name", "ground_truth_count", "discovered_count"])
        writer.writeheader()
        writer.writerows(results)
    
    logging.info(f"Reports generated: {json_filename} and {csv_filename}")
    return csv_filename  # Return the CSV filename for potential use in main()

def main():
    logging.info("Starting the analysis process")
    
    parser = argparse.ArgumentParser(description="Analyze incident reports using Azure AI services.")
    parser.add_argument("--output", type=str, default="reports", help="Output directory for reports")
    args = parser.parse_args()

    try:
        # Load incident types
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

        # Sort results by ground_truth_count in descending order
        results.sort(key=lambda x: x['ground_truth_count'], reverse=True)

        # Generate report
        logging.info("Generating final report")
        csv_filename = generate_report(results, args.output)

        logging.info("Analysis complete for all incident types.")
        print(f"Analysis complete. Reports saved with timestamp.")
        print(f"Check the '{args.output}' directory for the generated JSON and CSV files.")
        print(f"CSV report: {csv_filename}")
    except Exception as e:
        logging.error(f"An error occurred during the main process: {str(e)}")
        print(f"An error occurred. Please check the logs for details.")

if __name__ == "__main__":
    main()