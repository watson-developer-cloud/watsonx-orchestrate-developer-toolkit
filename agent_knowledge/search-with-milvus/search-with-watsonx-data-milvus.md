# How to set up Agent Knowledge in watsonx Orchestrate CP4D with watsonx.data Milvus CP4D and watsonx.ai CP4D  
This document explains how to set up watsonx.data Milvus CP4D as a content repository of Agent Knowledge in watsonx Orchestrate CP4D by using the embedding model in watsonx.ai CP4D.

## Before you begin
1. Provision a watsonx.data instance
    * watsonx.data on Cloud Pak for Data (on-prem): follow [this doc](https://www.ibm.com/docs/en/cloud-paks/cp-data/5.2.x?topic=installing-administering-cloud-pak-data) to install and set up watsonx.data on Cloud Pak for Data 
2. Add an Milvus service in the watsonx.data console
    * watsonx.data on Cloud Pak for Data (on-prem): [Adding a Milvus service](https://www.ibm.com/docs/en/watsonxdata/standard/2.2.x?topic=milvus-adding-service)
3. This guide focuses on how to setup watsonx.data Milvus CP4D as the content repository. For how to setup watsonx.ai CP4D and watsonx Orchestrate CP4D, please refer to the relevant documents.

## Table of contents
* [Step 1: Collect Milvus connection info](#step-1-collect-milvus-connection-info)
  * [Get the credentials](#get-the-credentials)
  * [Get other connection details](#get-other-connection-details)
* [Step 2: Ingest data into Milvus](#step-2-ingest-data-into-milvus)
  * [Option 1: Ingest data through watsonx.ai](#option-1-ingest-data-through-watsonxai)
  * [Option 2: Ingest data using custom code](#option-2-ingest-data-using-custom-code)
* [Step 3: Connect to Agent Knowledge in watsonx Orchestrate](#step-3-connect-to-agent-knowledge-in-watsonx-orchestrate)

## Step 1: Collect Milvus connection info
### Get the credentials
#### Username
The default username is `cpadmin` for the Milvus service on watsonx.data. You can also find the username in the Milvus "Access control" panel in the `Infrastructure Manager` of the watsonx.data instance.

#### Password
Use the password you created for `cpadmin` or a different user that has the access to the Milvus service as identified above.

### Get other connection details
Here are the steps to collect other Milvus connection details from the watsonx.data console:

1. Go to the `Infrastructure manager` page.
2. Click the Milvus service to open the `Details` page.
3. Click on `View connect details` to view more connection details.
4. Collect the GRPC `host`, `port`, and the SSL certificate from the service details.

## Step 2: Ingest data into Milvus
You can ingest data into Milvus vector database either through watsonx.ai or by using custom code.
### Option 1: Ingest data through watsonx.ai
#### Create a Milvus connection
On the watsonx.ai Project Assets page, click on `New asset` --> choose `Connect a data source` --> choose `Milvus` --> click `Next` --> fill in the connection details and credentials as below --> `Test connection` --> click `Create`.

<img src="./assets/create-milvus-connection.png" width="1080" height="574" />

#### Create a vector index and upload documents
On the watsonx.ai Project Assets page, using the Milvus connection created in the previous step, you can create a vector index and upload documents into it. Here are the steps:
1. On the watsonx.ai Project Assets page, click on `New asset` --> choose `Ground gen AI with vectorized documents`.
2. On the left-side panel, select `watsonx.data Milvus` as the vector store --> fill in name and description --> select the Milvus connection created earlier. 
3. Select the Milvus connection created earlier -> Select `Database` and `Embeddings model` from the dropdowns --> click `Next`. For example,  
<img src="./assets/create-milvus-index-watsonx-ai.png" width="1080" height="574" />

4. Click `New collection` to create a new collection.
5. Provide a unique collection name and choose files to add to the Milvus collection --> click `Create`. Please take a note of the values of the `Document name field` and the `Text field` under `Advanced settings`, you will need to use these values later to setup Agent Knowledge. 
<img src="./assets/create-milvus-collection-and-ingest-watsonx-ai.png" width="1080" height="574" />

6. Once the document uploading process is done, you can start testing it in the prompt lab.

**NOTE: `document_name` and `text` are the two main fields created in the Milvus collection schema by default. When searching this Milvus collection using custom code, you need to specify these two fields as output_fields. When setting up the built-in Milvus search integration, you need to configure the Title and Body fields with these two fields.**

### Option 2: Ingest data using custom code
Here is a sample code to ingest documents into Milvus: [../examples/index-with-milvus.py](../examples/index-with-milvus.py). To run it, 
1. Install dependencies:
   ```bash
   python3 -m pip install pymilvus langchain langchain-milvus langchain-ibm ibm-watsonx-ai PyPDF2
   ```
2. Create environment variables for Milvus credentials
  ```bash
  export MILVUS_HOST="Your Milvus GRPC host"
  export MILVUS_PORT="Your Milvus GRPC port"
  export MILVUS_USER="cpadmin" // The default username for watsonx.data Milvus on-premise
  export MILVUS_PASSWORD="Your watsonx.data Milvus on-premise password"
  export MILVUS_PEM_PATH="the file path to the watsonx.data Milvus on-premise TLS certificate"
  export MILVUS_COLLECTION_NAME="Your Milvus collection name" // It can be anything

  export WATSONX_AI_URL="Your watsonx.ai on-premise URL"
  export WATSONX_AI_USERNAME="Your watsonx.ai on-premise username" // watsonx.ai embeddings model is used to create vectors
  export WATSONX_AI_PASSWORD="Your watsonx.ai on-premise password" // watsonx.ai embeddings model is used to create vectors
  export WATSONX_AI_PROJECT_ID="Your watsonx.ai project ID" // watsonx.ai project ID is required to access the embeddings models
  ```
3. Update the `SOURCE_FILES`, `SOURCE_URLS`, and `SOURCE_TITLES` variables at the begining of the script to your file names, urls, and titles respectively.
4. Run the script
   ```bash
   python3 index-with-milvus.py
   ```

## Step 3: Connect to Agent Knowledge in watsonx Orchestrate

**NOTE: The embedding model you use for search using either option in [Step 3](#step-3-connect-to-agent-knowledge-in-watsonx-orchestrate) has to align with the embedding model used for data ingestion in [Step 2](#step-2-ingest-data-into-milvus).**

This option allows you to integrate with your watsonx.data Milvus on-premise service through the Agent Knowledge feature of watsonx Orchestrate.

Please go to the [watsonx Orchestrate product docs](https://www.ibm.com/docs/en/watsonx/watson-orchestrate/base?topic=agents-connecting-milvus-content-repository) to find more details about how to set up Milvus as a content repository of Agent Knowledge.

