# Incident Report Generator and Analyzer

This project consists of scripts for generating synthetic incident reports and analyzing them using various Azure AI services and OpenAI.

## Prerequisites

- Python 3.8 or higher
- An OpenAI API key
- Azure AI Search service
- Azure Text Analytics service
- Azure OpenAI service

## Installation

1. Clone the repository:
   ```
   git clone <repository-url>
   cd <repository-name>
   ```

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On Windows:
     ```
     venv\Scripts\activate
     ```
   - On macOS and Linux:
     ```
     source venv/bin/activate
     ```

4. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Setting Environment Variables

Create a `.env` file in the root directory of the project with the following content:

```
OPENAI_API_KEY=your_openai_api_key
AZURE_SEARCH_ENDPOINT=your_azure_search_endpoint
AZURE_SEARCH_KEY=your_azure_search_key
AZURE_TEXT_ANALYTICS_ENDPOINT=your_azure_text_analytics_endpoint
AZURE_TEXT_ANALYTICS_KEY=your_azure_text_analytics_key
AZURE_OPENAI_ENDPOINT=your_azure_openai_endpoint
AZURE_OPENAI_KEY=your_azure_openai_key
AZURE_OPENAI_DEPLOYMENT=your_azure_openai_deployment
```

Replace the placeholders with your actual API keys and endpoints. Make sure to keep this file secure and never commit it to version control.

## Running the Scripts

### Generating Synthetic Data

To generate synthetic incident reports:

1. Ensure you're in the project root directory and your virtual environment is activated.

2. Run the generate_data.py script:
   ```
   python tasks/generate_data.py
   ```

This script will create synthetic incident reports based on the configuration in `config/incident_type_distribution.json` and save them in the `data/small` directory.

### Running the Analysis Scripts

There are three main scripts for analyzing the generated incident reports:

1. query_azureai.py
2. query_openai.py
3. query_azure_search.py

To run any of these scripts:

1. Ensure you're in the project root directory and your virtual environment is activated.

2. Run the desired script with the incident type as an argument:
   ```
   python tasks/<script_name>.py <incident_type>
   ```
   Replace `<script_name>` with the name of the script you want to run, and `<incident_type>` with the type of incident you want to query for. For composite terms, use quotes. For example:
   ```
   python tasks/query_azureai.py scaffolding
   python tasks/query_openai.py "near miss"
   python tasks/query_azure_search.py "chemical spill"
   ```

### Script Descriptions

1. query_azureai.py:
   - Creates a search index in Azure AI Search (if not exists)
   - Indexes the generated documents
   - Uses Azure AI Search to find relevant documents
   - Utilizes Azure OpenAI to analyze and count incidents

2. query_openai.py:
   - Uses Azure AI Search to find relevant documents
   - Leverages Azure OpenAI to analyze the content and count incidents
   - Provides a more detailed analysis using the power of large language models

3. query_azure_search.py:
   - Utilizes Azure AI Search to find relevant documents
   - Uses Azure Text Analytics to extract key phrases
   - Counts incidents based on key phrase extraction and content analysis

### Order of Execution

For the best results, follow this order:

1. Run the `generate_data.py` script first to create the synthetic incident reports.
2. Run the `create_index.py` script to set up the search index and index the documents.
3. After the data generation and indexing are complete, you can run any of the query scripts (`query_azureai.py`, `query_openai.py`, or `query_azure_search.py`) to analyze the generated reports.

### Customizing the Scripts

- To change the number of documents generated, modify the `num_documents` variable in `tasks/generate_data.py`.
- To change the incident type distribution, edit the `config/incident_type_distribution.json` file.
- To query for different incident types, simply pass the desired incident type as an argument when running the query scripts.

### Examples

1. Generate synthetic data:
   ```
   python tasks/generate_data.py
   ```

2. Create and populate the search index:
   ```
   python tasks/create_index.py
   ```

3. Query for scaffolding incidents using Azure AI:
   ```
   python tasks/query_azureai.py scaffolding
   ```

4. Query for chemical spill incidents using OpenAI:
   ```
   python tasks/query_openai.py "chemical spill"
   ```

5. Query for near miss incidents using Azure Search and Text Analytics:
   ```
   python tasks/query_azure_search.py "near miss"
   ```

Remember to use quotes for incident types that contain spaces.

### Viewing Results

- The `generate_data.py` script will log its progress and save the generated reports in the `data/small` directory.
- The query scripts will output the count of incidents for the specified query to the console and log detailed information about their processes.

Remember to check the console output and log files for any error messages or important information during the execution of these scripts.

### Running Additional Scripts

In addition to the main scripts, there are three more scripts that you can run for different purposes:

#### 1. Creating the Search Index

To create the Azure AI Search index:

1. Ensure you're in the project root directory and your virtual environment is activated.

2. Run the create_index.py script:
   ```
   python tasks/create_index.py
   ```

This script will:
- Delete the existing index if it exists
- Create a new search index in Azure AI Search
- Read and index the documents from the `data/small` directory

Run this script before running the query scripts to ensure your index is up-to-date.

#### 2. Querying All Incident Types

To analyze all incident types defined in the configuration:

1. Ensure you're in the project root directory and your virtual environment is activated.

2. Run the query_all.py script:
   ```
   python tasks/query_all.py
   ```

This script will:
- Read and index documents if they haven't been indexed yet
- Load incident types from the configuration file
- Count occurrences of each incident type using Azure AI services
- Generate JSON and CSV reports with the results

The reports will be saved in the `reports` directory with timestamps in their filenames.

#### 3. Discovering Incident Types

To discover potential incident types from the data:

1. Ensure you're in the project root directory and your virtual environment is activated.

2. Run the discover_azureai.py script:
   ```
   python tasks/discover_azureai.py
   ```

This script will:
- Create a search index if it doesn't exist
- Read and index documents if they haven't been indexed yet
- Use Azure AI Text Analytics to extract key phrases from the documents
- Identify the top 20 most frequent key phrases as potential incident types
- Write the results to a JSON file and print them to the console

The discovered incident types will be saved in `reports/terms_discovered.json`.

### Examples

1. Create the search index and index documents:
   ```
   python tasks/create_index.py
   ```

2. Query all incident types defined in the configuration:
   ```
   python tasks/query_all.py
   ```

3. Discover potential new incident types:
   ```
   python tasks/discover_azureai.py
   ```

### Order of Execution

For the best results, follow this order:

1. Run `generate_data.py` to create synthetic incident reports.
2. Run `create_index.py` to set up the search index and index the documents.
3. Run `query_all.py` to analyze all predefined incident types.
4. Run `discover_azureai.py` to find potential new incident types.
5. Use `query_azureai.py` for specific incident type queries.

Remember to check the console output and log files for any error messages or important information during the execution of these scripts.

Notes:
- Consider Azure AI search strictiness parameter.
- When generating data, add ID to the document, so the query returns the ID back.
- Generate Parquet files for synthetic data.
- Try different search strategies for Azure Search.
