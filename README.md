# Incident Report Generator and Analyzer

This project consists of two main scripts: one for generating synthetic incident reports and another for analyzing them using Azure AI services.

## Prerequisites

- Python 3.8 or higher
- An OpenAI API key
- Azure AI Search service
- Azure Text Analytics service

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

## Running the Scripts

### Generating Synthetic Data

To generate synthetic incident reports:

1. Ensure you're in the project root directory and your virtual environment is activated.

2. Run the generate_data.py script:
   ```
   python tasks/generate_data.py
   ```

This script will create synthetic incident reports based on the configuration in `config/incident_type_distribution.json` and save them in the `data/small` directory.

### Running the Azure AI Query Script

To analyze the generated incident reports using Azure AI services:

1. Ensure you're in the project root directory and your virtual environment is activated.

2. Run the query_azureai.py script with the incident type as an argument:
   ```
   python tasks/query_azureai.py <incident_type>
   ```
   Replace `<incident_type>` with the type of incident you want to query for. For composite terms, use quotes. For example:
   ```
   python tasks/query_azureai.py scaffolding
   python tasks/query_azureai.py "near miss"
   ```

This script will:
- Create a search index in Azure AI Search
- Index the generated documents
- Perform a query to count incidents of the specified type

### Order of Execution

For the best results, follow this order:

1. Run the `generate_data.py` script first to create the synthetic incident reports.
2. After the data generation is complete, run the `query_azureai.py` script to analyze the generated reports.

### Customizing the Scripts

- To change the number of documents generated, modify the `num_documents` variable in `tasks/generate_data.py`.
- To change the incident type distribution, edit the `config/incident_type_distribution.json` file.
- To query for different incident types, simply pass the desired incident type as an argument when running `query_azureai.py`.

### Examples

1. Generate synthetic data:
   ```
   python tasks/generate_data.py
   ```

2. Query for scaffolding incidents:
   ```
   python tasks/query_azureai.py scaffolding
   ```

3. Query for chemical spill incidents:
   ```
   python tasks/query_azureai.py "chemical spill"
   ```

4. Query for near miss incidents:
   ```
   python tasks/query_azureai.py "near miss"
   ```

Remember to use quotes for incident types that contain spaces.

### Viewing Results

- The `generate_data.py` script will log its progress and save the generated reports in the `data/small` directory.
- The `query_azureai.py` script will output the count of incidents for the specified query to the console and log detailed information about its process.

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
