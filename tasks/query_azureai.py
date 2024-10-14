import os
import logging
from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from openai import AzureOpenAI
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

def main():
    logging.info("Starting the analysis process")
    
    parser = argparse.ArgumentParser(description="Analyze incident reports using Azure AI services.")
    parser.add_argument("incident_type", type=str, nargs='?', help="The type of incident to query for (use quotes for composite terms)")
    args = parser.parse_args()

    try:
        # Check if incident_type is provided
        if args.incident_type is None:
            print("Error: Please provide an incident type as a command-line argument.")
            print("Usage: python query_openai.py \"incident type\"")
            print("Example: python query_openai.py \"slip and fall\"")
            logging.error("No incident type provided")
            return

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