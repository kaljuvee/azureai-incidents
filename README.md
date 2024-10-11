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
