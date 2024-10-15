import os
import logging
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI
from dotenv import load_dotenv
import json
import datetime
import time
from tenacity import retry, stop_after_attempt, wait_exponential
import ast
import csv

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

try:
    search_credential = AzureKeyCredential(search_key)
    logging.info("Azure Search credential created successfully")
except ValueError as e:
    logging.error(f"Error creating Azure Search credential: {str(e)}")
    raise

try:
    # Initialize clients
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

@retry(stop=stop_after_attempt(5), wait=wait_exponential(multiplier=1, min=4, max=10))
def make_openai_request(openai_client, system_message, user_message):
    return openai_client.chat.completions.create(
        model=openai_deployment,
        messages=[
            {"role": "system", "content": system_message},
            {"role": "user", "content": user_message}
        ],
        temperature=0.5,
        max_tokens=200
    )

def discover_incidents(top_n=50, batch_size=10):
    logging.info(f"Discovering top {top_n} incident types")
    try:
        results = list(search_client.search("*", top=50))
        logging.info(f"Found {len(results)} documents")
        
        if not results:
            logging.info("No documents found")
            return []
        
        all_incidents = []
        
        # Process documents in batches
        for i in range(0, len(results), batch_size):
            batch = results[i:i+batch_size]
            batch_content = "\n\n".join([doc['content'] for doc in batch])
            
            system_message = "You are an AI assistant tasked with analyzing incident reports and identifying distinct types of incidents or topics."
            user_message = f"Based on the following incident reports, identify and list distinct types of incidents or topics. Provide your response as a Python list of strings, with each string representing a distinct incident type or topic.\n\nIncident reports:\n{batch_content}"
            
            try:
                response = make_openai_request(openai_client, system_message, user_message)
                
                # Extract the Python list from the response
                response_content = response.choices[0].message.content.strip()
                # Remove markdown code block formatting if present
                if response_content.startswith("```python"):
                    response_content = response_content.split("\n", 1)[1].rsplit("\n", 1)[0]
                elif response_content.startswith("```"):
                    response_content = response_content.split("\n", 1)[1].rsplit("\n", 1)[0]
                
                # Clean up the response content
                response_content = response_content.strip()
                response_content = response_content.replace('\n', '').replace('    ', '')
                
                # Safely evaluate the string as a Python expression
                batch_incidents = ast.literal_eval(response_content)
                
                if not isinstance(batch_incidents, list):
                    raise ValueError("Response is not a list")
                all_incidents.extend(batch_incidents)
                logging.info(f"Processed batch {i//batch_size + 1}, found {len(batch_incidents)} incidents")
            except Exception as e:
                logging.error(f"Error processing batch: {str(e)}")
                logging.error(f"Raw response: {response.choices[0].message.content if 'response' in locals() else 'No response'}")
                continue
            
            # Add a delay between batches to avoid rate limiting
            time.sleep(2)
        
        logging.info(f"Discovered a total of {len(all_incidents)} incident types")
        
        # Count occurrences of each incident type
        incident_counts = {}
        for incident in all_incidents:
            incident_counts[incident] = incident_counts.get(incident, 0) + 1
        
        # Get top N incident types
        top_incidents = sorted(incident_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]
        
        logging.info(f"Top {top_n} incident types discovered")
        return top_incidents
    except Exception as e:
        logging.error(f"Error in discover_incidents: {str(e)}")
        return []

def write_top_incidents_to_files(top_incidents):
    logging.info("Writing top incidents to JSON and CSV files")
    try:
        os.makedirs('reports', exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Write JSON file
        json_filename = f'reports/incidents_discovered_{timestamp}.json'
        with open(json_filename, 'w') as f:
            json.dump(top_incidents, f, indent=2)
        logging.info(f"Successfully wrote top incidents to {json_filename}")
        
        # Write CSV file
        csv_filename = f'reports/incidents_discovered_{timestamp}.csv'
        with open(csv_filename, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow(['incident_name', 'count'])  # Write header
            for incident, count in top_incidents:
                writer.writerow([incident, count])
        logging.info(f"Successfully wrote top incidents to {csv_filename}")
    except Exception as e:
        logging.error(f"Error writing top incidents to files: {str(e)}")

def main():
    logging.info("Starting the discovery process")
    
    try:
        # Discover top 50 incident types
        top_incidents = discover_incidents(top_n=50)

        if not top_incidents:
            logging.warning("No incidents were discovered.")
            print("No incidents were discovered. Please check the logs for details.")
            return

        # Write top incident types to JSON and CSV files
        write_top_incidents_to_files(top_incidents)

        # Print top incident types
        logging.info("Discovery complete. Top incident types:")
        print("Top incident types:")
        for incident, count in top_incidents:
            logging.info(f"- {incident}: {count}")
            print(f"- {incident}: {count}")
    except Exception as e:
        logging.error(f"An error occurred during the main process: {str(e)}")
        print("An error occurred. Please check the logs for details.")

if __name__ == "__main__":
    main()
